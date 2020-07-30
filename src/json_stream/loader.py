from json_stream.base import StreamingJSONBase, PersistentStreamingJSONBase, TransientStreamingJSONBase
from json_stream.tokenizer import tokenize


def load(fp, persistent=False):
    token_stream = tokenize(fp)
    _, token = next(token_stream)

    if persistent:
        return PersistentStreamingJSONBase.factory(token, token_stream)
    else:
        return TransientStreamingJSONBase.factory(token, token_stream)
