from json_stream.base import StreamingJSONObject, StreamingJSONList, StreamingJSONBase
from json_stream.iterators import ensure_file
from json_stream.select_tokenizer import default_tokenizer
from json_stream.tokenizer import TokenType


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


def visit_many(fp_or_iterator, visitor, tokenizer=default_tokenizer):
    fp = ensure_file(fp_or_iterator)
    token_stream = tokenizer(fp)
    for token_type, token in token_stream:
        if token_type == TokenType.OPERATOR:
            obj = StreamingJSONBase.factory(token, token_stream, persistent=False)
            _visit(obj, visitor, ())
            obj.read_all()
        else:
            _visit(token, visitor, ())
        yield


def visit(fp_or_iterator, visitor, tokenizer=default_tokenizer):
    next(visit_many(fp_or_iterator, visitor, tokenizer))
