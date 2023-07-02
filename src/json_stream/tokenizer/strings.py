import io
import unicodedata
from typing import Union
from io import DEFAULT_BUFFER_SIZE

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

SURROGATE = 'Cs'

CHAR = 1
STRING_ESCAPE = 2
UNICODE = 4
UNICODE_SURROGATE_START = 5
UNICODE_SURROGATE_STRING_ESCAPE = 6
UNICODE_SURROGATE = 7


class JsonStringReader(io.TextIOBase):
    def __init__(self, stream: io.TextIOBase, initial_buffer=''):
        self.stream = stream
        self.buffer = initial_buffer
        self.readline_buffer = ''
        self.unicode_buffer = ''
        self.state = CHAR
        self.end_of_string = False
        self.index = 0

    @property
    def complete(self):
        return self.end_of_string and not self.readline_buffer

    def readable(self) -> bool:
        return True

    def read(self, size: Union[int, None] = None) -> str:
        result = ''
        length = DEFAULT_BUFFER_SIZE
        while not self.complete and (size is None or not result):
            if size:
                length = size - len(result)
            result += self._read_chunk(length)
        return result

    def _read_chunk(self, size: int) -> str:
        if self.readline_buffer:
            result, self.readline_buffer = self.readline_buffer[:size], self.readline_buffer[size:]
            return result
        chunk = self.buffer or self.stream.read(size)
        if not chunk:
            raise ValueError("Unterminated string at end of file")
        state = self.state
        unicode_buffer = self.unicode_buffer
        result = ""
        start = 0
        for i, c in enumerate(chunk):
            self.index += 1
            if i == size:
                if state == CHAR:
                    result += chunk[start:i]
                self.buffer = chunk[i:]
                break
            if state == CHAR:
                if c == '"':
                    result += chunk[start:i]
                    self.end_of_string = True
                    self.buffer = chunk[i + 1:]
                    break
                elif c == "\\":
                    state = STRING_ESCAPE
                    result += chunk[start:i]
                    start = i + 1

            elif state == STRING_ESCAPE:
                char = STRING_ESCAPE_CODES.get(c)
                start = i + 1
                if char:
                    result += char
                    state = CHAR
                elif c == 'u':
                    state = UNICODE
                else:
                    raise ValueError("Invalid string escape: {}".format(c))

            elif state == UNICODE:
                unicode_buffer += c
                start = i + 1
                if len(unicode_buffer) == 4:
                    try:
                        code_point = int(unicode_buffer, 16)
                    except ValueError:
                        raise ValueError(f"Invalid unicode literal: \\u{unicode_buffer}")
                    char = chr(code_point)
                    if unicodedata.category(char) == SURROGATE:
                        state = UNICODE_SURROGATE_START
                    else:
                        result += char
                        unicode_buffer = ''
                        state = CHAR

            elif state == UNICODE_SURROGATE_START:
                if c == "\\":
                    state = UNICODE_SURROGATE_STRING_ESCAPE
                    start = i + 1
                else:
                    raise ValueError(f"Unpaired UTF-16 surrogate")

            elif state == UNICODE_SURROGATE_STRING_ESCAPE:
                if c == "u":
                    state = UNICODE_SURROGATE
                    start = i + 1
                else:
                    raise ValueError(f"Unpaired UTF-16 surrogate")

            elif state == UNICODE_SURROGATE:
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
                    state = CHAR
        else:
            result += chunk[start:]
            self.buffer = ''

        self.state = state
        self.unicode_buffer = unicode_buffer
        return result

    def readline(self, size: int = None) -> str:
        result = ''
        read_size = DEFAULT_BUFFER_SIZE
        while not self.complete:
            if size:
                result_length = len(result)
                if result_length >= size:
                    result, self.readline_buffer = result[:size], result[size:] + self.readline_buffer
                    break
                read_size = size - result_length
            chunk = self._read_chunk(read_size)
            i = chunk.find('\n')
            if i < 0:
                result += chunk
            else:
                chunk, self.readline_buffer = chunk[:i+1], chunk[i+1:]
                result += chunk
                break
        return result
