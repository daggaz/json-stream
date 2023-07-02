"""
Taken from the NAYA project

https://github.com/danielyule/naya

Copyright (c) 2019 Daniel Yule
"""
import io
from typing import Optional, Tuple

from json_stream.tokenizer.strings import JsonStringReader


class TokenType:
    OPERATOR = 0
    STRING = 1
    NUMBER = 2
    BOOLEAN = 3
    NULL = 4


class State:
    WHITESPACE = 0
    INTEGER_0 = 1
    INTEGER_SIGN = 2
    INTEGER = 3
    INTEGER_EXP = 4
    INTEGER_EXP_0 = 5
    FLOATING_POINT_0 = 6
    FLOATING_POINT = 8
    STRING = 9
    STRING_END = 11
    TRUE_1 = 12
    TRUE_2 = 13
    TRUE_3 = 14
    FALSE_1 = 15
    FALSE_2 = 16
    FALSE_3 = 17
    FALSE_4 = 18
    NULL_1 = 19
    NULL_2 = 20
    NULL_3 = 21


class SpecialChar:
    # Kind of a hack but simple: if we used the empty string "" to represent
    # EOF, expressions like `char in "0123456789"` would be true for EOF, which
    # is confusing. If we used a non-string, they would result in TypeErrors.
    # By using the string "EOF", they work as expected. The only thing we have
    # to be careful about is to not ever use "EOF" in any such strings used for
    # char membership checking, which we have no reason to do anyway.
    EOF = "EOF"


def _guess_encoding(stream):
    # if it looks like a urllib response, get the charset from the headers (if any)
    try:
        encoding = stream.headers.get_content_charset()
    except:  # noqa
        encoding = None
    if encoding is None:
        # JSON is supposed to be UTF-8
        # https://tools.ietf.org/id/draft-ietf-json-rfc4627bis-09.html#:~:text=The%20default%20encoding%20is%20UTF,16%20and%20UTF%2D32).
        encoding = 'utf-8'
    return encoding


def _ensure_text(stream):
    data = stream.read(0)
    if isinstance(data, bytes):
        encoding = _guess_encoding(stream)
        return io.TextIOWrapper(stream, encoding=encoding)
    return stream


