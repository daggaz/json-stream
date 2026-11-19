import io
from unittest import TestCase

from json_stream.iterators import IterableStream
from json_stream.tokenizer import tokenize, TokenType, Tokenizer, SpecialChar

DOC = '{"key": "valué 😀", "list": [1, -25, 3.125e+10, true, null], "esc": "a\\"b\\\\c\\u00e9"}  [42] "x"'
EXPECTED = [
    (TokenType.OPERATOR, "{"),
    (TokenType.STRING, "key"),
    (TokenType.OPERATOR, ":"),
    (TokenType.STRING, "valué 😀"),
    (TokenType.OPERATOR, ","),
    (TokenType.STRING, "list"),
    (TokenType.OPERATOR, ":"),
    (TokenType.OPERATOR, "["),
    (TokenType.NUMBER, 1),
    (TokenType.OPERATOR, ","),
    (TokenType.NUMBER, -25),
    (TokenType.OPERATOR, ","),
    (TokenType.NUMBER, 3.125e+10),
    (TokenType.OPERATOR, ","),
    (TokenType.BOOLEAN, True),
    (TokenType.OPERATOR, ","),
    (TokenType.NULL, None),
    (TokenType.OPERATOR, "]"),
    (TokenType.OPERATOR, ","),
    (TokenType.STRING, "esc"),
    (TokenType.OPERATOR, ":"),
    (TokenType.STRING, 'a"b\\cé'),
    (TokenType.OPERATOR, "}"),
    (TokenType.OPERATOR, "["),
    (TokenType.NUMBER, 42),
    (TokenType.OPERATOR, "]"),
    (TokenType.STRING, "x"),
]


def one_byte_chunks(data):
    # splits multi-byte UTF-8 characters across chunks
    return IterableStream(data[i:i + 1] for i in range(len(data)))


