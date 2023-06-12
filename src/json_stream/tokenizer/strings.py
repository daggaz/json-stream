import io
import unicodedata
from typing import Union

from json_stream.tokenizer import State, SURROGATE

STRING_ESCAPE_CODES = {
    '\\': '\\',
    '/': '/',
    '"': '"',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    't': '\t',
    'r': '\r'
}


class JsonStringReader(io.TextIOBase):
    def __init__(self, stream: io.TextIOBase, initial_buffer=''):
        self.stream = stream
        self.buffer = initial_buffer
        self.unicode_buffer = ''
        self.state = State.STRING
        self.complete = False

    def read(self, size: Union[int, None] = None) -> str:
        result = ''
        length = io.DEFAULT_BUFFER_SIZE
        while not self.complete and (size is None or not result):
            if size:
                length = size - len(result)
            result += self._read_chunk(length)
        return result

    def _read_chunk(self, size: Union[int, None] = ...) -> str:
        chunk = self.buffer or self.stream.read(size)
        if not chunk:
            raise ValueError("Unterminated string at end of file")
        state = self.state
        unicode_buffer = self.unicode_buffer
        result = ""
        start = 0
        for i, c in enumerate(chunk):
            if i == size:
                if state == State.STRING:
                    result += chunk[start:i]
                self.buffer = chunk[i:]
                break
            if state == State.STRING:
                if c == '"':
                    result += chunk[start:i]
                    self.complete = True
                    self.buffer = chunk[i + 1:]
                    break
                elif c == "\\":
                    state = State.STRING_ESCAPE
                    result += chunk[start:i]
                    start = i + 1

            elif state == State.STRING_ESCAPE:
                char = STRING_ESCAPE_CODES.get(c)
                start = i + 1
                if char:
                    result += char
                    state = State.STRING
                elif c == 'u':
                    state = State.UNICODE
                else:
                    raise ValueError("Invalid string escape: {}".format(c))

            elif state == State.UNICODE:
                unicode_buffer += c
                start = i + 1
                if len(unicode_buffer) == 4:
                    try:
                        code_point = int(unicode_buffer, 16)
                    except ValueError:
                        raise ValueError(f"Invalid unicode literal: \\u{unicode_buffer}")
                    char = chr(code_point)
                    if unicodedata.category(char) == SURROGATE:
                        state = State.UNICODE_SURROGATE_START
                    else:
                        result += char
                        unicode_buffer = ''
                        state = State.STRING

            elif state == State.UNICODE_SURROGATE_START:
                if c == "\\":
                    state = State.UNICODE_SURROGATE_STRING_ESCAPE
                    start = i + 1
                else:
                    raise ValueError(f"Unpaired UTF-16 surrogate")

            elif state == State.UNICODE_SURROGATE_STRING_ESCAPE:
                if c == "u":
                    state = State.UNICODE_SURROGATE
                    start = i + 1
                else:
                    raise ValueError(f"Unpaired UTF-16 surrogate")

            elif state == State.UNICODE_SURROGATE:
                unicode_buffer += c
                start = i + 1
                if len(unicode_buffer) == 8:
                    code_point_1 = int(unicode_buffer[:4], 16)
                    try:
                        code_point_2 = int(unicode_buffer[4:], 16)
                    except ValueError:
                        raise ValueError(f"Invalid unicode literal: \\u{unicode_buffer[4:]}")
                    if unicodedata.category(chr(code_point_2)) != SURROGATE:
                        raise ValueError(f"Second half of UTF-16 surrogate pair is not a surrogate!")
                    try:
                        pair = int.to_bytes(code_point_1, 2, 'little') + int.to_bytes(code_point_2, 2, 'little')
                        result += pair.decode('utf-16-le')
                    except ValueError:
                        raise ValueError(
                            f"Error decoding UTF-16 surrogate pair \\u{unicode_buffer[:4]}\\u{unicode_buffer[4:]}"
                        )
                    unicode_buffer = ''
                    state = State.STRING
        else:
            result += chunk[start:]
            self.buffer = ''

        self.state = state
        self.unicode_buffer = unicode_buffer
        return result
