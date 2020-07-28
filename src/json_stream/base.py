import collections
from collections import OrderedDict
from itertools import chain
from typing import Sized, Optional, Iterator, Sequence, Union, Any, Mapping

from naya.json import TOKEN_TYPE


class TransientAccessException(Exception):
    pass


class StreamingJSONStates:
    STREAMING = 'STREAMING'
    DONE = 'DONE'


class StreamingJSONBase(Sized):
    @classmethod
    def factory(cls, token, token_stream, persistent):
        if token == '{':
            return StreamingJSONObject(token_stream, persistent)
        if token == '[':
            return StreamingJSONList(token_stream, persistent)
        raise ValueError(f"Unknown operator {token}")

    def __init__(self, token_stream, persistent):
        self._state = StreamingJSONStates.STREAMING
        self._stream = token_stream
        self._child: Optional[StreamingJSONBase] = None
        self._data = self._init_persistent_data() if persistent else None
        self._i = -1

    @property
    def persistent(self):
        return self._data is not None

    def _clear_child(self):
        if self._child is not None:
            self._child.read_all()
            self._child = None

    def _iter_items(self):
        while True:
            yield self._next()

    def _next(self):
        if not self.is_streaming():
            raise StopIteration()
        self._clear_child()
        item = self._load_item()
        self._i += 1
        return item

    def _done(self):
        self._state = StreamingJSONStates.DONE
        raise StopIteration()

    def read_all(self):
        collections.deque(self._iter_items(), maxlen=0)

    def _iter(self):
        return self._iter_items()

    def _init_persistent_data(self):
        raise NotImplementedError()

    def _load_item(self):
        raise NotImplementedError()

    def is_streaming(self):
        return self._state == StreamingJSONStates.DONE

    def __iter__(self) -> Iterator[str]:
        if self.persistent:
            return chain(self._data, self._iter())
        if self._i != -1:
            raise TransientAccessException("Cannot restart iteration of transient JSON stream")
        return self._iter()

    def __len__(self) -> int:
        self.read_all()
        return self._i + 1

    def __repr__(self):
        return f"<{type(self).__name__}: {repr(self._data)}, {self._state}>"


class StreamingJSONList(StreamingJSONBase, Sequence):
    def __init__(self, token_stream, persistent):
        super().__init__(token_stream, persistent)

    def _init_persistent_data(self):
        return []

    def _load_item(self):
        token_type, v = next(self._stream)
        if token_type == TOKEN_TYPE.OPERATOR:
            if v == ']':
                self._done()
            if v == ',':
                token_type, v = next(self._stream)
            else:
                raise ValueError(f"Expecting value, comma or ], got {v}")
        if token_type == TOKEN_TYPE.OPERATOR:
            self._child = v = StreamingJSONBase.factory(v, self._stream, self.persistent)
        if self._data is not None:
            self._data.append(v)
        return v

    def _find_item(self, i):
        if self._i >= i:
            raise TransientAccessException(f"Index {i} already passed in this stream")
        for v in iter(self._iter_items()):
            if self._i == i:
                return v
        raise IndexError(f"Index {i} out of range")

    def __getitem__(self, i: Union[int, slice]) -> Any:
        if self.persistent:
            try:
                return self._data[i]
            except IndexError:
                pass
        return self._find_item(i)


class StreamingJSONObject(StreamingJSONBase, Mapping):
    def _init_persistent_data(self):
        return OrderedDict()

    def _iter(self):
        return (k for k, v in self._iter_items())

    def items(self):
        return self._iter_items()

    def _load_item(self):
        token_type, k = next(self._stream)
        if token_type == TOKEN_TYPE.OPERATOR:
            if k == '}':
                self._done()
            if k == ',':
                token_type, k = next(self._stream)
        if token_type != TOKEN_TYPE.STRING:
            raise ValueError(f"Expecting string, comma or }}, got {k} ({token_type})")

        token_type, token = next(self._stream)
        if token_type != TOKEN_TYPE.OPERATOR or token != ":":
            raise ValueError("Expecting :")

        token_type, v = next(self._stream)
        if token_type == TOKEN_TYPE.OPERATOR:
            self._child = v = StreamingJSONBase.factory(v, self._stream, self.persistent)
        if self._data is not None:
            self._data[k] = v
        return k, v

    def _find_item(self, k):
        for next_k, v in iter(self._iter_items()):
            if next_k == k:
                return v
        if self.persistent:
            raise KeyError(k)
        raise TransientAccessException(f"{k} not found in transient JSON stream or already passed in this stream")

    def __getitem__(self, k) -> Any:
        if self.persistent:
            try:
                return self._data[k]
            except KeyError:
                pass
        return self._find_item(k)
