from io import StringIO
from unittest import TestCase

import json_stream


class TestVisitor(TestCase):
    def test_visitor(self):
        json = '{"x": 1, "y": {}, "xxxx": [1,2, {"yyyy": 1}, "z", 1, []]}'
        visited = []
        json_stream.visit(StringIO(json), lambda a, b: visited.append((a, b)))
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
