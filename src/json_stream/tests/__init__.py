import asyncio
import json
from io import BytesIO, StringIO
from itertools import zip_longest
from unittest import TestCase

from json_stream import load, aload
from json_stream.base import TransientAccessException
from json_stream.tokenizer import tokenize


class JSONLoadTestCase(TestCase):
    def _test_object(self, obj, persistent, binary=False):
        self.assertListEqual(list(self._to_data(obj, persistent, binary)), list(obj))
        self.assertListEqual(list(self._to_data(obj, persistent, binary).keys()), list(obj.keys()))
        self.assertListEqual(list(self._to_data(obj, persistent, binary).values()), list(obj.values()))
        self.assertListEqual(list(self._to_data(obj, persistent, binary).items()), list(obj.items()))

        for key in obj.keys():
            self.assertEqual(self._to_data(obj, persistent, binary).get(key), obj[key])

        self.assertFalse("foobar" in obj.keys())
        self.assertEqual(self._to_data(obj, persistent, binary).get("foobar"), None)
        self.assertEqual(self._to_data(obj, persistent, binary).get("foobar", "specified default"), "specified default")

        if persistent:
            self.assertEqual(len(self._to_data(obj, persistent, binary)), len(obj))
        for k, expected_k in zip_longest(self._to_data(obj, persistent, binary), obj):
            self.assertEqual(k, expected_k)

        if not persistent:
            data = self._to_data(obj, persistent, binary)
            iter(data)  # iterates first time
            with self.assertRaises(TransientAccessException):
                iter(data)  # can't get second iterator
            with self.assertRaises(TransientAccessException):
                data.keys()  # can't get keys
            with self.assertRaises(TransientAccessException):
                data.values()  # can't get keys
            with self.assertRaises(TransientAccessException):
                data.items()  # can't get keys

    def _test_list(self, obj, persistent, binary=False):
        self.assertListEqual(list(self._to_data(obj, persistent, binary)), list(obj))
        if persistent:
            self.assertEqual(len(self._to_data(obj, persistent, binary)), len(obj))
        for k, expected_k in zip_longest(self._to_data(obj, persistent, binary), obj):
            self.assertEqual(k, expected_k)

        if not persistent:
            data = self._to_data(obj, persistent, binary)
            iter(data)  # iterates first time
            with self.assertRaises(TransientAccessException):
                iter(data)  # can't get second iterator

    def _tokenizer(self):
        return tokenize

    def _to_stream(self, obj, *, binary=False):
        raise NotImplementedError()

    def _to_data(self, obj, persistent, binary):
        raise NotImplementedError()


class SyncJSONLoadTestCase(JSONLoadTestCase):
    def _to_stream(self, obj, *, binary=False):
        data = json.dumps(obj)
        if binary:
            return BytesIO(data.encode())
        return StringIO(data)

    def _to_data(self, obj, persistent, binary):
        stream = self._to_stream(obj, binary=binary)
        tokenizer = self._tokenizer()
        return load(stream, persistent=persistent, tokenizer=tokenizer)


class AsyncJSONLoadTestCase(JSONLoadTestCase):
    def _to_stream(self, obj, *, binary=False):
        data = json.dumps(obj)
        if binary:
            return ABytesIO(data.encode())
        return AStringIO(data)

    def _to_data(self, obj, persistent, binary):
        return asyncio.run(self._ato_data(obj, persistent, binary))

    async def _ato_data(self, obj, persistent, binary):
        stream = self._to_stream(obj, binary=binary)
        tokenizer = self._tokenizer()
        return await aload(stream, persistent=persistent, tokenizer=tokenizer)


class ABytesIO:
    def __init__(self, data: bytes):
        self.reader = asyncio.StreamReader()
        self.reader.feed_data(data)
        self.reader.feed_eof()

    async def read(self, n=-1) -> bytes:
        return await self.reader.read(n)


class AStringIO:
    def __init__(self, data: str):
        self.io = ABytesIO(data.encode())

    async def read(self, n=-1) -> str:
        return (await self.io.read(n)).decode()
