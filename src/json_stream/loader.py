from json_stream.base import factory
from json_stream.iterators import ensure_file
from json_stream.select_tokenizer import default_tokenizer
from json_stream.tokenizer import OPERATOR


def load(fp_or_iterable, persistent=False, tokenizer=default_tokenizer):
    fp = ensure_file(fp_or_iterable)
    token_stream = tokenizer(fp)
    token_type, token = next(token_stream)
    if token_type == OPERATOR:
        return factory[persistent, token](token_stream)
    return token