def tokenize(stream, *, buffering=-1, strings_as_files=False, **_):
    stream = _ensure_text(stream)

    def is_delimiter(char):
        return char.isspace() or char in "{}[]:," or char == SpecialChar.EOF

    token = []
    completed = False
    now_token: Optional[Tuple] = None

    def process_char(char):
        nonlocal completed, now_token, state, buffer, index
        advance = True
        add_char = False
        if state == State.WHITESPACE:
            if char == "{":
                completed = True
                now_token = (TokenType.OPERATOR, "{")
            elif char == "}":
                completed = True
                now_token = (TokenType.OPERATOR, "}")
            elif char == "[":
                completed = True
                now_token = (TokenType.OPERATOR, "[")
            elif char == "]":
                completed = True
                now_token = (TokenType.OPERATOR, "]")
            elif char == ",":
                completed = True
                now_token = (TokenType.OPERATOR, ",")
            elif char == ":":
                completed = True
                now_token = (TokenType.OPERATOR, ":")
            elif char == '"':
                state = State.STRING
                now_token = (TokenType.STRING, JsonStringReader(stream, buffer))
                if strings_as_files:
                    completed = True
                advance = False
            elif char in "123456789":
                state = State.INTEGER
                add_char = True
            elif char == "0":
                state = State.INTEGER_0
                add_char = True
            elif char == "-":
                state = State.INTEGER_SIGN
                add_char = True
            elif char == "f":
                state = State.FALSE_1
            elif char == "t":
                state = State.TRUE_1
            elif char == "n":
                state = State.NULL_1
            elif not char.isspace() and not char == SpecialChar.EOF:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.INTEGER:
            if char in "0123456789":
                add_char = True
            elif char == ".":
                state = State.FLOATING_POINT_0
                add_char = True
            elif char == "e" or char == 'E':
                state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NUMBER, int("".join(token)))
                advance = False
            else:
                raise ValueError("A number must contain only digits.  Got '{}'".format(char))
        elif state == State.INTEGER_0:
            if char == ".":
                state = State.FLOATING_POINT_0
                add_char = True
            elif char == "e" or char == 'E':
                state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NUMBER, 0)
                advance = False
            else:
                raise ValueError("A 0 must be followed by a '.' or a 'e'.  Got '{0}'".format(char))
        elif state == State.INTEGER_SIGN:
            if char == "0":
                state = State.INTEGER_0
                add_char = True
            elif char in "123456789":
                state = State.INTEGER
                add_char = True
            else:
                raise ValueError("A - must be followed by a digit.  Got '{0}'".format(char))
        elif state == State.INTEGER_EXP_0:
            if char == "+" or char == "-" or char in "0123456789":
                state = State.INTEGER_EXP
                add_char = True
            else:
                raise ValueError("An e in a number must be followed by a '+', '-' or digit.  Got '{0}'".format(char))
        elif state == State.INTEGER_EXP:
            if char in "0123456789":
                add_char = True
            elif is_delimiter(char):
                completed = True
                now_token = (TokenType.NUMBER, float("".join(token)))
                state = State.WHITESPACE
                advance = False
            else:
                raise ValueError("A number exponent must consist only of digits.  Got '{}'".format(char))
        elif state == State.FLOATING_POINT:
            if char in "0123456789":
                add_char = True
            elif char == "e" or char == "E":
                state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                completed = True
                now_token = (TokenType.NUMBER, float("".join(token)))
                state = State.WHITESPACE
                advance = False
            else:
                raise ValueError("A number must include only digits")
        elif state == State.FLOATING_POINT_0:
            if char in "0123456789":
                state = State.FLOATING_POINT
                add_char = True
            else:
                raise ValueError("A number with a decimal point must be followed by a fractional part")
        elif state == State.FALSE_1:
            if char == "a":
                state = State.FALSE_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_2:
            if char == "l":
                state = State.FALSE_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_3:
            if char == "s":
                state = State.FALSE_4
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_4:
            if char == "e":
                state = State.WHITESPACE
                completed = True
                now_token = (TokenType.BOOLEAN, False)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_1:
            if char == "r":
                state = State.TRUE_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_2:
            if char == "u":
                state = State.TRUE_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_3:
            if char == "e":
                state = State.WHITESPACE
                completed = True
                now_token = (TokenType.BOOLEAN, True)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_1:
            if char == "u":
                state = State.NULL_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_2:
            if char == "l":
                state = State.NULL_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_3:
            if char == "l":
                state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NULL, None)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.STRING:
            reader: JsonStringReader = now_token[1]
            try:
                s = reader.read()
            finally:
                index += reader.index
            if not strings_as_files:
                now_token = (TokenType.STRING, s)
                completed = True
            buffer = reader.buffer
            state = State.STRING_END
        elif state == State.STRING_END:
            if is_delimiter(char):
                advance = False
                state = State.WHITESPACE
            else:
                raise ValueError("Expected whitespace or an operator after string.  Got '{}'".format(char))

        if add_char:
            token.append(char)

        return advance

    state = State.WHITESPACE
    if not buffering:
        buffering = 1
    elif buffering <= 0:
        buffering = io.DEFAULT_BUFFER_SIZE
    buffering = buffering.__index__()
    buffer = stream.read(buffering)
    c = None
    index = -1
    advance = True
    while buffer:
        if advance:
            c, buffer = buffer[0], buffer[1:] or stream.read(buffering)
            index += 1
        try:
            advance = process_char(c)
        except ValueError as e:
            raise ValueError("".join([e.args[0], " at index {}".format(index)]))
        if completed:
            completed = False
            token = []
            yield now_token

    process_char(SpecialChar.EOF)
    if completed:
        yield now_token
