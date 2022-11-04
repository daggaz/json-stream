import json
from io import BytesIO, StringIO
from itertools import zip_longest
from unittest import TestCase

from json_stream.select_tokenizer import default_tokenizer

from json_stream import load
from json_stream.base import TransientAccessException


class JSONLoadTestCase(TestCase):
    def _test_object(self, obj, persistent, binary=False, tokenizer=default_tokenizer):
        self.assertListEqual(list(self._to_data(obj, persistent, binary, tokenizer)), list(obj))
        self.assertListEqual(list(self._to_data(obj, persistent, binary, tokenizer).keys()), list(obj.keys()))
        self.assertListEqual(list(self._to_data(obj, persistent, binary, tokenizer).values()), list(obj.values()))
        self.assertListEqual(list(self._to_data(obj, persistent, binary, tokenizer).items()), list(obj.items()))

        for key in obj.keys():
            self.assertEqual(self._to_data(obj, persistent, binary, tokenizer).get(key), obj[key])

        self.assertFalse("foobar" in obj.keys())
        self.assertEqual(self._to_data(obj, persistent, binary, tokenizer).get("foobar"), None)
        self.assertEqual(self._to_data(obj, persistent, binary, tokenizer).get("foobar", "specified default"), "specified default")

        if persistent:
            self.assertEqual(len(self._to_data(obj, persistent, binary, tokenizer)), len(obj))
        for k, expected_k in zip_longest(self._to_data(obj, persistent, binary, tokenizer), obj):
            self.assertEqual(k, expected_k)

        if not persistent:
            data = self._to_data(obj, persistent, binary, tokenizer)
            iter(data)  # iterates first time
            with self.assertRaises(TransientAccessException):
                iter(data)  # can't get second iterator
            with self.assertRaises(TransientAccessException):
                data.keys()  # can't get keys
            with self.assertRaises(TransientAccessException):
                data.values()  # can't get keys
            with self.assertRaises(TransientAccessException):
                data.items()  # can't get keys

    def _test_list(self, obj, persistent, binary=False, tokenizer=default_tokenizer):
        self.assertListEqual(list(self._to_data(obj, persistent, binary, tokenizer)), list(obj))
        if persistent:
            self.assertEqual(len(self._to_data(obj, persistent, binary, tokenizer)), len(obj))
        for k, expected_k in zip_longest(self._to_data(obj, persistent, binary, tokenizer), obj):
            self.assertEqual(k, expected_k)

        if not persistent:
            data = self._to_data(obj, persistent, binary, tokenizer)
            iter(data)  # iterates first time
            with self.assertRaises(TransientAccessException):
                iter(data)  # can't get second iterator

    def _to_data(self, obj, persistent, binary, tokenizer):
        data = json.dumps(obj)
        if binary:
            stream = BytesIO(data.encode())
        else:
            stream = StringIO(data)
        return load(stream, persistent=persistent, tokenizer=tokenizer)
