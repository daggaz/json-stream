import io
from unittest import TestCase
from json_stream.iterators import IterableStream


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

    def test_read_str_chunks(self):
        # create some chunks of text data
        data_str = (
            "a" * io.DEFAULT_BUFFER_SIZE,
            "b" * (io.DEFAULT_BUFFER_SIZE + 1),
            "c" * (io.DEFAULT_BUFFER_SIZE - 1),
        )
        expected = ("".join(data_str)).encode()

        # stream it and check the result
        stream = IterableStream(data_str)
        self.assertEqual(stream.read(), expected)
