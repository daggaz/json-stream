import collections
import copy
from abc import ABC
from collections import OrderedDict, deque
from itertools import chain, count as itertools_count, zip_longest
from typing import Optional, Iterator, Any

from json_stream.tokenizer import TokenType


class TransientAccessException(Exception):
    pass


class StreamingJSONBase(ABC):
    INCOMPLETE_ERROR = "Unexpected end of file"

    @classmethod
    def factory(cls, token, token_stream, persistent):
        if persistent:
            if token == '{':
                return PersistentStreamingJSONObject(token_stream)
            if token == '[':
                return PersistentStreamingJSONList(token_stream)
        else:
            if token == '{':
                return TransientStreamingJSONObject(token_stream)
            if token == '[':
                return TransientStreamingJSONList(token_stream)
        raise ValueError(f"Unknown operator {token}")  # pragma: no cover

    _persistent_children: bool

    def __init__(self, token_stream):
        self.streaming = True
        self._stream = token_stream
        self._child: Optional[StreamingJSONBase] = None

    def _clear_child(self):
        if self._child is not None:
            self._child.read_all()
            self._child = None

    def _iter_items(self):
        while True:
            if not self.streaming:
                return
            self._clear_child()
            try:
                item = self._load_item()
            except StopIteration:
                if self.streaming:
                    raise ValueError(self.INCOMPLETE_ERROR)
                return
            yield item

    def _done(self):
        self.streaming = False
        raise StopIteration()

    def read_all(self):
        collections.deque(self._iter_items(), maxlen=0)

    def _load_item(self):
        raise NotImplementedError()  # pragma: no cover

    def _find_item(self, k):
        raise NotImplementedError()  # pragma: no cover

    def _get__iter__(self):
        raise NotImplementedError()  # pragma: no cover

    def __getitem__(self, k) -> Any:
        raise NotImplementedError()  # pragma: no cover

    def __iter__(self) -> Iterator[str]:
        raise NotImplementedError()  # pragma: no cover

    def __copy__(self):
        raise copy.Error("Copying json_steam objects leads to a bad time")

    def __deepcopy__(self, memo):
        raise copy.Error("Copying json_steam objects leads to a bad time")


class PersistentStreamingJSONBase(StreamingJSONBase, ABC):
    def __init__(self, token_stream):
        super().__init__(token_stream)
        self._data = self._init_persistent_data()
        self._persistent_children = True

    def _init_persistent_data(self):
        raise NotImplementedError()  # pragma: no cover

    def transient(self):
        self._persistent_children = False
        return self

    def __iter__(self):
        return chain(self._data, self._get__iter__())

    def __len__(self) -> int:
        self.read_all()
        return len(self._data)

    def __repr__(self):  # pragma: no cover
        return f"<{type(self).__name__}: {repr(self._data)}, {'STREAMING' if self.streaming else 'DONE'}>"

    def __contains__(self, item):
        self.read_all()
        return item in self._data


class TransientStreamingJSONBase(StreamingJSONBase, ABC):
    def __init__(self, token_stream):
        super().__init__(token_stream)
        self._started = False
        self._persistent_children = False

    def _iter_items(self):
        self._started = True
        return super()._iter_items()

    def __getitem__(self, k) -> Any:
        return self._find_item(k)

    def __iter__(self):
        self._check_started()
        return self._get__iter__()

    def persistent(self):
        self._check_started()
        self._persistent_children = True
        return self

    def _check_started(self):
        if self._started:
            raise TransientAccessException("Cannot restart iteration of transient JSON stream")

    def __repr__(self):  # pragma: no cover
        return f"<{type(self).__name__}: TRANSIENT, {'STREAMING' if self.streaming else 'DONE'}>"


class StreamingJSONList(StreamingJSONBase, ABC):
    INCOMPLETE_ERROR = "Unterminated list at end of file"

    def _load_item(self):
        token_type, v = next(self._stream)
        if token_type == TokenType.OPERATOR:
            if v == ']':
                self._done()
            if v == ',':
                token_type, v = next(self._stream)
            elif v in '{[':
                pass
            else:  # pragma: no cover
                raise ValueError(f"Expecting value, comma or ], got {v}")
        if token_type == TokenType.OPERATOR:
            self._child = v = self.factory(v, self._stream, self._persistent_children)
        return v

    def _get__iter__(self):
        return self._iter_items()

    def index(self, item, start=0, stop=None):
        for i, v in enumerate(self._iter_items()):
            if i < start:
                continue
            elif stop is not None and i > stop:
                break
            if v is item or v == item:
                return i
        raise ValueError

    @staticmethod
    def _index_args(*args):
        return args[:args.index(None) if None in args else -1]


