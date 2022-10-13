from json_stream.base import StreamingJSONBase
from json_stream.select_tokenizer import default_tokenizer


def load(fp, persistent=False, tokenizer=default_tokenizer):
    token_stream = tokenizer(fp)
    _, token = next(token_stream)
    return StreamingJSONBase.factory(token, token_stream, persistent)
