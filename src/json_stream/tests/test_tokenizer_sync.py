from io import StringIO


from json_stream.tests import base_tokenizer_tests
from json_stream.tokenizer import tokenize


class TestSyncTokenizer(base_tokenizer_tests.JsonTokenizationTestCase):
    def tokenize_sequence(self, string):
        return list(tokenize(StringIO(string)))
