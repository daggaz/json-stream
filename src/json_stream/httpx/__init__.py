import io

import json_stream
from json_stream.select_tokenizer import default_tokenizer
from json_stream.iter_utils import IterableStream


CONTENT_CHUNK_SIZE = 10 * 1024


def _to_file(response, chunk_size):
    return io.BufferedReader(IterableStream(response.iter_bytes(chunk_size=chunk_size)))


def load(response, persistent=False, tokenizer=default_tokenizer, chunk_size=CONTENT_CHUNK_SIZE):
    return json_stream.load(_to_file(response, chunk_size), persistent=persistent, tokenizer=tokenizer)


def visit(response, visitor, tokenizer=default_tokenizer, chunk_size=CONTENT_CHUNK_SIZE):
    return json_stream.visit(_to_file(response, chunk_size), visitor, tokenizer=tokenizer)
