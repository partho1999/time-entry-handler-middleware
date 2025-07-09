from .protocol import SXProtocol, SXProtocolReq, SXProtocolResp
from .session import session_manager, DeviceSession
from .utils import get_rand_num6
import json

class MessageSender:
    def send(self, session_bean: DeviceSession, protocol: SXProtocol):
        # Placeholder for WebSocket send logic
        # In a real implementation, this would send over a WebSocket
        if session_bean.session and getattr(session_bean.session, 'is_open', lambda: False)():
            # session_bean.session.send(protocol.to_protocol_string())
            print(f"Sending to session {session_bean.session_id}: {protocol.to_protocol_string()}")
        else:
            print(f"Session {session_bean.session_id} is not open.")

message_sender = MessageSender()

class MessageHandler:
    def __init__(self):
        self.response_handler = None

    def set_response_handler(self, handler):
        self.response_handler = handler

    def handle_message_resp(self, session, message):
        # 'session' is a placeholder for WebSocketSession
        payload = message if isinstance(message, str) else getattr(message, 'payload', '')
        sx_protocol = SXProtocolParser.parse(payload)
        if sx_protocol is None:
            self.close_invalid_session(session)
            return
        if isinstance(sx_protocol, SXProtocolReq):
            self.handle_request(session, sx_protocol)
        else:
            self.handle_response(session, sx_protocol)

    def close_invalid_session(self, session):
        print(f"Invalid session {getattr(session, 'session_id', None)} closed.")
        # session_manager.close_session(getattr(session, 'session_id', None))

    def handle_request(self, session, req: SXProtocolReq):
        if req.path == '/api/auth/random':
            self.handle_request_of_random(session, req)
        elif req.path == '/api/auth/login':
            self.handle_request_of_login(session, req)

    def handle_request_of_login(self, session, req: SXProtocolReq):
        session_id = getattr(session, 'session_id', None)
        ws_session_bean = session_manager.get_session(session_id)
        if ws_session_bean is None:
            return
        if ws_session_bean.authed:
            return
        req_json = req.data or {}
        serial_no = req_json.get('serial_no')
        random_val = req_json.get('random')
        password = req_json.get('password')
        if random_val != ws_session_bean.random:
            session_manager.close_session(session_id)
            return
        # Password check logic placeholder (always True)
        if not True:
            return
        ws_session_bean.authed = True
        resp = SXProtocolResp(req.request_id)
        data_obj = {'status': 200, 'session_id': session_id}
        resp.data = data_obj
        message_sender.send(ws_session_bean, resp)

    def handle_request_of_random(self, session, req: SXProtocolReq):
        param_json = req.data or {}
        serial_no = param_json.get('serial_no')
        ws_session_bean = session_manager.get_session(getattr(session, 'session_id', None))
        if ws_session_bean is None:
            return
        ws_session_bean.sn = serial_no
        session_manager.update_session_sn(ws_session_bean.session_id, serial_no)
        m_random = str(get_rand_num6())
        ws_session_bean.random = m_random
        resp = SXProtocolResp(req.request_id)
        resp.data = {'random': m_random}
        message_sender.send(ws_session_bean, resp)

    def handle_response(self, session, resp: SXProtocolResp):
        if self.response_handler:
            self.response_handler(session, resp)

# Singleton instance
message_handler = MessageHandler()

# Import protocol parser at the end to avoid circular import
from .protocol import SXProtocolParser 