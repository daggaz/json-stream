from io import StringIO, BytesIO
from unittest import TestCase

import json_stream


class TestVisitor(TestCase):
    JSON = '{"x": 1, "y": {}, "xxxx": [1,2, {"yyyy": 1}, "z", 1, []]}'

    def test_visitor(self):
        visited = []
        json_stream.visit(StringIO(self.JSON), lambda a, b: visited.append((a, b)))
        self._assert_data_okay(visited)

    def test_visitor_binary(self):
        visited = []
        json_stream.visit(BytesIO(self.JSON.encode()), lambda a, b: visited.append((a, b)))
        self._assert_data_okay(visited)

    def test_visitor_primitive(self):
        visited = []
        json_stream.visit(StringIO("1"), lambda a, b: visited.append((a, b)))
        self.assertListEqual([(1, ())], visited)

    def test_visitor_without_json_value(self):
        for text in ('', ' \t\r\n'):
            sources = [
                StringIO(text), BytesIO(text.encode()),
                [text], [text.encode()],
                list(text), [char.encode() for char in text],
            ]
            for source in sources:
                with self.subTest(text=text, source=source):
                    visited = []
                    with self.assertRaisesRegex(ValueError, 'No JSON value found'):
                        json_stream.visit(source, lambda a, b: visited.append((a, b)))
                    self.assertListEqual([], visited)

    def test_visit_many_without_json_value(self):
        for text in ('', ' \t\r\n'):
            for source in (StringIO(text), BytesIO(text.encode())):
                with self.subTest(text=text, source=source):
                    visited = []
                    self.assertListEqual([], list(json_stream.visit_many(source, lambda a, b: visited.append((a, b)))))
                    self.assertListEqual([], visited)

    def _assert_data_okay(self, visited):
        self.assertListEqual([
            (1, ('x',)),
            ({}, ('y',)),
            (1, ('xxxx', 0)),
            (2, ('xxxx', 1)),
            (1, ('xxxx', 2, 'yyyy')),
            ("z", ('xxxx', 3)),
            (1, ('xxxx', 4)),
            ([], ('xxxx', 5)),
        ], visited)
