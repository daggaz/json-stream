from json_stream.base import StreamingJSONBase, TokenType
from json_stream.iterators import ensure_file
from json_stream.select_tokenizer import default_tokenizer


def load(fp_or_iterable, persistent=False, tokenizer=default_tokenizer, buffering=-1, strings_as_files=False):
    fp = ensure_file(fp_or_iterable)
    token_stream = tokenizer(fp, buffering=buffering, strings_as_files=strings_as_files)
    token_type, token = next(token_stream)
    if token_type == TokenType.OPERATOR:
        return StreamingJSONBase.factory(token, token_stream, persistent)
    return token
