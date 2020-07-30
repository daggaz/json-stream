"""
Taken from the NAYA project

https://github.com/danielyule/naya

Copyright (c) 2019 Daniel Yule
"""
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

    def assertStringEquals(self, expected, actual):
        token_list = [token for token in tokenize(StringIO('"{}"'.format(actual)))]
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
        self.assertStringEquals("word", "word")
        self.assertStringEquals("with\tescape", "with\\tescape")
        self.assertStringEquals("with\n a different escape", "with\\n a different escape")
        self.assertStringEquals("using a \bbackspace", "using a \\bbackspace")
        self.assertStringEquals("now we have \f a formfeed", "now we have \\f a formfeed")
        self.assertStringEquals("\"a quote\"", "\\\"a quote\\\"")
        self.assertStringEquals("", "")
        self.assertStringEquals("/", "\\/")
        self.assertStringEquals("this char: \u0202", "this char: \\u0202")
        self.assertStringEquals("\uaf78", "\\uaf78")
        self.assertStringEquals("\u8A0b", "\\u8A0b")
        self.assertStringEquals("\ub3e7", "\\uB3e7")
        self.assertStringEquals("\u12ef", "\\u12eF")
        self.assertRaises(ValueError, self.tokenize_sequence, "\"\\uay76\"")
        self.assertRaises(ValueError, self.tokenize_sequence, "\"\\h\"")
        self.assertRaises(ValueError, self.tokenize_sequence, "\"\\2\"")
        self.assertRaises(ValueError, self.tokenize_sequence, "\"\\!\"")
        self.assertRaises(ValueError, self.tokenize_sequence, "\"\\u!\"")

    def test_sequence(self):
        result = [token for token in tokenize(StringIO("123 \"abc\":{}"))]
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
        result = [token for token in tokenize(StringIO(big_file))]
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
        result = [token for token in tokenize(StringIO(big_file_no_space))]
        self.assertListEqual(result, expected)
        result = [token for token in tokenize(StringIO("854.6,123"))]
        self.assertEqual(result, [(2, 854.6), (0, ','), (2, 123)])
        self.assertRaises(ValueError, self.tokenize_sequence, "123\"text\"")
        self.assertRaises(ValueError, self.tokenize_sequence, "23.9e10true")
        self.assertRaises(ValueError, self.tokenize_sequence, "\"test\"56")
