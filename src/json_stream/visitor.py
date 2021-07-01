from json_stream.base import TransientStreamingJSONBase, StreamingJSONObject, StreamingJSONList
from json_stream.tokenizer import tokenize


def _visit(obj, visitor, path):
    k = None
    if isinstance(obj, StreamingJSONObject):
        for k, v in obj.items():
            _visit(v, visitor, path + (k,))
        if k is None:
            visitor({}, path)
    elif isinstance(obj, StreamingJSONList):
        for k, v in enumerate(obj):
            _visit(v, visitor, path + (k,))
        if k is None:
            visitor([], path)
    else:
        visitor(obj, path)


def visit(fp, visitor):
    token_stream = tokenize(fp)
    _, token = next(token_stream)
    obj = TransientStreamingJSONBase.factory(token, token_stream)
    _visit(obj, visitor, ())
