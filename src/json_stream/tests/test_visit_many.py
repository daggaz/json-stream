from io import StringIO
from unittest import TestCase

import json_stream


class TestVisitMany(TestCase):
    def test_visit_many(self):
        payload = "\n".join([
            '{"a": 1}',
            '[1, 2]',
            '3',
            'true',
            'null',
            '"x"',
            '{}',
            '[]',
        ])
        stream = StringIO(payload)

        visited_batches = []
        current = []

        def visitor(item, path):
            current.append((item, path))

        for _ in json_stream.visit_many(stream, visitor):
            visited_batches.append(current)
            current = []

        # We only verify that per-top-level JSON text we received at least one visit
        # and that the first visited path matches the expected top-level structure.
        # Detailed traversal behavior is covered by other visitor tests.
        self.assertEqual(len(visited_batches), 8)
        self.assertEqual(visited_batches[0][0], (1, ('a',)))          # {"a": 1}
        self.assertEqual(visited_batches[1][0], (1, (0,)))            # [1, 2]
        self.assertEqual(visited_batches[2][0], (3, ()))              # 3
        self.assertEqual(visited_batches[3][0], (True, ()))           # true
        self.assertEqual(visited_batches[4][0], (None, ()))           # null
        self.assertEqual(visited_batches[5][0], ("x", ()))           # "x"
        self.assertEqual(visited_batches[6][0], ({}, ()))             # {}
        self.assertEqual(visited_batches[7][0], ([], ()))             # []
