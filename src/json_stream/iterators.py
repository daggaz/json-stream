import io


class IterableStream(io.RawIOBase):
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.remainder = None

    def readinto(self, buffer):
        try:
            chunk = self.remainder or next(self.iterator)
            length = min(len(buffer), len(chunk))
            buffer[:length], self.remainder = chunk[:length], chunk[length:]
            return length
        except StopIteration:
            return 0    # indicate EOF

    def readable(self):
        return True


def ensure_file(fp_or_iterable):
    if hasattr(fp_or_iterable, 'read'):
        return fp_or_iterable
    return IterableStream(fp_or_iterable)  # will raise TypeError if not iterable
