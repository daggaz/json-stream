from json_stream.base import StreamingJSONObject, StreamingJSONList, StreamingJSONBase
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


def visit(fp_or_iterator, visitor, tokenizer=default_tokenizer, buffering=-1, strings_as_files=False):
    fp = ensure_file(fp_or_iterator)
    token_stream = tokenizer(fp, buffering=buffering, strings_as_files=strings_as_files)
    _, token = next(token_stream)
    obj = StreamingJSONBase.factory(token, token_stream, persistent=False)
    _visit(obj, visitor, ())
