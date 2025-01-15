from io import StringIO
from unittest import skipUnless

import json_stream_rs_tokenizer

from json_stream import load

from json_stream.select_tokenizer import get_tokenizer

from json_stream.tests import JSONLoadTestCase


@skipUnless(hasattr(json_stream_rs_tokenizer, 'RustTokenizer'), 'rust tokenizer not available')
class TestRSTokenizer(JSONLoadTestCase):
    def test_load_object(self):
        self.assertIs(get_tokenizer(), json_stream_rs_tokenizer.RustTokenizer)
        obj = {"a": 1, "b": None, "c": True}
        self._test_object(obj, persistent=False)

    def test_load_object_binary(self):
        self.assertIs(get_tokenizer(), json_stream_rs_tokenizer.RustTokenizer)
        obj = {"a": 1, "b": None, "c": True}
        self._test_object(obj, persistent=False, binary=True)

    def test_unterminated_string(self):
        with self.assertRaisesRegex(ValueError, "Unterminated string"):
            load(StringIO('["unterminated')).read_all()
