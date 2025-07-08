# Service migrated from Java ISxDeviceService and SxDeviceServiceImpl
from typing import List, Optional
import time
import threading
import json
import asyncio

class SxDeviceService:
    def __init__(self):
        self.message_handler = MessageHandler()

    async def send_request(self, sn: str, req):
        return await self.message_handler.send_request(sn, req)

    def is_device_online(self, sn: str) -> bool:
        """Check if device is online (to be implemented)"""
        return False

    def get_device_session(self, sn: str):
        """Get device session (to be implemented)"""
        return None

    def get_online_device_session_list(self) -> List:
        """Get list of online device sessions (to be implemented)"""
        return []

    def check_client_login(self, serial_no: str, random: str, password: str) -> bool:
        """Check client login (default: always True)"""
        return True 

class ProtocolReq:
    def __init__(self, request_id, method, path, data):
        self.request_id = request_id
        self.method = method
        self.path = path
        self.data = data

    def to_protocol_string(self):
        # Compose a protocol string similar to Java SXProtocolResp
        lines = [
            f"{self.request_id}&HTTP/1.1 {200} OK\r\n",
            "\r\n",
            json.dumps(self.data)
        ]
        return ''.join(lines)

class ProtocolResp:
    def __init__(self, request_id, status=200, data=None):
        self.request_id = request_id
        self.status = status
        self.data = data or {}

    def to_protocol_string(self):
        # Compose a protocol string similar to Java SXProtocolResp
        lines = [
            f"{self.request_id}&HTTP/1.1 {self.status} OK\r\n",
            "\r\n",
            json.dumps(self.data)
        ]
        return ''.join(lines)

class WsSession:
    def __init__(self, sn, session_id, authed=False, last_ping_pong_time=None, random=None, session=None):
        self.sn = sn
        self.session_id = session_id
        self.authed = authed
        self.last_ping_pong_time = last_ping_pong_time or int(time.time() * 1000)
        self.random = random
        self.session = session  # Not persisted, just for runtime

class SessionManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.ws_session_map = {}  # session_id -> WsSession
        self.sn_sid_map = {}      # sn -> session_id

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def new_session(self, session: WsSession):
        self.ws_session_map[session.session_id] = session
        if session.sn:
            self.sn_sid_map[session.sn] = session.session_id

    def get_session_by_sn(self, sn: str) -> Optional[WsSession]:
        session_id = self.sn_sid_map.get(sn)
        if session_id:
            return self.ws_session_map.get(session_id)
        return None

    def get_online_sessions(self) -> List[WsSession]:
        return [s for s in self.ws_session_map.values() if s.authed]

    def close_session(self, session_id: str):
        session = self.ws_session_map.pop(session_id, None)
        if session and session.sn in self.sn_sid_map:
            del self.sn_sid_map[session.sn]

    def session_authed(self, session_id: str):
        session = self.ws_session_map.get(session_id)
        if session:
            session.authed = True

class MessageHandler:
    def __init__(self, session_manager=None):
        self.session_manager = session_manager or SessionManager.get_instance()
        self.send_result_map = {}  # request_id -> asyncio.Event/result
        self.protocol_handlers = {}
        self.register_protocol_handler('/api/auth/random', self.handle_request_of_random)
        self.register_protocol_handler('/api/auth/login', self.handle_request_of_login)
        # Register more handlers as needed

    def register_protocol_handler(self, path, handler):
        self.protocol_handlers[path] = handler

    def parse_protocol(self, payload: str):
        # Parse protocol string to ProtocolReq or ProtocolResp
        try:
            lines = payload.split('\r\n')
            first_line = lines[0]
            if '&' not in first_line:
                return None
            parts = first_line.split()
            id_and_method = parts[0].split('&')
            if len(id_and_method) < 2:
                return None
            request_id = id_and_method[0]
            if id_and_method[1].startswith('HTTP'):
                # Response
                status = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 200
                data = json.loads(lines[-1]) if lines[-1].startswith('{') else {}
                return ProtocolResp(request_id, status, data)
            else:
                # Request
                method = id_and_method[1]
                path = parts[1] if len(parts) > 1 else ''
                data = json.loads(lines[-1]) if lines[-1].startswith('{') else {}
                return ProtocolReq(request_id, method, path, data)
        except Exception:
            return None

    def handle_message_resp(self, ws_session: WsSession, payload):
        # Accepts either a protocol string or dict (for testing)
        if isinstance(payload, str):
            proto = self.parse_protocol(payload)
        else:
            # Assume dict for test/dev
            proto = ProtocolReq(payload.get('request_id'), payload.get('method'), payload.get('path'), payload.get('data'))
        if isinstance(proto, ProtocolReq):
            handler = self.protocol_handlers.get(proto.path, self.handle_unknown_command)
            handler(ws_session, proto)
        elif isinstance(proto, ProtocolResp):
            self.handle_response(proto)

    async def send_request(self, sn, req, timeout=30):
        ws_session = self.session_manager.get_session_by_sn(sn)
        if ws_session is None or not ws_session.authed:
            return ProtocolResp(req.request_id, 408, {"error": "Device offline or not authed"})
        event = asyncio.Event()
        self.send_result_map[req.request_id] = {"event": event, "result": None}
        # Send the message
        if ws_session.session is not None:
            await ws_session.session.send(text_data=req.to_protocol_string())
        else:
            return ProtocolResp(req.request_id, 408, {"error": "No session object"})
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return ProtocolResp(req.request_id, 408, {"error": "Timeout"})
        finally:
            result = self.send_result_map.pop(req.request_id, {}).get("result")
        return result or ProtocolResp(req.request_id, 408, {"error": "No response"})

    def handle_response(self, resp: ProtocolResp):
        # Called when a response is received
        entry = self.send_result_map.get(resp.request_id)
        if entry:
            entry["result"] = resp
            entry["event"].set()

    def handle_request_of_random(self, ws_session: WsSession, req: ProtocolReq):
        # Simulate random generation and response
        import random
        m_random = str(random.randint(100000, 999999))
        ws_session.random = m_random
        ws_session.sn = req.data.get('serial_no')
        self.session_manager.sn_sid_map[ws_session.sn] = ws_session.session_id
        resp = ProtocolResp(req.request_id, 200, {"random": m_random})
        # Send response
        if ws_session.session:
            # Async send for Channels
            import asyncio
            asyncio.create_task(ws_session.session.send(text_data=resp.to_protocol_string()))

    def handle_request_of_login(self, ws_session: WsSession, req: ProtocolReq):
        # Simulate login check
        serial_no = req.data.get('serial_no')
        random_val = req.data.get('random')
        password = req.data.get('password')
        if random_val != ws_session.random:
            # Random mismatch, close session
            if ws_session.session:
                import asyncio
                asyncio.create_task(ws_session.session.close())
            return
        # For now, always succeed
        ws_session.authed = True
        resp = ProtocolResp(req.request_id, 200, {"status": 200, "session_id": ws_session.session_id})
        if ws_session.session:
            import asyncio
            asyncio.create_task(ws_session.session.send(text_data=resp.to_protocol_string()))

    def handle_unknown_command(self, ws_session: WsSession, req: ProtocolReq):
        # Default handler for unknown commands
        resp = ProtocolResp(req.request_id, 404, {"error": "Unknown command"})
        if ws_session.session:
            import asyncio
            asyncio.create_task(ws_session.session.send(text_data=resp.to_protocol_string()))

    def send(self, ws_session: WsSession, message):
        # Placeholder for sending logic
        pass 