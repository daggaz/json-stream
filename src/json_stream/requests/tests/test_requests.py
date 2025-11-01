import io
import json
from itertools import zip_longest
from unittest import TestCase
from unittest.mock import Mock

from json_stream import to_standard_types
from json_stream.requests import load, visit, load_many, visit_many


class TestLoad(TestCase):
    maxDiff = None

    @staticmethod
    def grouper(iterable, n):
        """Collect data into fixed-length chunks or blocks"""
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue="")

    def _create_mock_response(self, data=None):
        # requests iter_content returns an iterable of bytes
        response = Mock()
        if data is None:
            data = json.dumps({
                "a": "a" * io.DEFAULT_BUFFER_SIZE,
                "b": "b",
            })
        content = ("".join(chunk).encode() for chunk in self.grouper(data, 1024))
        response.iter_content.return_value = content
        return response

    def _assertDataOkay(self, data):
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

    def test_load_persistent(self):
        response = self._create_mock_response()

        # load in persistent mode
        data = load(response, persistent=True)

        self._assertDataOkay(data)

    def test_load_transient(self):
        response = self._create_mock_response()

        # load in transient mode
        data = load(response, persistent=False)

        self._assertDataOkay(data)

    def test_visitor(self):
        response = self._create_mock_response()

        visited = []
        visit(response, lambda item, path: visited.append((item, path)))

        self.assertListEqual([
            ('a' * io.DEFAULT_BUFFER_SIZE, ('a',)),
            ('b', ('b',)),
        ], visited)

    def test_load_many(self):
        expected = [{
            "a": "a" * io.DEFAULT_BUFFER_SIZE,
        }, {
            "b": "b" * io.DEFAULT_BUFFER_SIZE,
        }]
        data = "".join(json.dumps(i) for i in expected)
        response = self._create_mock_response(data=data)
        count = 0
        for item, exp in zip(load_many(response), expected):
            self.assertEqual(exp, to_standard_types(item))
            count += 1
        self.assertEqual(count, len(expected))

    def test_visit_many(self):
        items = [{
            "a": "a" * io.DEFAULT_BUFFER_SIZE,
        }, {
            "b": "b" * io.DEFAULT_BUFFER_SIZE,
        }]
        data = "".join(json.dumps(e) for e in items)
        response = self._create_mock_response(data=data)
        current_visit = []
        visits = []

        def visitor(item, path):
            current_visit.append((item, path))
        for _ in visit_many(response, visitor):
            visits.append(current_visit)
            current_visit = []
        self.assertEqual(len(visits), len(items))
        self.assertEqual(visits[0], [('a' * io.DEFAULT_BUFFER_SIZE, ('a',))])
        self.assertEqual(visits[1], [('b' * io.DEFAULT_BUFFER_SIZE, ('b',))])
