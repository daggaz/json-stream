from json_stream.base import StreamingJSONBase, TokenType
from json_stream.iterators import ensure_file
from json_stream.select_tokenizer import default_tokenizer


def load(fp_or_iterable, persistent=False, tokenizer=default_tokenizer):
    return next(load_many(fp_or_iterable, persistent, tokenizer))


def load_many(fp_or_iterable, persistent=False, tokenizer=default_tokenizer):
    fp = ensure_file(fp_or_iterable)
    token_stream = tokenizer(fp)
    for token_type, token in token_stream:
        if token_type == TokenType.OPERATOR:
            data = StreamingJSONBase.factory(token, token_stream, persistent)
            yield data
            data.read_all()
        else:
            yield token
