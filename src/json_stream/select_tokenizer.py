from warnings import warn

from json_stream.iterators import ensure_file
from json_stream.tokenizer import tokenize
from json_stream_rs_tokenizer import rust_tokenizer_or_raise, ExtensionException


def get_tokenizer(**kwargs):
    try:
        return rust_tokenizer_or_raise(**kwargs)
    except ExtensionException as e:
        warn(str(e), category=ImportWarning)  # ImportWarnings are ignored by default
        return tokenize


def get_token_stream(fp_or_iterable, tokenizer, **tokenizer_kwargs):
    fp = ensure_file(fp_or_iterable)
    if tokenizer is None:
        tokenizer = get_tokenizer(**tokenizer_kwargs)
    return tokenizer(fp, **tokenizer_kwargs)
