import io


class IterableStream(io.RawIOBase):
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.remainder = None  # type: bytes | None

    def _normalize_chunk(self, chunk):
        # Ensure chunk is bytes for writing into a binary buffer
        if isinstance(chunk, str):
            return chunk.encode()
        return chunk

    def readinto(self, buffer):
        try:
            # Wrap `buffer: WriteableBuffer` in memoryview to ensure len() and slicing
            mv = memoryview(buffer)
            chunk = self.remainder or self._normalize_chunk(next(self.iterator))
            length = min(len(mv), len(chunk))
            mv[:length], self.remainder = chunk[:length], chunk[length:]
            return length
        except StopIteration:
            return 0    # indicate EOF

    def readable(self):
        return True


def ensure_file(fp_or_iterable):
    if hasattr(fp_or_iterable, 'read'):
        return fp_or_iterable
    return IterableStream(fp_or_iterable)  # will raise TypeError if not iterable
