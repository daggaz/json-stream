from io import StringIO
from unittest import skipUnless, TestCase, skip

import json_stream_rs_tokenizer

from json_stream import load
from json_stream.select_tokenizer import default_tokenizer

from json_stream.tests import JsonStreamTestCase


@skipUnless(hasattr(json_stream_rs_tokenizer, 'RustTokenizer'), 'rust tokenizer not available')
class TestsyncRSTokenizer(JsonStreamTestCase):
    def _tokenizer(self: TestCase):
        self.assertIs(default_tokenizer, json_stream_rs_tokenizer.RustTokenizer)
        return default_tokenizer

    def test_load_object(self: JsonStreamTestCase):
        obj = {"a": 1, "b": None, "c": True}
        self._test_object(obj, persistent=False)

    def test_load_object_binary(self: JsonStreamTestCase):
        obj = {"a": 1, "b": None, "c": True}
        self._test_object(obj, persistent=False, binary=True)

    def test_unterminated_string(self: JsonStreamTestCase):
        with self.assertRaisesRegex(ValueError, "Unterminated string"):
            load(StringIO('["unterminated')).read_all()


@skipUnless(hasattr(json_stream_rs_tokenizer, 'RustTokenizer'), 'rust tokenizer not available')
@skip('Rust tokenizer is not async compatible yet')
class TestAsyncRSTokenizer(TestCase):
    pass
