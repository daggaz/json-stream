import asyncio

from json_stream.tests import base_tokenizer_tests, AStringIO
from json_stream.tokenizer import tokenize


class TestAsyncTokenizer(base_tokenizer_tests.JsonTokenizationTestCase):
    def tokenize_sequence(self, string):
        return asyncio.run(self._tokenize_sequence(string))

    async def _tokenize_sequence(self, string):
        return [token async for token in await tokenize(AStringIO(string))]
