from json_stream.base import StreamingJSONObject, StreamingJSONList, factory
from json_stream.iterators import ensure_file
from json_stream.select_tokenizer import default_tokenizer


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


def visit(fp_or_iterator, visitor, tokenizer=default_tokenizer):
    fp = ensure_file(fp_or_iterator)
    token_stream = tokenizer(fp)
    _, token = next(token_stream)
    obj = factory[False, token](token_stream)
    _visit(obj, visitor, ())
