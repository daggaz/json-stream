import json_stream
from json_stream.select_tokenizer import default_tokenizer


CONTENT_CHUNK_SIZE = 10 * 1024


def _to_iterable(response, chunk_size):
    return response.iter_content(chunk_size=chunk_size)


def load(response, persistent=False, tokenizer=default_tokenizer, chunk_size=CONTENT_CHUNK_SIZE):
    return json_stream.load(_to_iterable(response, chunk_size), persistent=persistent, tokenizer=tokenizer)


def visit(response, visitor, tokenizer=default_tokenizer, chunk_size=CONTENT_CHUNK_SIZE):
    return json_stream.visit(_to_iterable(response, chunk_size), visitor, tokenizer=tokenizer)
