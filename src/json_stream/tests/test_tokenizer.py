"""
Taken from the NAYA project

https://github.com/danielyule/naya

Copyright (c) 2019 Daniel Yule
"""
import re
from io import StringIO
from unittest import TestCase

from json_stream.tokenizer import tokenize, TokenType


class TestJsonTokenization(TestCase):
    def tokenize_sequence(self, string):
        return [token for token in tokenize(StringIO(string))]

    def assertNumberEquals(self, expected, actual):
        token_list = self.tokenize_sequence(actual)
        self.assertEqual(1, len(token_list))
        ttype, token = token_list[0]
        self.assertEqual(expected, token)
        self.assertEqual(ttype, TokenType.NUMBER)

    def assertOperatorEquals(self, expected, actual):

        token_list = self.tokenize_sequence(actual)
        ttype, token = token_list[0]
        self.assertEqual(expected, token)
        self.assertEqual(ttype, TokenType.OPERATOR)

    def assertStringEquals(self, *, expected, json_input):
        token_list = self.tokenize_sequence(json_input)
        self.assertEqual(1, len(token_list))
        ttype, token = token_list[0]
        self.assertEqual(expected, token)
        self.assertEqual(ttype, TokenType.STRING)

    def test_number_parsing(self):
        self.assertNumberEquals(0, "0")
        self.assertNumberEquals(0.5, "0.5")
        self.assertNumberEquals(0, "-0")
        self.assertNumberEquals(12, "12")
        self.assertNumberEquals(3.5, "3.5")
        self.assertNumberEquals(1.2e11, "12e10")
        self.assertNumberEquals(7.8e-14, "78E-15")
        self.assertNumberEquals(0, "0e10")
        self.assertNumberEquals(65.7, "65.7")
        self.assertNumberEquals(892.978, "892.978")
        self.assertNumberEquals(8.9e7, "8.9E7")
        self.assertRaises(ValueError, self.tokenize_sequence, "01")
        self.assertRaises(ValueError, self.tokenize_sequence, "1.")
        self.assertRaises(ValueError, self.tokenize_sequence, "-01")
        self.assertRaises(ValueError, self.tokenize_sequence, "2a")
        self.assertRaises(ValueError, self.tokenize_sequence, "-a")
        self.assertRaises(ValueError, self.tokenize_sequence, "3.b")
        self.assertRaises(ValueError, self.tokenize_sequence, "3.e10")
        self.assertRaises(ValueError, self.tokenize_sequence, "3.6ea")
        self.assertRaises(ValueError, self.tokenize_sequence, "67.8e+a")

    def test_operator_parsing(self):
        self.assertOperatorEquals("{", "{")
        self.assertOperatorEquals("}", "}")
        self.assertOperatorEquals("[", "[")
        self.assertOperatorEquals("]", "]")
        self.assertOperatorEquals(":", ":")
        self.assertOperatorEquals(",", ",")

    def test_string_parsing(self):
        self.assertStringEquals(expected="word", json_input=r'"word"')
        self.assertStringEquals(expected="with\tescape", json_input=r'"with\tescape"')
        self.assertStringEquals(expected="with\n a different escape", json_input=r'"with\n a different escape"')
        self.assertStringEquals(expected="using a \bbackspace", json_input=r'"using a \bbackspace"')
        self.assertStringEquals(expected="now we have \f a formfeed", json_input=r'"now we have \f a formfeed"')
        self.assertStringEquals(expected="\"a quote\"", json_input=r'"\"a quote\""')
        self.assertStringEquals(expected="", json_input=r'""')
        self.assertStringEquals(expected="/", json_input=r'"\/"')
        self.assertStringEquals(expected="this char at end: Ȃ", json_input=r'"this char at end: \u0202"')
        self.assertStringEquals(expected="this char in middle: Ȃ.", json_input=r'"this char in middle: \u0202."')
        self.assertStringEquals(expected="꽸", json_input=r'"\uaf78"')
        self.assertStringEquals(expected="訋", json_input=r'"\u8A0b"')
        self.assertStringEquals(expected="돧", json_input=r'"\uB3e7"')
        self.assertStringEquals(expected="ዯ", json_input=r'"\u12eF"')
        with self.assertRaisesRegex(ValueError, re.escape(r"Invalid unicode literal: \uay76 at index 6")):
            self.tokenize_sequence(r'"\uay76"')
        with self.assertRaisesRegex(ValueError, "Invalid string escape: h at index 2"):
            self.tokenize_sequence(r'"\h"')
        with self.assertRaisesRegex(ValueError, "Invalid string escape: 2 at index 2"):
            self.tokenize_sequence(r'"\2"')
        with self.assertRaisesRegex(ValueError, "Invalid string escape: ! at index 2"):
            self.tokenize_sequence(r'"\!"')
        with self.assertRaisesRegex(ValueError, "Unterminated unicode literal at end of file"):
            self.tokenize_sequence(r'"\u!"')

    def test_unterminated_strings(self):
        with self.assertRaisesRegex(ValueError, "Unterminated string at end of file"):
            self.tokenize_sequence('"unterminated')

    def test_sequence(self):
        result = self.tokenize_sequence("123 \"abc\":{}")
        self.assertEqual(result, [(2, 123), (1, 'abc'), (0, ':'), (0, '{'), (0, '}')])

        # Borrowed from http://en.wikipedia.org/wiki/JSON
        big_file = """{
          "firstName": "John",
          "lastName": "Smith",
          "isAlive": true,
          "isDead": false,
          "age": 25,
          "height_cm": 167.6,
          "address": {
            "streetAddress": "21 2nd Street",
            "city": "New York",
            "state": "NY",
            "postalCode": "10021-3100"
          },
          "phoneNumbers": [
            {
              "type": "home",
              "number": "212 555-1234"
            },
            {
              "type": "office",
              "number": "646 555-4567"
            }
          ],
          "children": [],
          "spouse": null
        }"""
        result = self.tokenize_sequence(big_file)
        expected = [(0, '{'), (1, 'firstName'), (0, ':'), (1, 'John'), (0, ','), (1, 'lastName'), (0, ':'),
                    (1, 'Smith'), (0, ','), (1, 'isAlive'), (0, ':'), (3, True), (0, ','), (1, 'isDead'), (0, ':'),
                    (3, False), (0, ','), (1, 'age'), (0, ':'),
                    (2, 25), (0, ','), (1, 'height_cm'), (0, ':'), (2, 167.6), (0, ','), (1, 'address'), (0, ':'),
                    (0, '{'), (1, 'streetAddress'), (0, ':'), (1, '21 2nd Street'), (0, ','), (1, 'city'), (0, ':'),
                    (1, 'New York'), (0, ','), (1, 'state'), (0, ':'), (1, 'NY'), (0, ','), (1, 'postalCode'),
                    (0, ':'), (1, '10021-3100'), (0, '}'), (0, ','), (1, 'phoneNumbers'), (0, ':'), (0, '['), (0, '{'),
                    (1, 'type'), (0, ':'), (1, 'home'), (0, ','), (1, 'number'), (0, ':'), (1, '212 555-1234'),
                    (0, '}'), (0, ','), (0, '{'), (1, 'type'), (0, ':'), (1, 'office'), (0, ','), (1, 'number'),
                    (0, ':'), (1, '646 555-4567'), (0, '}'), (0, ']'), (0, ','), (1, 'children'), (0, ':'), (0, '['),
                    (0, ']'), (0, ','), (1, 'spouse'), (0, ':'), (4, None), (0, '}')]
        self.assertListEqual(result, expected)
        big_file_no_space = '{"firstName":"John","lastName":"Smith","isAlive":true,"isDead":false,"age":25,"height_cm' \
                            '":167.6,"address":{"streetAddress":"21 2nd Street","city":"New York","state":"NY","posta' \
                            'lCode":"10021-3100"},"phoneNumbers":[{"type":"home","number":"212 555-1234"},{"type":"of' \
                            'fice","number":"646 555-4567"}],"children":[],"spouse":null}'
        result = self.tokenize_sequence(big_file_no_space)
        self.assertListEqual(result, expected)
        result = self.tokenize_sequence("854.6,123")
        self.assertEqual(result, [(2, 854.6), (0, ','), (2, 123)])
        self.assertRaises(ValueError, self.tokenize_sequence, "123\"text\"")
        self.assertRaises(ValueError, self.tokenize_sequence, "23.9e10true")
        self.assertRaises(ValueError, self.tokenize_sequence, "\"test\"56")

    def test_unicode_literal(self):
        result = list(tokenize(StringIO(r'"\u00c4"')))
        self.assertListEqual(result, [(1, 'Ä')])

    def test_unicode_literal_truncated(self):
        with self.assertRaisesRegex(ValueError, re.escape(r'Invalid unicode literal: \u00c" at index 6')):
            list(tokenize(StringIO(r'"\u00c"')))

    def test_unicode_literal_bad_hex(self):
        with self.assertRaisesRegex(ValueError, re.escape(r"Invalid unicode literal: \u00x4 at index 6")):
            list(tokenize(StringIO(r'"\u00x4"')))

    def test_unicode_surrogate_pair_literal(self):
        result = list(tokenize(StringIO(r'"\ud834\udd1e"')))
        self.assertListEqual(result, [(1, '𝄞')])

    def test_unicode_surrogate_pair_unpaired(self):
        with self.assertRaisesRegex(ValueError, "Unpaired UTF-16 surrogate at index 7"):
            list(tokenize(StringIO(r'"\ud834"')))
        with self.assertRaisesRegex(ValueError, "Unpaired UTF-16 surrogate at end of file"):
            list(tokenize(StringIO(r'"\ud834')))
        with self.assertRaisesRegex(ValueError, "Unpaired UTF-16 surrogate at index 8"):
            list(tokenize(StringIO(r'"\ud834\x')))
        with self.assertRaisesRegex(ValueError, "Unpaired UTF-16 surrogate at end of file"):
            list(tokenize(StringIO(r'"\ud834' + '\\')))

    def test_unicode_surrogate_pair_non_surrogate(self):
        with self.assertRaisesRegex(ValueError, "Second half of UTF-16 surrogate pair is not a surrogate! at index 12"):
            list(tokenize(StringIO(r'"\ud834\u00c4"')))

    def test_unicode_surrogate_pair_literal_truncated(self):
        with self.assertRaisesRegex(ValueError, re.escape(r'Invalid unicode literal: \u00c" at index 12')):
            list(tokenize(StringIO(r'"\ud834\u00c"')))

    def test_unicode_surrogate_pair_literal_bad_hex(self):
        with self.assertRaisesRegex(ValueError, re.escape(r"Invalid unicode literal: \u00x4 at index 12")):
            list(tokenize(StringIO(r'"\ud834\u00x4"')))

    def test_unicode_surrogate_pair_literal_invalid(self):
        message = re.escape(r"Error decoding UTF-16 surrogate pair \ud834\ud834 at index 12")
        with self.assertRaisesRegex(ValueError, message):
            list(tokenize(StringIO(r'"\ud834\ud834"')))

    def test_unicode_surrogate_pair_literal_unterminated(self):
        with self.assertRaisesRegex(ValueError, r"Unterminated unicode literal at end of file"):
            list(tokenize(StringIO(r'"\ud834\ud83')))
