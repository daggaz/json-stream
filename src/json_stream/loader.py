from json_stream.base import StreamingJSONBase
from json_stream.tokenizer import tokenize


def load(fp, persistent=False):
    token_stream = tokenize(fp)
    _, token = next(token_stream)
    return StreamingJSONBase.factory(token, token_stream, persistent)