class TestTokenizerBuffering(TestCase):
    def test_buffer_sizes(self):
        streams = {
            "text": lambda: io.StringIO(DOC),
            "binary": lambda: io.BytesIO(DOC.encode()),
            "one byte chunks": lambda: one_byte_chunks(DOC.encode()),
        }
        for name, make_stream in streams.items():
            for buffering in (-1, 0, 1, 2, 3, 7, 4096):
                with self.subTest(stream=name, buffering=buffering):
                    self.assertListEqual(EXPECTED, list(tokenize(make_stream(), buffering=buffering)))

    def test_process_char_alone(self):
        # __next__ skips runs of plain characters, but process_char() must still handle
        # every character by itself for other drivers (e.g. async) that feed it directly
        tokenizer = Tokenizer(None)
        tokens = []
        for char in DOC:
            advance = False
            while not advance:
                advance, token = tokenizer.process_char(char)
                if token:
                    tokens.append(token)
                    tokenizer.token_buffer = []
        _, token = tokenizer.process_char(SpecialChar.EOF)
        self.assertIsNone(token)
        self.assertListEqual(EXPECTED, tokens)

    def test_read_sizes(self):
        class Recorder:
            def __init__(self, stream, seekable):
                self.stream, self.is_seekable, self.sizes = stream, seekable, []

            def seekable(self):
                return self.is_seekable

            def read(self, size=-1):
                if size:
                    self.sizes.append(size)
                return self.stream.read(size)

        cases = [
            # (stream, seekable, buffering, expected read size)
            (lambda: io.StringIO(DOC), True, -1, io.DEFAULT_BUFFER_SIZE),
            (lambda: io.StringIO(DOC), False, -1, 1),  # e.g. a pipe: don't wait for 8k chars
            (lambda: io.StringIO(DOC), False, 16, 16),
            (lambda: io.BytesIO(DOC.encode()), False, -1, io.DEFAULT_BUFFER_SIZE),
            (lambda: io.BytesIO(DOC.encode()), True, 0, 1),
        ]
        for make_stream, seekable, buffering, expected in cases:
            with self.subTest(seekable=seekable, buffering=buffering, expected=expected):
                stream = Recorder(make_stream(), seekable)
                self.assertListEqual(EXPECTED, list(tokenize(stream, buffering=buffering)))
                self.assertEqual({expected}, set(stream.sizes))

    def test_unknown_kwargs_ignored(self):
        # options meant for the rust tokenizer must not break the python one
        self.assertListEqual(EXPECTED, list(tokenize(io.StringIO(DOC), not_a_python_option=True)))

    def test_raw_newlines_kept(self):
        # no newline translation for binary streams, same as for text streams and the rust tokenizer
        self.assertListEqual([(TokenType.STRING, "a\r\nb")], list(tokenize(io.BytesIO(b'"a\r\nb"'))))

    def test_truncated_utf8(self):
        with self.assertRaises(UnicodeDecodeError):
            list(tokenize(io.BytesIO('"é"'.encode()[:-2])))

    def test_invalid_utf8_raised_when_reached(self):
        # bytes read ahead are only decoded as far as they are valid; the error is raised
        # when the tokenizer actually gets to the bad byte
        tokenizer = tokenize(io.BytesIO(b'[1, \xff]'))
        self.assertEqual([(TokenType.OPERATOR, "["), (TokenType.NUMBER, 1), (TokenType.OPERATOR, ",")],
                         [next(tokenizer) for _ in range(3)])
        with self.assertRaises(UnicodeDecodeError):
            next(tokenizer)

    def test_error_index(self):
        with self.assertRaisesRegex(ValueError, "at index 9"):
            list(tokenize(io.StringIO('["abc",  x]'), buffering=4))

    def _tokenize_first_doc(self, stream, **kwargs):
        tokenizer = tokenize(stream, **kwargs)
        tokens = [next(tokenizer) for _ in range(23)]  # up to the end of the first object
        self.assertEqual(EXPECTED[:23], tokens)
        return tokenizer

    def test_remainder(self):
        rest = '  [42] "x"'
        for buffering in (-1, 2, 7):
            with self.subTest(buffering=buffering):
                tokenizer = self._tokenize_first_doc(io.StringIO(DOC), buffering=buffering)
                self.assertTrue(rest.startswith(tokenizer.remainder))
                tokenizer = self._tokenize_first_doc(io.BytesIO(DOC.encode()), buffering=buffering)
                self.assertTrue(rest.encode().startswith(tokenizer.remainder))

    def test_remainder_partial_character(self):
        tokenizer = tokenize(io.BytesIO('"x" "é"'.encode()), buffering=6)
        self.assertEqual((TokenType.STRING, "x"), next(tokenizer))
        # the first 6 bytes end half way through the é
        self.assertEqual(' "\xc3'.encode("latin-1"), tokenizer.remainder)

    def test_park_cursor(self):
        rest = '  [42] "x"'
        streams = {
            "text": (lambda: io.StringIO(DOC), rest),
            "binary": (lambda: io.BytesIO(DOC.encode()), rest.encode()),
        }
        for name, (make_stream, expected) in streams.items():
            for buffering in (-1, 2, 7):
                with self.subTest(stream=name, buffering=buffering):
                    stream = make_stream()
                    tokenizer = self._tokenize_first_doc(stream, buffering=buffering, correct_cursor=True)
                    tokenizer.park_cursor()
                    self.assertEqual(expected, stream.read())

    def test_park_cursor_continue(self):
        stream = io.StringIO(DOC)
        tokenizer = self._tokenize_first_doc(stream, buffering=3, correct_cursor=True)
        tokenizer.park_cursor()
        self.assertListEqual(EXPECTED[23:], list(tokenizer))

    def test_park_cursor_needs_correct_cursor(self):
        # as with the rust tokenizer, park_cursor() does nothing without correct_cursor=True
        stream = io.StringIO(DOC)
        tokenizer = self._tokenize_first_doc(stream)
        tokenizer.park_cursor()
        self.assertEqual("", stream.read())

    def test_park_cursor_unseekable(self):
        # unseekable streams are read one character at a time with correct_cursor=True
        stream = IterableStream([DOC.encode()])
        tokenizer = self._tokenize_first_doc(stream, correct_cursor=True)
        tokenizer.park_cursor()
        self.assertEqual(b'  [42] "x"', stream.read())

    def test_park_cursor_after_number(self):
        # the delimiter that ended the number has been read, as with the rust tokenizer
        stream = io.StringIO("5 [2]")
        tokenizer = tokenize(stream, correct_cursor=True)
        self.assertEqual((TokenType.NUMBER, 5), next(tokenizer))
        tokenizer.park_cursor()
        self.assertEqual("[2]", stream.read())

    def test_park_cursor_before_reading(self):
        stream = io.StringIO("[1]")
        tokenizer = tokenize(stream, correct_cursor=True)
        tokenizer.park_cursor()
        self.assertEqual("", tokenizer.remainder)
        self.assertEqual("[1]", stream.read())

    def test_stream_without_seekable(self):
        class ReadOnly:
            def __init__(self, data):
                self.stream = io.StringIO(data)

            def read(self, size=-1):
                return self.stream.read(size)

        tokenizer = tokenize(ReadOnly(DOC), correct_cursor=True)
        self.assertListEqual(EXPECTED, list(tokenizer))
