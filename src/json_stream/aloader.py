from json_stream.tokenizer import TokenType, tokenize


async def aensure_file(fp_or_iterable):
    return fp_or_iterable  # TODO


async def aload(fp_or_iterable, persistent=False, tokenizer=tokenize):
    many = aload_many(fp_or_iterable, persistent=persistent, tokenizer=tokenizer)
    return await anext(many)


async def aload_many(fp_or_iterable, persistent=False, tokenizer=tokenize):
    fp = await aensure_file(fp_or_iterable)
    token_stream = await tokenizer(fp)
    async for token_type, token in token_stream:
        if token_type == TokenType.OPERATOR:
            data = await AStreamingJSONBase.factory(token, token_stream, persistent)
            yield data
            await data.aread_all()
        else:
            yield token
