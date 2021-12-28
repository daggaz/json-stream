from threading import local, Lock

from json_stream.dump import JSONStreamEncoder, _original_default

_lock = Lock()  # locked during state changes
_counter = 0  # number of patched threads
_thread = local()  # is *this* thread patched
_patched = Lock()  # locked while patch is active


class ThreadSafeJSONStreamEncoder(JSONStreamEncoder):
    def __enter__(self):
        global _counter
        with _lock:
            if _counter == 0:
                # patch if we are first
                _patched.acquire()
                super().__enter__()
            _thread.patched = True
            _counter += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _counter
        with _lock:
            _counter -= 1
            if _counter == 0:
                # unpatch if we are last
                super().__exit__(exc_type, exc_val, exc_tb)
                _patched.release()
            _thread.patched = False

    def default(self, obj):
        # if we end up being called by a thread that is _not_
        # patch (i.e. in a ThreadSafeJSONStreamEncoder
        # context), we must ensure that the patch is not active
        if not getattr(_thread, "patched", False):
            # block until any patching has been removed
            with _patched:
                # patch cannot be applied while in here
                assert not getattr(_thread, "patched", False)
                return _original_default
        return super().default(obj)
