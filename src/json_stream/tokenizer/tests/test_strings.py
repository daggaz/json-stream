import re
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from json_stream.tokenizer.strings import JsonStringReader


class TestJsonStringReader(TestCase):
    def test_string_parsing(self):
        self.assertStringEquals("word", r'"word"')
        self.assertStringEquals("this char at end: Ȃ", r'"this char at end: \u0202"')
        self.assertStringEquals("this char in middle: Ȃ.", r'"this char in middle: \u0202."')

    def test_empty_string(self):
        self.assertStringEquals("", r'""')

    def test_escaping(self):
        self.assertStringEquals("with\tescape", r'"with\tescape"')
        self.assertStringEquals("with\n a different escape", r'"with\n a different escape"')
        self.assertStringEquals("using a \bbackspace", r'"using a \bbackspace"')
        self.assertStringEquals("now we have \f a formfeed", r'"now we have \f a formfeed"')
        self.assertStringEquals('"a quote"', r'"\"a quote\""')
        self.assertStringEquals("/", r'"\/"')

    def test_unicode_literal(self):
        self.assertStringEquals('Ä', r'"\u00c4"')
        self.assertStringEquals("꽸", r'"\uaf78"')
        self.assertStringEquals("訋", r'"\u8A0b"')
        self.assertStringEquals("돧", r'"\uB3e7"')
        self.assertStringEquals("ዯ", r'"\u12eF"')

    def test_invalid_string_escape(self):
        self.assertStringRaises(r'"\h"', "Invalid string escape: h")
        self.assertStringRaises(r'"\2"', "Invalid string escape: 2")
        self.assertStringRaises(r'"\!"', "Invalid string escape: !")

    def test_unicode_literal_truncated(self):
        self.assertStringRaises(r'"\u00c"', re.escape(r'Invalid unicode literal: \u00c"'))

    def test_unicode_literal_bad_hex(self):
        self.assertStringRaises(r'"\u00x4"', re.escape(r"Invalid unicode literal: \u00x4"))

    def test_unicode_surrogate_pair_literal(self):
        self.assertStringEquals('𝄞', r'"\ud834\udd1e"')

    def test_unicode_surrogate_pair_unpaired(self):
        self.assertStringRaises(r'"\ud834"', "Unpaired UTF-16 surrogate")
        self.assertStringRaises(r'"\ud834', "Unterminated string at end of file")
        self.assertStringRaises(r'"\ud834\x', "Unpaired UTF-16 surrogate")
        self.assertStringRaises(r'"\ud834' + '\\', "Unterminated string at end of file")

    def test_unicode_surrogate_pair_non_surrogate(self):
        self.assertStringRaises(r'"\ud834\u00c4"', "Second half of UTF-16 surrogate pair is not a surrogate!")

    def test_unicode_surrogate_pair_literal_truncated(self):
        self.assertStringRaises(r'"\ud834\u00c"', re.escape(r'Invalid unicode literal: \u00c"'))

    def test_unicode_surrogate_pair_literal_bad_hex(self):
        self.assertStringRaises(r'"\ud834\u00x4"', re.escape(r"Invalid unicode literal: \u00x4"))

    def test_unicode_surrogate_pair_literal_invalid(self):
        message = re.escape(r"Error decoding UTF-16 surrogate pair \ud834\ud834")
        self.assertStringRaises(r'"\ud834\ud834"', message)

    def test_unicode_surrogate_pair_literal_unterminated(self):
        self.assertStringRaises(r'"\ud834\ud83', r"Unterminated string at end of file")

    def test_unterminated_strings(self):
        self.assertStringRaises('"unterminated', "Unterminated string at end of file")

    def test_unterminated_strings_while_in_escape(self):
        self.assertStringRaises(r'"\"', "Unterminated string at end of file")
        self.assertStringRaises(r'"\u"', "Unterminated string at end of file")
        self.assertStringRaises(r'"\u!"', "Unterminated string at end of file")
        self.assertStringRaises(r'"\u!!"', "Unterminated string at end of file")
        self.assertStringRaises(r'"\u!!!', "Unterminated string at end of file")

    def test_with_initial_buffer(self):
        self.assertStringEquals("there will be more string", buffer='"there will be ', stream='more string"')  # x   x x

    def test_remainder(self):
        reader, f = self.assertStringEquals(
            "after the string",
            stream='"after the string"there is more stuff',
            remaining_buffer='there is more stuff',
        )
        self.assertRead(reader, f, '', remaining_buffer='there is more stuff')

    def test_remainder_read_past_end_of_string(self):
        reader, f = self.assertStringEquals(
            "after the string",
            stream='"after the string"there is more stuff',
            remaining_buffer='the', remaining_stream='re is more stuff', amount=20
        )
        self.assertRead(reader, f, '', remaining_buffer='the', remaining_stream='re is more stuff', amount=20)

    def test_remainder_when_string_ends_after_initial_buffer(self):
        reader, f = self.assertStringEquals(
            "after the string",
            buffer='"after the', stream=' string"there is more stuff',
            remaining_buffer='there is more stuff',
        )
        self.assertRead(reader, f, '', remaining_buffer='there is more stuff')

    def test_remainder_when_string_ends_within_initial_buffer(self):
        reader, f = self.assertStringEquals(
            "after the string",
            buffer='"after the string"there', stream=' is more stuff',
            remaining_buffer='there', remaining_stream=' is more stuff',
        )
        self.assertRead(reader, f, '', remaining_buffer='there', remaining_stream=' is more stuff')

    def test_read_part_shorter_initial_buffer(self):
        reader, f = self.assertStringEquals(
            "there",
            buffer='"there will be ', stream='more string"',
            remaining_buffer=' will be ', remaining_stream='more string"', amount=5, complete=False,
        )
        self.assertRead(reader, f, ' will be more string')

    def test_read_part_longer_than_initial_buffer(self):
        reader, f = self.assertStringEquals(
            "there will be ",
            buffer='"there will be ', stream='more string"',
            remaining_buffer='', remaining_stream='more string"', amount=20, complete=False,
        )
        self.assertRead(reader, f, 'more string')

    def test_read_over_split_escape(self):
        json = r'"abcde\u00c4edcba"'
        for i in range(len(json)):
            buffer, stream = json[:i], json[i:]
            self.assertStringEquals("abcdeÄedcba", buffer=buffer, stream=stream)

    def test_readable(self):
        reader = JsonStringReader(StringIO())
        self.assertTrue(reader.readable())

    def test_readline(self):
        stream = StringIO(r'some\nlines\nof\ntext"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='some\n',
            remaining_readline_buffer='lines\nof\ntext',
            complete=False,
        )
        self.assertReadline(
            reader, stream,
            result='lines\n',
            remaining_readline_buffer='of\ntext',
            complete=False,
        )
        self.assertReadline(
            reader, stream,
            result='of\n',
            remaining_readline_buffer='text',
            complete=False,
        )
        self.assertReadline(
            reader, stream,
            result='text',
        )

    @patch('json_stream.tokenizer.strings.DEFAULT_BUFFER_SIZE', 10)
    def test_readline_needs_multiple_reads(self):
        stream = StringIO(r'aaaaaaaaaabbbbb\ncccdddddddd"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='aaaaaaaaaabbbbb\n',
            remaining_readline_buffer='ccc',
            remaining_stream='dddddddd"',
            complete=False,
        )
        self.assertReadline(reader, stream, 'cccdddddddd')

    def test_readline_eof_without_newline(self):
        stream = StringIO(r'aaaaaaaaaabbbbbcccdddddddd"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='aaaaaaaaaabbbbbcccdddddddd',
        )
        self.assertReadline(reader, stream, '')

    @patch('json_stream.tokenizer.strings.DEFAULT_BUFFER_SIZE', 10)
    def test_readline_then_read(self):
        stream = StringIO(r'aaaaaaaaaabbbbbbbb\ndddddddd"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='aaaaaaaaaabbbbbbbb\n',
            remaining_stream='dddddddd"',
            complete=False,
        )
        self.assertRead(reader, stream, result='dddddddd')

    @patch('json_stream.tokenizer.strings.DEFAULT_BUFFER_SIZE', 10)
    def test_readline_then_read_with_data_in_buffer(self):
        stream = StringIO(r'aaaaaaaaaabbbbb\ncccdddddddd"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='aaaaaaaaaabbbbb\n',
            remaining_readline_buffer='ccc',
            remaining_stream='dddddddd"',
            complete=False,
        )
        self.assertRead(reader, stream, result='cccdddddddd')

    def test_read_then_readline(self):
        stream = StringIO(r'aaaaaaaaaabbbbb\ncccdddddddd"')
        reader = JsonStringReader(stream)
        self.assertRead(
            reader, stream,
            result='aaaaaaaaaa',
            remaining_stream=r'bbbbb\ncccdddddddd"',
            amount=10,
            complete=False,
        )
        self.assertReadline(
            reader, stream,
            result='bbbbb\n',
            remaining_readline_buffer='cccdddddddd',
            complete=False,
        )
        self.assertReadline(
            reader, stream,
            result='cccdddddddd',
        )

    def test_readline_with_size_shorter_than_line(self):
        stream = StringIO(r'aaaaaaaaaabbbbb\ncccdddddddd"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='aaaaaaaaaa',
            remaining_stream=r'bbbbb\ncccdddddddd"',
            amount=10,
            complete=False,
        )
        self.assertReadline(
            reader, stream,
            result='bbbbb\n',
            remaining_readline_buffer='cccdddddddd',
            complete=False,
        )
        self.assertReadline(
            reader, stream,
            result='cccdddddddd',
        )

    def test_readline_with_size_longer_than_line(self):
        stream = StringIO(r'aaaaaaaaaabbbbb\ncccdddddddd"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='aaaaaaaaaabbbbb\n',
            remaining_readline_buffer='ccc',
            remaining_stream='dddddddd"',
            amount=20,
            complete=False,
        )
        self.assertReadline(reader, stream, 'cccdddddddd')

    def test_readline_trailing_newline(self):
        stream = StringIO(r'a\n"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='a\n',
        )

    def test_readline_no_trailing_newline(self):
        stream = StringIO(r'a\nb"')
        reader = JsonStringReader(stream)
        self.assertReadline(
            reader, stream,
            result='a\n',
            remaining_readline_buffer='b',
            complete=False
        )
        self.assertReadline(reader, stream, 'b')

    def test_readlines(self):
        stream = StringIO(r'some\nlines\nof\ntext"')
        reader = JsonStringReader(stream)
        self.assertListEqual(["some\n", "lines\n", "of\n", "text"], reader.readlines())
        self.assertEqual('', reader.readline_buffer)
        self.assertEqual('', reader.buffer)
        self.assertEqual('', stream.read())
        self.assertTrue(reader.complete)

    def assertStringEquals(self, result, stream, buffer='', remaining_buffer='', remaining_stream='', amount=None,
                           complete=True):
        if buffer:
            buffer = buffer[1:]
        else:
            stream = stream[1:]
        f = StringIO(stream)
        reader = JsonStringReader(f, buffer)
        self.assertRead(reader, f, result, remaining_buffer, remaining_stream, amount, complete)
        return reader, f

    def assertRead(self, reader, stream, result, remaining_buffer='', remaining_stream='', amount=None, complete=True):
        self.assertEqual(result, reader.read(amount))
        self.assertEqual(reader.readline_buffer, '')
        self.assertEqual(remaining_buffer, reader.buffer)
        pos = stream.tell()
        self.assertEqual(remaining_stream, stream.read())
        stream.seek(pos)
        self.assertEqual(complete, reader.complete)

    def assertReadline(self, reader, stream, result, remaining_readline_buffer='', remaining_buffer='',
                       remaining_stream='', amount=None, complete=True):
        self.assertEqual(result, reader.readline(amount))
        self.assertEqual(remaining_readline_buffer, reader.readline_buffer)
        self.assertEqual(remaining_buffer, reader.buffer)
        pos = stream.tell()
        self.assertEqual(remaining_stream, stream.read())
        stream.seek(pos)
        self.assertEqual(complete, reader.complete)

    def assertStringRaises(self, s, error):
        stream = StringIO(s[1:])
        f = JsonStringReader(stream)
        with self.assertRaisesRegex(ValueError, error):
            f.read()
