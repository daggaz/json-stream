import unittest
from io import StringIO, BytesIO
from unittest import TestCase

import json_stream
from json_stream import to_standard_types


class TestLoadMany(TestCase):
    def test_load_many(self):
        # NDJSON-like: one JSON value per line
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
        items = [
            to_standard_types(v) for v in json_stream.load_many(stream, persistent=True)
        ]
        self.assertListEqual(
            items,
            [
                {"a": 1},
                [1, 2],
                3,
                True,
                None,
                "x",
                {},
                [],
            ],
        )

    def test_load_many_concatenated(self):
        payload = b'{"a": 1}[1,2]truenull"x"{}[]'
        stream = BytesIO(payload)
        items = [
            to_standard_types(v) for v in json_stream.load_many(stream, persistent=False)
        ]
        # Even when persistent=False, materialization should consume correctly per item
        self.assertListEqual(
            items,
            [
                {"a": 1},
                [1, 2],
                True,
                None,
                "x",
                {},
                [],
            ],
        )

    @unittest.expectedFailure
    def test_load_many_incompatible_concatenations(self):
        # this fails because the tokeniser want's certain primitives to be followed by delimiter
        payloads = [
            [b'{"a": 1}[]', [{"a": 1}, []]],  # this one works
            [b'3true', [3, True]],
            [b'3.0true', [3.0, True]],
            [b'1.2e11true', [120000000000.0, True]],
            [b'0true', [0, True]],
            [b'""true', [0, True]],
        ]
        errors = []
        for payload, expected in payloads:
            try:
                stream = BytesIO(payload)
                items = [
                    to_standard_types(v) for v in json_stream.load_many(stream, persistent=False)
                ]
                self.assertListEqual(expected, items)
            except ValueError as e:
                errors.append(f"{payload}: {e}")
        self.assertListEqual([], errors)

    def test_load_many_skips_after_item_partially_consumed(self):
        # Ensure that after yielding an object/array, the generator resumes and continues
        # to the next top-level JSON text correctly.
        payload = '{"first": [1, 2, 3]} {"second": {"x": 1}, "unconsumed": 7} 4'
        stream = StringIO(payload)

        gen = json_stream.load_many(stream, persistent=True)

        first = next(gen)
        # consume partially then fully
        self.assertEqual(list(first["first"]), [1, 2, 3])

        second = next(gen)
        self.assertEqual(dict(second["second"].items()), {"x": 1})

        third = next(gen)
        self.assertEqual(third, 4)

        with self.assertRaises(StopIteration):
            next(gen)
