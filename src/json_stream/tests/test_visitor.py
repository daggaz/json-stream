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
