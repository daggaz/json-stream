import json
from io import StringIO
from unittest import TestCase

import json_stream
from json_stream.dump import default, JSONStreamEncoder


class TestDump(TestCase):
    JSON = '{"count": 3, "results": ["a", "b", "c"]}'

    def test_dump_default(self):
        data = json_stream.load(StringIO(self.JSON), persistent=True)
        output = json.dumps(data, default=default)
        self._assert_json_okay(output)

    def test_dump_cls(self):
        data = json_stream.load(StringIO(self.JSON), persistent=True)
        output = json.dumps(data, cls=JSONStreamEncoder)
        self._assert_json_okay(output)

    def test_dump_context(self):
        data = json_stream.load(StringIO(self.JSON), persistent=True)
        with JSONStreamEncoder():
            output = json.dumps(data)
        self._assert_json_okay(output)

    def _assert_json_okay(self, value):
        self.assertEqual('{"count": 3, "results": ["a", "b", "c"]}', value)
