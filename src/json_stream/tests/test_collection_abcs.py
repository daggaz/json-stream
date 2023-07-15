from typing import Mapping, Sequence

from json_stream.select_tokenizer import default_tokenizer
from json_stream.tests import JSONLoadTestCase


class TestCollectionABCs(JSONLoadTestCase):

    def test_isinstance_sequence(self):
        for persistent in (True, False):
            with self.subTest(persistent=persistent):
                self.assertIsInstance(self._to_data([], persistent,  False, default_tokenizer), Sequence)

    def test_isinstance_mapping(self):
        for persistent in (True, False):
            with self.subTest(persistent=persistent):
                self.assertIsInstance(self._to_data({}, persistent,  False, default_tokenizer), Mapping)
