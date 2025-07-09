from channels.generic.websocket import AsyncWebsocketConsumer
import json
import uuid
from .session import session_manager, DeviceSession
from .message import message_handler
from .protocol import SXProtocolParser, SXProtocolReq, SXProtocolResp

class DeviceWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Generate a unique session ID for this connection
        self.session_id = str(uuid.uuid4())
        session_bean = DeviceSession(session_id=self.session_id, session=self)
        session_manager.new_session(session_bean)
        await self.accept()

    async def disconnect(self, close_code):
        session_manager.close_session(self.session_id)

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming WebSocket messages
        session_bean = session_manager.get_session(self.session_id)
        if not session_bean:
            await self.close()
            return
        if text_data:
            # Use the synchronous message handler for now
            message_handler.handle_message_resp(session_bean, text_data)

    async def send_protocol(self, protocol):
        # Send a protocol message to the client
        await self.send(text_data=protocol.to_protocol_string())

    def is_open(self):
        # Used by MessageSender
        return self.channel_layer is not None 