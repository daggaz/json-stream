import io
import json
from unittest import TestCase, skipUnless
import json_stream

try:
    import json_stream_rs_tokenizer
    HAS_RS_TOKENIZER = hasattr(json_stream_rs_tokenizer, 'RustTokenizer')
except ImportError:
    HAS_RS_TOKENIZER = False

class TestBinaryResumption(TestCase):
    @skipUnless(HAS_RS_TOKENIZER, 'Rust tokenizer not available')
    def test_json_then_binary(self):
        json_header = json.dumps({"header": "info"})
        binary_data = b'\x00\x01\x02\x03'
        test_data = json_header.encode('utf-8') + binary_data
        test_file = io.BytesIO(test_data)
        
        # Load with correct_cursor=True
        header = json_stream.load(test_file, correct_cursor=True)
        
        # Consume all data from header
        header.read_all()
        
        # Signal that we are done with JSON and want to resume binary read
        header.tokenizer.park_cursor()
        
        # Verify file cursor position
        self.assertEqual(test_file.tell(), len(json_header))
        
        # Verify binary data
        remaining = test_file.read()
        self.assertEqual(remaining, binary_data)

    @skipUnless(HAS_RS_TOKENIZER, 'Rust tokenizer not available')
    def test_binary_then_json(self):
        binary_data = b'binary_start'
        json_data = b'{"a": 1}'
        test_data = binary_data + json_data
        test_file = io.BytesIO(test_data)
        
        # Read binary
        read_binary = test_file.read(len(binary_data))
        self.assertEqual(read_binary, binary_data)
        
        # Load JSON
        data = json_stream.load(test_file)
        self.assertEqual(dict(data.items()), {"a": 1})

    @skipUnless(HAS_RS_TOKENIZER, 'Rust tokenizer not available')
    def test_json_then_binary_then_json(self):
        json_1 = b'{"first": true}'
        binary_middle = b'middle_binary'
        json_2 = b'{"second": false}'
        test_data = json_1 + binary_middle + json_2
        test_file = io.BytesIO(test_data)
        
        # Load first JSON
        data1 = json_stream.load(test_file, correct_cursor=True)
        self.assertEqual(dict(data1.items()), {"first": True})
        data1.read_all()
        data1.tokenizer.park_cursor()
        self.assertEqual(test_file.tell(), len(json_1))
        
        # Read middle binary
        read_middle = test_file.read(len(binary_middle))
        self.assertEqual(read_middle, binary_middle)
        
        # Load second JSON
        data2 = json_stream.load(test_file)
        self.assertEqual(dict(data2.items()), {"second": False})

    @skipUnless(HAS_RS_TOKENIZER, 'Rust tokenizer not available')
    def test_load_many_then_binary(self):
        json_1 = '{"a": 1}'
        json_2 = '{"b": 2}'
        binary_data = b'binary'
        test_data = json_1.encode('utf-8') + json_2.encode('utf-8') + binary_data

        test_file = io.BytesIO(test_data)

        loader = json_stream.load_many(test_file, correct_cursor=True)

        # Read first JSON
        doc1 = next(loader)
        doc1.read_all()

        # Read second JSON
        doc2 = next(loader)
        doc2.read_all()

        # Now park cursor
        doc2.tokenizer.park_cursor()

        self.assertEqual(test_file.tell(), len(json_1) + len(json_2))
        self.assertEqual(test_file.read(), binary_data)
