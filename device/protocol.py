import json
import time
from .constants import *

class SXProtocol:
    def __init__(self, request_id=None):
        self.request_id = request_id
        self.data = None
        self.array_data = None
        self.data_str = None

    def to_protocol_string(self):
        raise NotImplementedError

    def get_data_str(self):
        if self.data_str is None:
            if self.data is not None:
                self.data_str = json.dumps(self.data)
            elif self.array_data is not None:
                self.data_str = json.dumps(self.array_data)
            else:
                self.data_str = ''
        return self.data_str

    def get_data(self):
        if self.data is None and self.data_str:
            self.data = json.loads(self.data_str)
        return self.data

class SXProtocolReq(SXProtocol):
    _request_id_counter = int(time.time() * 1000)

    def __init__(self, request_id=None):
        super().__init__(request_id)
        self.method = None
        self.path = None

    def to_protocol_string(self):
        data_str = self.get_data_str()
        protocol = (
            f"{self.request_id}{CONSTANT_AND}{self.method}{CONSTANT_SP}{self.path}{CONSTANT_SP}{REQUEST_HEADER_HTTP_VER}{REQUEST_NEWLINE}"
            f"{REQUEST_HEADER_HOST}{REQUEST_NEWLINE}"
            f"{REQUEST_HEADER_LENGTH}{len(data_str.encode('utf-8'))}{REQUEST_NEWLINE}"
            f"{REQUEST_HEADER_CONTENT_TYPE}{REQUEST_NEWLINE}"
            f"{REQUEST_NEWLINE}"
            f"{data_str}"
        )
        return protocol

    @classmethod
    def new_request(cls, request_id=None):
        if request_id is None:
            cls._request_id_counter += 1
            request_id = str(cls._request_id_counter)
        return SXProtocolReq(request_id)

class SXProtocolResp(SXProtocol):
    def __init__(self, request_id, status=200, reason='OK'):
        super().__init__(request_id)
        self.status = status
        self.reason = reason

    def to_protocol_string(self):
        data_str = self.get_data_str()
        protocol = (
            f"{self.request_id}{CONSTANT_AND}{REQUEST_HEADER_HTTP_VER}{CONSTANT_SP}{self.status}{CONSTANT_SP}{self.reason}{REQUEST_NEWLINE}"
            f"{REQUEST_NEWLINE}"
            f"{data_str}"
        )
        return protocol

class SXProtocolParser:
    @staticmethod
    def parse(content):
        if not content:
            return None
        try:
            lines = content.split(REQUEST_NEWLINE)
            first_line = lines[0].replace('& ', '&') if '& ' in lines[0] else lines[0]
            fls = first_line.split()
            ffc = fls[0].split('&')
            if ffc[1].startswith('HTTP'):
                # Response
                status = int(fls[1])
                reason = fls[2] if len(fls) > 2 else 'OK'
                resp = SXProtocolResp(ffc[0], status, reason)
                last_line = lines[-1].strip()
                if last_line.startswith('{') or last_line.startswith('['):
                    try:
                        resp.data = json.loads(last_line)
                    except Exception:
                        resp.data_str = last_line
                else:
                    resp.data_str = last_line
                return resp
            else:
                # Request
                req = SXProtocolReq(ffc[0])
                req.method = ffc[1]
                req.path = fls[1]
                last_line = lines[-1].strip()
                if last_line.startswith('{') or last_line.startswith('['):
                    try:
                        req.data = json.loads(last_line)
                    except Exception:
                        req.data_str = last_line
                else:
                    req.data_str = last_line
                return req
        except Exception as e:
            print(f"Failed to parse SXProtocol: {e}")
        return None 