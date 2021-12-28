"""
Taken from the NAYA project

https://github.com/danielyule/naya

Copyright (c) 2019 Daniel Yule
"""
import io


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
    STRING_ESCAPE = 10
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
    UNICODE_1 = 22
    UNICODE_2 = 23
    UNICODE_3 = 24
    UNICODE_4 = 25


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


def tokenize(stream):
    stream = _ensure_text(stream)

    def is_delimiter(char):
        return char.isspace() or char in "{}[]:,"

    token = []
    charcode = 0
    completed = False
    now_token = ""

    def process_char(char, charcode):
        nonlocal token, completed, now_token
        advance = True
        add_char = False
        next_state = state
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
            elif char == "\"":
                next_state = State.STRING
            elif char in "123456789":
                next_state = State.INTEGER
                add_char = True
            elif char == "0":
                next_state = State.INTEGER_0
                add_char = True
            elif char == "-":
                next_state = State.INTEGER_SIGN
                add_char = True
            elif char == "f":
                next_state = State.FALSE_1
            elif char == "t":
                next_state = State.TRUE_1
            elif char == "n":
                next_state = State.NULL_1
            elif not char.isspace():
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.INTEGER:
            if char in "0123456789":
                add_char = True
            elif char == ".":
                next_state = State.FLOATING_POINT_0
                add_char = True
            elif char == "e" or char == 'E':
                next_state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NUMBER, int("".join(token)))
                advance = False
            else:
                raise ValueError("A number must contain only digits.  Got '{}'".format(char))
        elif state == State.INTEGER_0:
            if char == ".":
                next_state = State.FLOATING_POINT_0
                add_char = True
            elif char == "e" or char == 'E':
                next_state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NUMBER, 0)
                advance = False
            else:
                raise ValueError("A 0 must be followed by a '.' or a 'e'.  Got '{0}'".format(char))
        elif state == State.INTEGER_SIGN:
            if char == "0":
                next_state = State.INTEGER_0
                add_char = True
            elif char in "123456789":
                next_state = State.INTEGER
                add_char = True
            else:
                raise ValueError("A - must be followed by a digit.  Got '{0}'".format(char))
        elif state == State.INTEGER_EXP_0:
            if char == "+" or char == "-" or char in "0123456789":
                next_state = State.INTEGER_EXP
                add_char = True
            else:
                raise ValueError("An e in a number must be followed by a '+', '-' or digit.  Got '{0}'".format(char))
        elif state == State.INTEGER_EXP:
            if char in "0123456789":
                add_char = True
            elif is_delimiter(char):
                completed = True
                now_token = (TokenType.NUMBER, float("".join(token)))
                next_state = State.WHITESPACE
                advance = False
            else:
                raise ValueError("A number exponent must consist only of digits.  Got '{}'".format(char))
        elif state == State.FLOATING_POINT:
            if char in "0123456789":
                add_char = True
            elif char == "e" or char == "E":
                next_state = State.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                completed = True
                now_token = (TokenType.NUMBER, float("".join(token)))
                next_state = State.WHITESPACE
                advance = False
            else:
                raise ValueError("A number must include only digits")
        elif state == State.FLOATING_POINT_0:
            if char in "0123456789":
                next_state = State.FLOATING_POINT
                add_char = True
            else:
                raise ValueError("A number with a decimal point must be followed by a fractional part")
        elif state == State.FALSE_1:
            if char == "a":
                next_state = State.FALSE_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_2:
            if char == "l":
                next_state = State.FALSE_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_3:
            if char == "s":
                next_state = State.FALSE_4
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.FALSE_4:
            if char == "e":
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.BOOLEAN, False)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_1:
            if char == "r":
                next_state = State.TRUE_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_2:
            if char == "u":
                next_state = State.TRUE_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.TRUE_3:
            if char == "e":
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.BOOLEAN, True)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_1:
            if char == "u":
                next_state = State.NULL_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_2:
            if char == "l":
                next_state = State.NULL_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.NULL_3:
            if char == "l":
                next_state = State.WHITESPACE
                completed = True
                now_token = (TokenType.NULL, None)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == State.STRING:
            if char == "\"":
                completed = True
                now_token = (TokenType.STRING, "".join(token))
                next_state = State.STRING_END
            elif char == "\\":
                next_state = State.STRING_ESCAPE
            else:
                add_char = True
        elif state == State.STRING_END:
            if is_delimiter(char):
                advance = False
                next_state = State.WHITESPACE
            else:
                raise ValueError("Expected whitespace or an operator after strin.  Got '{}'".format(char))
        elif state == State.STRING_ESCAPE:
            next_state = State.STRING
            if char == "\\" or char == "\"":
                add_char = True
            elif char == "b":
                char = "\b"
                add_char = True
            elif char == "f":
                char = "\f"
                add_char = True
            elif char == "n":
                char = "\n"
                add_char = True
            elif char == "t":
                char = "\t"
                add_char = True
            elif char == "r":
                char = "\r"
                add_char = True
            elif char == "/":
                char = "/"
                add_char = True
            elif char == "u":
                next_state = State.UNICODE_1
                charcode = 0
            else:
                raise ValueError("Invalid string escape: {}".format(char))
        elif state == State.UNICODE_1:
            if char in "0123456789":
                charcode = (ord(char) - 48) * 4096
            elif char in "abcdef":
                charcode = (ord(char) - 87) * 4096
            elif char in "ABCDEF":
                charcode = (ord(char) - 55) * 4096
            else:
                raise ValueError("Invalid character code: {}".format(char))
            next_state = State.UNICODE_2
            char = ""
        elif state == State.UNICODE_2:
            if char in "0123456789":
                charcode += (ord(char) - 48) * 256
            elif char in "abcdef":
                charcode += (ord(char) - 87) * 256
            elif char in "ABCDEF":
                charcode += (ord(char) - 55) * 256
            else:
                raise ValueError("Invalid character code: {}".format(char))
            next_state = State.UNICODE_3
            char = ""
        elif state == State.UNICODE_3:
            if char in "0123456789":
                charcode += (ord(char) - 48) * 16
            elif char in "abcdef":
                charcode += (ord(char) - 87) * 16
            elif char in "ABCDEF":
                charcode += (ord(char) - 55) * 16
            else:
                raise ValueError("Invalid character code: {}".format(char))
            next_state = State.UNICODE_4
            char = ""
        elif state == State.UNICODE_4:
            if char in "0123456789":
                charcode += ord(char) - 48
            elif char in "abcdef":
                charcode += ord(char) - 87
            elif char in "ABCDEF":
                charcode += ord(char) - 55
            else:
                raise ValueError("Invalid character code: {}".format(char))
            next_state = State.STRING
            char = chr(charcode)
            add_char = True

        if add_char:
            token.append(char)

        return advance, next_state, charcode
    state = State.WHITESPACE
    char = stream.read(1)
    index = 0
    while char:
        try:
            advance, state, charcode = process_char(char, charcode)
        except ValueError as e:
            raise ValueError("".join([e.args[0], " at index {}".format(index)]))
        if completed:
            completed = False
            token = []
            yield now_token
        if advance:
            char = stream.read(1)
            index += 1
    process_char(" ", charcode)
    if completed:
        yield now_token