class PersistentStreamingJSONList(PersistentStreamingJSONBase, StreamingJSONList):
    def _init_persistent_data(self):
        return []

    def _load_item(self):
        item = super()._load_item()
        self._data.append(item)
        return item

    def _find_item(self, i):
        length = len(self._data)
        for v in iter(self._iter_items()):
            length += 1
            if length > i:
                return v
        raise IndexError(f"Index {i} out of range")

    def __getitem__(self, k) -> Any:
        try:
            return self._data[k]
        except IndexError:
            pass
        return self._find_item(k)

    def index(self, item, /, start=None, stop=None):
        args = self._index_args(start, stop)
        try:
            return self._data.index(item, *args)
        except ValueError:
            return len(self._data) + super().index(item, *args)

    def count(self, item):
        self.read_all()
        return self._data.count(item)

    def __reversed__(self):
        self.read_all()
        return reversed(self._data)


class TransientStreamingJSONList(TransientStreamingJSONBase, StreamingJSONList):
    def __init__(self, token_stream):
        super().__init__(token_stream)
        self._index = -1

    def _load_item(self):
        item = super()._load_item()
        self._index += 1
        return item

    def _find_item(self, i):
        if self._index > i:
            raise TransientAccessException(f"Index {i} already passed in this stream")
        for v in iter(self._iter_items()):
            if self._index == i:
                return v
        raise IndexError(f"Index {i} out of range")

    def index(self, item, /, start=None, stop=None):
        if (start is not None and start < 0) or (stop is not None and stop < 0):
            raise IndexError("Negative indices not supported for transient lists")
        return self._index + super().index(item, *self._index_args(start, stop)) + 1

    def count(self, item):
        self._check_started()
        # equivalent to but faster than sum(1 for i in self if i is item or i == item)
        counter = itertools_count()
        deque(zip((i for i in self._iter_items() if i is item or i == item), counter), maxlen=0)  # (consume at C speed)
        return next(counter)

    def __reversed__(self):
        self._check_started()
        # this approach releases memory as iterator advances
        stack = deque(self._iter_items())
        while stack:
            yield stack.pop()


class StreamingJSONObject(StreamingJSONBase, ABC):
    INCOMPLETE_ERROR = "Unterminated object at end of file"

    def _load_item(self):
        token_type, k = next(self._stream)
        if token_type == TokenType.OPERATOR:
            if k == '}':
                self._done()
            if k == ',':
                token_type, k = next(self._stream)
        if token_type != TokenType.STRING:  # pragma: no cover
            raise ValueError(f"Expecting string, comma or }}, got {k} ({token_type})")

        token_type, token = next(self._stream)
        if token_type != TokenType.OPERATOR or token != ":":
            raise ValueError("Expecting :")  # pragma: no cover

        token_type, v = next(self._stream)
        if token_type == TokenType.OPERATOR:
            self._child = v = self.factory(v, self._stream, self._persistent_children)
        return k, v

    def _get__iter__(self):
        return (k for k, v in self._iter_items())

    def _find_item(self, k):
        for next_k, v in iter(self._iter_items()):
            if next_k == k:
                return v
        raise KeyError(k)

    def items(self):
        raise NotImplementedError()  # pragma: no cover

    def keys(self):
        raise NotImplementedError()  # pragma: no cover

    def values(self):
        raise NotImplementedError()  # pragma: no cover

    def get(self, k, default=None) -> Any:
        try:
            return self[k]
        except KeyError:
            return default


class PersistentStreamingJSONObject(PersistentStreamingJSONBase, StreamingJSONObject):
    def _init_persistent_data(self):
        return OrderedDict()

    def _load_item(self):
        k, v = super()._load_item()
        self._data[k] = v
        return k, v

    def items(self):
        return chain(self._data.items(), self._iter_items())

    def keys(self):
        return chain(self._data.keys(), (k for k, v in self._iter_items()))

    def values(self):
        return chain(self._data.keys(), (v for k, v in self._iter_items()))

    def __getitem__(self, k) -> Any:
        try:
            return self._data[k]
        except KeyError:
            pass
        return self._find_item(k)

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        self.read_all()
        return self._data == other

    def __ne__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        self.read_all()
        return self._data != other


class TransientStreamingJSONObject(TransientStreamingJSONBase, StreamingJSONObject):
    def _find_item(self, k):
        was_started = self._started
        try:
            return super()._find_item(k)
        except KeyError:
            if was_started:
                raise TransientAccessException(
                    f"{k} not found in transient JSON stream or already passed in this stream",
                )
            raise

    def items(self):
        self._check_started()
        return self._iter_items()

    def keys(self):
        self._check_started()
        return (k for k, v in self._iter_items())

    def values(self):
        self._check_started()
        return (v for k, v in self._iter_items())

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        not_equal = object()  # sentinel for length differences
        return all(a == b for a, b in zip_longest(self.items(), other.items(), fillvalue=not_equal))
