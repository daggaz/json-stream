import json
from io import StringIO
from unittest import TestCase

from json_stream.writer import streamable_dict, streamable_list


class TestWriter(TestCase):
    def test_writer_wrapper(self):
        def dict_content(n):
            yield "a  list", streamable_list(range(4))

        o = streamable_dict(dict_content(5))

        buffer = StringIO()
        json.dump(o, buffer)
        self.assertEqual('{"a  list": [0, 1, 2, 3]}', buffer.getvalue())

    def test_writer_decorator(self):

        @streamable_list
        def list_content(n):
            return range(n)

        @streamable_dict
        def dict_content(n):
            yield "a  list", list_content(n)

        o = dict_content(5)

        buffer = StringIO()
        json.dump(o, buffer)
        self.assertEqual('{"a  list": [0, 1, 2, 3, 4]}', buffer.getvalue())

    def test_writer_empty(self):

        @streamable_list
        def empty_list():
            for i in range(0):  # never yields
                yield i

        o = empty_list()

        buffer = StringIO()
        json.dump(o, buffer)
        self.assertEqual('[]', buffer.getvalue())
