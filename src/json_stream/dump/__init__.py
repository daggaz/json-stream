import json

from json_stream import to_standard_types
from json_stream.base import StreamingJSONBase

_original_default = json.JSONEncoder().default


class JSONStreamEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, StreamingJSONBase):
            return to_standard_types(obj)
        return _original_default(obj)

    def __enter__(self):
        json.JSONEncoder.default = self.default

    def __exit__(self, exc_type, exc_val, exc_tb):
        json.JSONEncoder.default = _original_default


default = JSONStreamEncoder().default
