from unittest import TestCase

import json_stream
from json_stream import to_standard_types


class TestBuffering(TestCase):
    def test_no_buffering(self):
        happenings = []

        def data_in_chunks(data, chunk_size=15):
            for i in range(0, len(data), chunk_size):
                part = data[i:i + chunk_size]
                happenings.append(('yield', part))
                yield part

        json_string = b'{"tasks":[{"id":1,"title":"task1"},{"id":2,"title":"task2"},{"id":3,"title":"task3"}]}'
        stream = json_stream.load(data_in_chunks(json_string))

        for task in stream["tasks"]:
            happenings.append(('item', to_standard_types(task)))

        self.assertListEqual([
            ('yield', b'{"tasks":[{"id"'),
            ('yield', b':1,"title":"tas'),
            ('yield', b'k1"},{"id":2,"t'),
            ('item', {'id': 1, 'title': 'task1'}),
            ('yield', b'itle":"task2"},'),
            ('item', {'id': 2, 'title': 'task2'}),
            ('yield', b'{"id":3,"title"'),
            ('yield', b':"task3"}]}'),
            ('item', {'id': 3, 'title': 'task3'})
        ], happenings)
