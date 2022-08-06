from json_stream.base import StreamingJSONObject, StreamingJSONList, StreamingJSONBase
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


def visit(fp, visitor, tokenizer=tokenize):
    token_stream = tokenizer(fp)
    _, token = next(token_stream)
    obj = StreamingJSONBase.factory(token, token_stream, persistent=False)
    _visit(obj, visitor, ())
