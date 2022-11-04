from json_stream.base import StreamingJSONBase
from json_stream.iterators import ensure_file
from json_stream.select_tokenizer import default_tokenizer


def load(fp_or_iterable, persistent=False, tokenizer=default_tokenizer):
    fp = ensure_file(fp_or_iterable)
    token_stream = tokenizer(fp)
    _, token = next(token_stream)
    return StreamingJSONBase.factory(token, token_stream, persistent)
