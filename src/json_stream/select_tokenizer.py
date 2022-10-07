from json_stream.tokenizer import tokenize

try:
    from json_stream_rs_tokenizer import RustTokenizer as default_tokenizer
except ImportError:
    default_tokenizer = tokenize

__all__ = ['default_tokenizer']
