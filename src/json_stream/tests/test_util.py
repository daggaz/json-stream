from io import StringIO
import json
from unittest import TestCase

import json_stream


class TestToStandardTypes(TestCase):
    JSON = '{"x": 1, "y": {}, "xxxx": [1,2, {"yyyy": 1}, "z", 1, []]}'

    def test_to_standard_types(self):
        js = json_stream.load(StringIO(self.JSON))
        converted = json_stream.to_standard_types(js)
        comparison = json.load(StringIO(self.JSON))
        self.assertEqual(converted, comparison)
