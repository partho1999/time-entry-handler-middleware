from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .services import SessionManager, WsSession, MessageHandler, ProtocolResp
import time

class DeviceWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.channel_name
        self.session_manager = SessionManager.get_instance()
        self.message_handler = MessageHandler(self.session_manager)
        await self.accept()
        ws_session = WsSession(sn=None, session_id=self.session_id, session=self)
        self.session_manager.new_session(ws_session)
        await self.send(text_data=json.dumps({"message": "WebSocket connected", "session_id": self.session_id}))

    async def disconnect(self, close_code):
        self.session_manager.close_session(self.session_id)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data is not None:
                # Try to parse as protocol string
                proto = self.message_handler.parse_protocol(text_data)
                ws_session = self.session_manager.ws_session_map.get(self.session_id)
                if isinstance(proto, ProtocolResp):
                    self.message_handler.handle_response(proto)
                elif ws_session is not None:
                    self.message_handler.handle_message_resp(ws_session, text_data)
                else:
                    await self.send(text_data=json.dumps({"error": "Session not found"}))
                await self.send(text_data=json.dumps({"received": text_data}))
            else:
                await self.send(text_data=json.dumps({"error": "No text data received"}))
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)})) 