import copy
import json
from io import StringIO, BytesIO
from itertools import zip_longest
from unittest import TestCase

from json_stream import load
from json_stream.base import (
    TransientAccessException,
    PersistentStreamingJSONObject,
    TransientStreamingJSONList,
    TransientStreamingJSONObject,
    PersistentStreamingJSONList,
)


class TestLoader(TestCase):
    def test_load_empty_object(self):
        obj = {}
        self._test_object(obj, persistent=True)
        self._test_object(obj, persistent=False)

    def test_load_object(self):
        obj = {"a": 1, "b": None, "c": True}
        self._test_object(obj, persistent=True)
        self._test_object(obj, persistent=False)

    def test_load_object_binary(self):
        obj = {"a": 1, "b": None, "c": True}
        self._test_object(obj, persistent=True, binary=True)
        self._test_object(obj, persistent=False, binary=True)

    def test_load_object_get_persistent(self):
        json_str = '{"a": 1, "b": null, "c": true}'

        # Access in order
        data = load(StringIO(json_str), persistent=True)
        self.assertEqual(data['a'], 1)
        self.assertEqual(data['b'], None)
        self.assertEqual(data['c'], True)
        with self.assertRaises(KeyError):
            _ = data['d']

        # Access out of order
        data = load(StringIO(json_str), persistent=True)
        self.assertEqual(data['b'], None)
        self.assertEqual(data['a'], 1)
        self.assertEqual(data['c'], True)
        with self.assertRaises(KeyError):
            _ = data['d']

        # Access with key error first order
        data = load(StringIO(json_str), persistent=True)
        with self.assertRaises(KeyError):
            _ = data['d']
        self.assertEqual(data['a'], 1)
        self.assertEqual(data['b'], None)
        self.assertEqual(data['c'], True)

    def test_load_object_get_transient(self):
        json_str = '{"a": 1, "b": null, "c": true}'

        # Access in order
        data = load(StringIO(json_str), persistent=False)
        self.assertEqual(data['a'], 1)
        self.assertEqual(data['b'], None)
        self.assertEqual(data['c'], True)
        with self.assertRaises(TransientAccessException):
            _ = data['d']

        # Access out of order
        data = load(StringIO(json_str), persistent=False)
        self.assertEqual(data['b'], None)
        with self.assertRaises(TransientAccessException):
            _ = data['a']
        with self.assertRaises(TransientAccessException):
            _ = data['c']  # stream was exhausted in search for 'a'
        with self.assertRaises(TransientAccessException):
            _ = data['d']  # don't know if this was a key error or was in the past

        # Access with key error first order
        data = load(StringIO(json_str), persistent=False)
        with self.assertRaises(KeyError):
            _ = data['d']
        with self.assertRaises(TransientAccessException):
            _ = data['a']  # stream was exhausted in search for 'd'

    def test_load_empty_list(self):
        obj = []
        self._test_list(obj, persistent=True)
        self._test_list(obj, persistent=False)

    def test_load_list(self):
        obj = [1, True, ""]
        self._test_list(obj, persistent=True)
        self._test_list(obj, persistent=False)

    def test_load_list_get_persistent(self):
        json_str = '[1, true, ""]'

        # Access in order
        data = load(StringIO(json_str), persistent=True)
        self.assertEqual(data[0], 1)
        self.assertTrue(data[1])
        self.assertEqual(data[2], "")
        with self.assertRaises(IndexError):
            _ = data[3]

        # Access out of order
        data = load(StringIO(json_str), persistent=True)
        self.assertEqual(data[0], 1)
        self.assertTrue(data[1])
        self.assertEqual(data[2], "")
        with self.assertRaises(IndexError):
            _ = data[3]

    def test_load_list_get_transient(self):
        json_str = '[1, true, ""]'

        # Access in order
        data = load(StringIO(json_str), persistent=False)
        self.assertEqual(data[0], 1)
        self.assertTrue(data[1])
        self.assertEqual(data[2], "")
        with self.assertRaises(IndexError):
            _ = data[3]

        # Access out of order
        data = load(StringIO(json_str), persistent=False)
        self.assertTrue(data[1])
        with self.assertRaises(TransientAccessException):
            _ = data[0]
        self.assertEqual(data[2], "")
        with self.assertRaises(IndexError):
            _ = data[3]

    def test_load_nested_persistent(self):
        json_str = '{"count": 3, "results": ["a", "b", {}]}'
        data = load(StringIO(json_str), persistent=True)
        self.assertIsInstance(data, PersistentStreamingJSONObject)
        results = data['results']
        self.assertIsInstance(results, PersistentStreamingJSONList)
        self.assertEqual(results[0], 'a')
        self.assertEqual(results[1], 'b')
        self.assertIsInstance(results[2], PersistentStreamingJSONObject)
        self.assertEqual(len(results), 3)
        self.assertEqual(len(results[2]), 0)
        self.assertEqual(len(data), 2)
        self.assertEqual(data["count"], 3)

    def test_load_nested_transient(self):
        json_str = '{"count": 3, "results": ["a", "b", "c"]}'
        data = load(StringIO(json_str), persistent=False)
        self.assertIsInstance(data, TransientStreamingJSONObject)
        results = data['results']
        self.assertIsInstance(results, TransientStreamingJSONList)
        self.assertEqual(list(results), ['a', 'b', 'c'])

    def test_load_nested_transient_first_list_item_object(self):
        json_str = '[{"a": 4}, "b", "c"]'
        data = load(StringIO(json_str), persistent=False)
        self.assertIsInstance(data, TransientStreamingJSONList)
        items = iter(data)
        item = next(items)
        self.assertIsInstance(item, TransientStreamingJSONObject)
        self.assertDictEqual({"a": 4}, dict(item.items()))
        self.assertEqual(list(items), ['b', 'c'])

    def test_load_nested_transient_first_list_item_list(self):
        json_str = '[["a"], "b", "c"]'
        data = load(StringIO(json_str), persistent=False)
        self.assertIsInstance(data, TransientStreamingJSONList)
        items = iter(data)
        item = next(items)
        self.assertIsInstance(item, TransientStreamingJSONList)
        self.assertListEqual(["a"], list(item))
        self.assertEqual(list(items), ['b', 'c'])

    def test_not_copiable(self):
        json_str = '[["a"], "b", "c"]'
        with self.assertRaisesRegex(copy.Error, "^Copying json_steam objects leads to a bad time$"):
            copy.copy(load(StringIO(json_str)))
        with self.assertRaisesRegex(copy.Error, "^Copying json_steam objects leads to a bad time$"):
            copy.deepcopy(load(StringIO(json_str)))

    def test_transient_to_persistent(self):
        json_str = '{"results": [{"x": 1, "y": 3}, {"y": 4, "x": 2}]}'
        xs = iter((1, 2))
        ys = iter((3, 4))

        data = load(StringIO(json_str))  # data is a transient dict-like object
        self.assertIsInstance(data, TransientStreamingJSONObject)

        results = data['results']
        self.assertIsInstance(results, TransientStreamingJSONList)

        # iterate transient list, but produce persistent items
        for result in results.persistent():
            # result is a persistent dict-like object
            self.assertIsInstance(result, PersistentStreamingJSONObject)
            x = next(xs)
            y = next(ys)
            self.assertEqual(result['x'], x)
            self.assertEqual(result['y'], y)  # would error on second result without .persistent()
            self.assertEqual(result['x'], x)  # would error without .persistent()

    def test_persistent_to_transient(self):
        json_str = """{"a": 1, "x": ["long", "list", "I", "don't", "want", "in", "memory"], "b": 2}"""
        data = load(StringIO(json_str), persistent=True).transient()
        self.assertIsInstance(data, PersistentStreamingJSONObject)

        self.assertEqual(data["a"], 1)
        list_ = data["x"]
        self.assertIsInstance(list_, TransientStreamingJSONList)
        self.assertEqual(data["b"], 2)
        self.assertEqual(data["b"], 2)  # would error if data was transient
        with self.assertRaisesRegex(TransientAccessException, "Index 0 already passed in this stream"):
            _ = list_[0]  # cannot access transient list

    def _test_object(self, obj, persistent, binary=False):
        self.assertListEqual(list(self._to_data(obj, persistent, binary)), list(obj))
        self.assertListEqual(list(self._to_data(obj, persistent, binary).keys()), list(obj.keys()))
        self.assertListEqual(list(self._to_data(obj, persistent, binary).values()), list(obj.values()))
        self.assertListEqual(list(self._to_data(obj, persistent, binary).items()), list(obj.items()))
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

    def _test_list(self, obj, persistent):
        self.assertListEqual(list(self._to_data(obj, persistent)), list(obj))
        if persistent:
            self.assertEqual(len(self._to_data(obj, persistent)), len(obj))
        for k, expected_k in zip_longest(self._to_data(obj, persistent), obj):
            self.assertEqual(k, expected_k)

        if not persistent:
            data = self._to_data(obj, persistent)
            iter(data)  # iterates first time
            with self.assertRaises(TransientAccessException):
                iter(data)  # can't get second iterator

    def _to_data(self, obj, persistent, binary=False):
        data = json.dumps(obj)
        if binary:
            stream = BytesIO(data.encode())
        else:
            stream = StringIO(data)
        return load(stream, persistent)
