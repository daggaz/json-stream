from json_stream.base import StreamingJSONBase, TokenType
from json_stream.select_tokenizer import get_token_stream


def load(fp_or_iterable, persistent=False, tokenizer=None, buffering=-1, **kwargs):
    token_stream = get_token_stream(fp_or_iterable, tokenizer=tokenizer, buffering=buffering, **kwargs)
    token_type, token = next(token_stream)
    if token_type == TokenType.OPERATOR:
        return StreamingJSONBase.factory(token, token_stream, persistent)
    return token
