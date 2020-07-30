import io
import json
from itertools import zip_longest
from unittest import TestCase
from unittest.mock import Mock

from json_stream.requests import IterableStream, load


class TestIterableStream(TestCase):
    def test_read(self):
        # create some chunks of binary data
        data = (
            b"a" * io.DEFAULT_BUFFER_SIZE,
            b"b" * (io.DEFAULT_BUFFER_SIZE + 1),
            b"c" * (io.DEFAULT_BUFFER_SIZE - 1),
        )

        # stream it and check the result
        stream = IterableStream(data)
        self.assertEqual(stream.read(), b"".join(data))


class TestLoad(TestCase):
    @staticmethod
    def grouper(iterable, n):
        "Collect data into fixed-length chunks or blocks"
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue="")

    def test_load_persistent(self):
        # requests iter_content returns an iterable of bytes
        response = Mock()
        data = json.dumps({
            "a": "a" * io.DEFAULT_BUFFER_SIZE,
            "b": "b",
        })
        content = ("".join(chunk).encode() for chunk in self.grouper(data, 1024))
        response.iter_content.return_value = content

        # load in persistent mode
        data = load(response, persistent=True)

        # is streaming
        self.assertTrue(data.streaming)

        # check the data
        self.assertTupleEqual(
            (
                ("a", "a" * io.DEFAULT_BUFFER_SIZE),
                ("b", "b"),
            ),
            tuple(sorted(data.items())),
        )

        # all done?
        self.assertFalse(data.streaming)

    def test_load_transient(self):
        # requests iter_content returns an iterable of bytes
        response = Mock()
        data = json.dumps({
            "a": "a" * io.DEFAULT_BUFFER_SIZE,
            "b": "b",
        })
        content = ("".join(chunk).encode() for chunk in self.grouper(data, 1024))
        response.iter_content.return_value = content

        # load in transient mode
        data = load(response, persistent=False)

        # is streaming
        self.assertTrue(data.streaming)

        # check the data
        self.assertTupleEqual(
            (
                ("a", "a" * io.DEFAULT_BUFFER_SIZE),
                ("b", "b"),
            ),
            tuple(sorted(data.items())),
        )

        # all done?
        self.assertFalse(data.streaming)
