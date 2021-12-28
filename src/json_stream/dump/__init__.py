import json

from json_stream.base import StreamingJSONObject, StreamingJSONList

_original_default = json.JSONEncoder().default


class JSONStreamEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, StreamingJSONObject):
            return dict(obj)
        if isinstance(obj, StreamingJSONList):
            return list(obj)
        return _original_default(obj)

    def __enter__(self):
        json.JSONEncoder.default = self.default

    def __exit__(self, exc_type, exc_val, exc_tb):
        json.JSONEncoder.default = _original_default


default = JSONStreamEncoder().default
