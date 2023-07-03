import json_stream


CONTENT_CHUNK_SIZE = 10 * 1024


def _to_iterable(response, chunk_size):
    return response.iter_bytes(chunk_size=chunk_size)


def load(response, persistent=False, tokenizer=None, chunk_size=CONTENT_CHUNK_SIZE, buffering=0, **kwargs):
    return json_stream.load(
        _to_iterable(response, chunk_size),
        persistent=persistent,
        tokenizer=tokenizer,
        buffering=buffering,
        **kwargs
    )


def visit(response, visitor, tokenizer=None, chunk_size=CONTENT_CHUNK_SIZE, buffering=0, **kwargs):
    return json_stream.visit(
        _to_iterable(response, chunk_size),
        visitor,
        tokenizer=tokenizer,
        buffering=buffering,
        **kwargs
    )
