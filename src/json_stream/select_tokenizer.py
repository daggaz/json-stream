from warnings import warn

from json_stream.tokenizer import tokenize
from json_stream_rs_tokenizer import rust_tokenizer_or_raise, ExtensionException, RequestedFeatureUnavailable

try:
    default_tokenizer = rust_tokenizer_or_raise()
except RequestedFeatureUnavailable as e:
    warn(  # raise warning about degraded rust extension
        f"json-stream's rust tokenizer extensions are not fully functional on this platform:"
        f"{str(e)}"
        f"You can swap to the slower pure-python tokenizer implementation by passing"
        f"tokenizer=json_stream.tokenizer.tokenize to any json-stream function",
    )
    default_tokenizer = rust_tokenizer_or_raise(requires_bigint=False)
except ExtensionException as e:
    warn(str(e), category=ImportWarning)  # ImportWarnings are ignored by default
    default_tokenizer = tokenize

__all__ = ['default_tokenizer']
