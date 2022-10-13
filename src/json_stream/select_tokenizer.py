from warnings import warn

from json_stream.tokenizer import tokenize
from json_stream_rs_tokenizer import rust_tokenizer_or_raise, ExtensionException

try:
    default_tokenizer = rust_tokenizer_or_raise()
except ExtensionException as e:
    warn(str(e), category=ImportWarning)  # ImportWarnings are ignored by default
    default_tokenizer = tokenize

__all__ = ['default_tokenizer']
