from typing import Mapping, Sequence

from json_stream.tests import JsonStreamTestCase


class TestSyncCollectionABCs(JsonStreamTestCase):
    def test_isinstance_sequence(self):
        for persistent in (True, False):
            with self.subTest(persistent=persistent):
                self.assertIsInstance(self._to_data([], persistent,  False), Sequence)

    def test_isinstance_mapping(self):
        for persistent in (True, False):
            with self.subTest(persistent=persistent):
                self.assertIsInstance(self._to_data({}, persistent,  False), Mapping)
