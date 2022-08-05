from json_stream.base import StreamingJSONBase
from json_stream.tokenizer import tokenize


def load(fp, persistent=False, tokenizer=tokenize):
    token_stream = tokenizer(fp)
    _, token = next(token_stream)
    return StreamingJSONBase.factory(token, token_stream, persistent)
