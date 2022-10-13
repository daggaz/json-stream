# json-stream

[![Tests](https://github.com/daggaz/json-stream/actions/workflows/tests.yml/badge.svg)](https://github.com/daggaz/json-stream/actions/workflows/tests.yml)
[![PyPI package and version badge](https://img.shields.io/pypi/v/json-stream)](https://pypi.org/project/json-stream)
[![Supported Python versions badge](https://img.shields.io/pypi/pyversions/json-stream)](https://pypi.org/project/json-stream/)
[![Donate](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-blue.svg)](https://www.buymeacoffee.com/daggaz)

Simple streaming JSON parser and encoder.

When [reading](#reading) JSON data, `json-stream` can decode JSON data in 
a streaming manner.

When [writing](#writing) JSON data, `json-stream` can stream JSON objects 
as you produce them.

These techniques allow you to [reduce memory consumption and 
latency](#standard-json-problems).

# <a id="reading"></a> Reading

`json-stream` is a JSON parser just like the standard library's
 [`json.load()`](https://docs.python.org/3/library/json.html#json.load). It 
 will read a JSON document and convert it into native python types.

```python
import json_stream
data = json_stream.load(f)
```

Features:
* stream all JSON data types (objects, lists and simple types)
* stream nested data
* simple pythonic `list`-like/`dict`-like interface
* stream truncated or malformed JSON data (up to the first error)
* [native code parsing speedups](#rust-tokenizer) for most common platforms 
* pure python fallback if native extensions not available

Unlike `json.load()`, `json-stream` can _stream_ JSON data from a file-like
object. This has the following benefits:

* it does not require the whole json document to be read into memory up-front
* it can start producing data before the entire document has finished loading
* it only requires enough memory to hold the data currently being parsed

## Usage

### `json_stream.load()`

`json_stream.load()` has two modes of operation, controlled by
the `persistent` argument (default false).

It is also possible to "mix" the modes as you consume the data.

#### Transient mode (default)

This mode is appropriate if you can consume the data iteratively. You cannot 
move backwards through the stream to read data that has already been skipped
over. It is the mode you **must** use if you want process large amounts of
JSON data without consuming large amounts of memory required.

In transient mode, only the data currently being read is stored in memory. Any
data previously read from the stream is discarded (it's up to you what to do 
with it) and attempting to access this data results in a
`TransientAccessException`.

```python
import json_stream

# JSON: {"count": 3, "results": ["a", "b", "c"]}
data = json_stream.load(f)  # data is a transient dict-like object 
# stream has been read up to "{"

# use data like a dict
results = data["results"]  # results is a transient list-like object
# stream has been read up to "[", we now cannot read "count"

# iterate transient list
for result in results:
    print(result)  # prints a, b, c
# stream has been read up to "]"

# attempt to read "count" from earlier in stream
count = data["count"]  # will raise exception
# stream is now exhausted

# attempt to read from list that has already been iterated
for result in results:  # will raise exception
    pass
```

#### Persistent mode

In persistent mode all previously read data is stored in memory as
it is parsed. The returned `dict`-like or `list`-like objects
can be used just like normal data structures.

If you request an index or key that has already been read from the stream
then it is retrieved from memory. If you request an index or key that has
not yet been read from the stream, then the request blocks until that item
is found in the stream.

```python
import json_stream

# JSON: {"count": 1, "results": ["a", "b", "c"]}
data = json_stream.load(f, persistent=True)
# data is a streaming  dict-like object 
# stream has been read up to "{"

# use data like a dict
results = data["results"]  # results is a streaming list-like object
# stream has been read up to "["
# count has been stored data

# use results like a list
a_result = results[1]  # a_result = "b"
# stream has been read up to the middle of list
# "a" and "b" have been stored in results

# read earlier data from memory
count = data["count"]  # count = 1

# consume rest of list
results.read_all()
# stream has been read up to "}"
# "c" is now stored in results too
# results.is_streaming() == False

# consume everything
data.read_all()
# stream is now exhausted
# data.is_streaming() == False
```

Persistent mode is not appropriate if you care about memory consumption, but
provides an identical experience compared to `json.load()`.

#### Mixed mode

In some cases you will need to be able to randomly access some part of the 
data, but still only have that specific data taking up memory resources.

For example, you might have a very long list of objects, but you cannot always 
access the keys of the objects in stream order. You want to be able to iterate
the list transiently, but access the result objects persistently.

This can be achieved using the `persistent()` method of all the `list` or
`dict`-like objects json_stream produces. Calling `persistent()` causes the existing
transient object to produce persistent child objects.

Note that the `persistent()` method makes the children of the object it
is called on persistent, not the object it is called on.

```python
import json_stream

# JSON: {"results": [{"x": 1, "y": 3}, {"y": 4, "x": 2}]}
# note that the keys of the inner objects are not ordered 
data = json_stream.load(f)  # data is a transient dict-like object 

# iterate transient list, but produce persistent items
for result in data['results'].persistent():
    # result is a persistent dict-like object
    print(result['x'])  # print x
    print(result['y'])  # print y (error on second result without .persistent())
    print(result['x'])  # print x again (error without .persistent())
```

The opposite is also possible, going from persistent mode to transient mode, though 
the use cases for this are more esoteric.

```python
# JSON: {"a": 1, "x": ["long", "list", "I", "don't", "want", "in", "memory"], "b": 2}
data = load(StringIO(json), persistent=True).transient()
# data is a persistent dict-list object that produces transient children

print(data["a"])  # prints 1
x = data["x"]  # x is a transient list, you can use it accordingly
print(x[0])  # prints long

# access earlier data from memory
print(data["a"])  # this would have raised an exception if data was transient

print(data["b"])  # prints 2

# we have now moved past all the data in the transient list
print(x[0])  # will raise exception
```

### visitor pattern

You can also parse using a visitor-style approach where a function you supply
is called for each data item as it is parsed (depth-first).

This uses a transient parser under the hood, so does not consume memory for
the whole document.

```python
import json_stream

# JSON: {"x": 1, "y": {}, "xxxx": [1,2, {"yyyy": 1}, "z", 1, []]}

def visitor(item, path):
    print(f"{item} at path {path}")

json_stream.visit(f, visitor)
```

Output:
```
1 at path ('x',)
{} at path ('y',)
1 at path ('xxxx', 0)
2 at path ('xxxx', 1)
1 at path ('xxxx', 2, 'yyyy')
z at path ('xxxx', 3)
1 at path ('xxxx', 4)
[] at path ('xxxx', 5)
```

### Stream a URL

#### urllib

```python
import urllib.request
import json_stream

with urllib.request.urlopen('http://example.com/data.json') as response:
    data = json_stream.load(response)
```

#### requests

```python
import requests
import json_stream.requests

with requests.get('http://example.com/data.json', stream=True) as response:
    data = json_stream.requests.load(response)
```

### Stream a URL (with visitor)

#### urllib

```python
import urllib.request
import json_stream

def visitor(item, path):
    print(f"{item} at path {path}")
    
with urllib.request.urlopen('http://example.com/data.json') as response:
    json_stream.visit(response, visitor)
```

#### requests

```python
import requests
import json_stream.requests

def visitor(item, path):
    print(f"{item} at path {path}")
    
with requests.get('http://example.com/data.json', stream=True) as response:
    json_stream.requests.visit(response, visitor)
```

### Encoding json-stream objects

You can encode _persistent_ json-stream `dict`-like and `list`-like object back to JSON using the built-in
`json.dump()` or `json.dumps` functions, but with a little additional work:

```python
import json

import json_stream
from json_stream.dump import JSONStreamEncoder, default

data = json_stream.load(f, persistent=True)

# Option 1: supply json_stream.encoding.default as the default argument
print(json.dumps(data, default=default))

# Option 2: supply json_stream.encoding.JSONStreamEncoder as the cls argument
# This allows you to create your own subclass to further customise encoding
print(json.dumps(data, cls=JSONStreamEncoder))
```

If you are using a library that internally takes data you pass it and encodes
it using `json.dump()`. You can also use JSONStreamEncoder() as a context manager.

It works by monkey-patching the built-in `JSONEncoder.default` method during the
scope of the `with` statement.

```python 
# library code
def some_library_function_out_of_your_control(arg):
    json.dumps(arg)

# your code
with JSONStreamEncoder():
    some_library_function_out_of_your_control(data)
```

#### Thread safety (experimental)

There is also a thread-safe version of the `json.dump` context manager:

```python
from json_stream.dump.threading import ThreadSafeJSONStreamEncoder

# your code
with ThreadSafeJSONStreamEncoder():
   some_library_function_out_of_your_control(data)
```

The thread-safe implementation will ensure that concurrent uses of the 
context manager will only apply the patch for the first thread entering
the patched section(s) and will only remove the patch when the last
thread exits the patched sections(s)

Additionally, if the patch is somehow called by a thread that is _not_
currently in a patched section (i.e. some other thread calling 
`json.dump`) then that thread will block until the patch has been
removed. While such an un-patched thread is active, any thread attempting
to apply the patch is blocked.

### <a id="rust-tokenizer"></a> Rust tokenizer speedups

By default `json-stream` uses the 
[`json-stream-rs-tokenizer`](https://pypi.org/project/json-stream-rs-tokenizer/)
native extension.

This is a 3rd party Rust-based tokenizer implementations that provides
significant parsing speedup compared to pure python implementation.

`json-stream` will fallback to its pure python tokenizer implementation
if `json-stream-rs-tokenizer` is not available.

### Custom tokenizer

You can supply an alternative JSON tokenizer implementation. Simply pass 
a tokenizer to the `load()` or `visit()` methods.

```python
json_stream.load(f, tokenizer=some_tokenizer)
```

The requests methods also accept a customer tokenizer parameter.


# Writing

The standard library's `json.dump()` function can only accept standard
python types such as `dict`, `list`, `str`.

`json-stream` allows you to write streaming JSON output based on python
generators instead.

For actually encoding and writing to the stream, `json-stream` 
still uses the standard library's `json.dump()` function, but provides
wrappers that adapt python generators into `dict`/`list` subclasses 
that `json.dump()` can use.

The means that you do not have to generate all of your data upfront
before calling `json.dump()`.

## Usage

To use `json-stream` to generate JSON data iteratively, you must first 
write python generators (or use any other iterable).

To output JSON objects, the iterable must yield key/value pairs.

To output JSON lists, the iterable must yield individual items.

The values yielded can be either be standard python types or another other
`Streamable` object, allowing lists and object to be arbitrarily nested.

`streamable_list`/`streamable_dict` can be used to wrap an existing
iterable:
```python
import sys
import json

from json_stream import streamable_list

# wrap existing iterable
data = streamable_list(range(10))

# consume iterable with standard json.dump()
json.dump(data, sys.stdout)
```

Or they can be used as decorators on generator functions:
```python
import json
import sys

from json_stream import streamable_dict

# declare a new streamable dict generator function
@streamable_dict
def generate_dict_of_squares(n):
    for i in range(n):
        # this could be some memory intensive operation
        # or just a really large value of n
        yield i, i ** 2

# data is will already be Streamable because
# of the decorator
data = generate_dict_of_squares(10)
json.dump(data, sys.stdout)
```

## Example

The following example generates a JSON object with a nested JSON list.
It uses `time.sleep()` to slow down the generation and show that the
output is indeed written as the data is created.

```python
import sys
import json
import time

from json_stream.writer import streamable_dict, streamable_list


# define a list data generator that (slowly) yields 
# items that will be written as a JSON list
@streamable_list
def generate_list(n):
    # output n numbers and their squares
    for i in range(n):  # range is itself a generator
        yield i
        time.sleep(1)


# define a dictionary data generator that (slowly) yields 
# key/value pairs that will be written as a JSON dict
@streamable_dict
def generate_dict(n):
    # output n numbers and their squares
    for i in range(n):  # range is itself a generator
        yield i, i ** 2
        time.sleep(1)

    # yield another dictionary item key, with the value
    # being a streamed nested list
    yield "a list", generate_list(n)


# get a streamable generator
data = generate_dict(5)

# use json.dump() to write dict generator to stdout
json.dump(data, sys.stdout, indent=2)

# if you already have an iterable object, you can just
# call streamable_* on it to make it writable
data = streamable_list(range(10))
json.dump(data, sys.stdout)

```

Output:
```json
{
  "0": 0,
  "1": 1,
  "2": 4,
  "3": 9,
  "4": 16,
  "a list": [
    0,
    1,
    2,
    3,
    4
  ]
}
```

# <a id="standard-json-problems"></a> What are the problems with the standard `json` package?

## Reading with `json.load()`
The problem with the `json.load()` stem from the fact that it must read
the whole JSON document into memory before parsing it.

### Memory usage

`json.load()` first reads the whole document into memory as a string. It
then starts parsing that string and converting the whole document into python
types again stored in memory. For a very large document, this could be more
memory than you have available to your system.

`json_stream.load()` does not read the whole document into memory, it only
buffers enough from the stream to produce the next item of data.

Additionally, in the default transient mode (see below) `json-stream` doesn't store 
up all of the parsed data in memory.

### Latency

`json.load()` produces all the data after parsing the whole document. If you
only care about the first 10 items in a list of 2 million items, then you
have wait until all 2 million items have been parsed first.

`json_stream.load()` produces data as soon as it is available in the stream.

## <a id="writing"></a> Writing

### Memory usage

While `json.dump()` does iteratively write JSON data to the given
file-like object, you must first produce the entire document to be 
written as standard python types (`dict`, `list`, etc). For a very
large document, this could be more memory than you have available 
to your system.

`json-stream` allows you iteratively generate your data one item at
a time, and thus consumes only the memory required to generate that
one item.

### Latency

`json.dump()` can only start writing to the output file once all the
data has been generated up front at standard python types.

The iterative generation of JSON items provided by `json-stream`
allows the data to be written as it is produced.

# Future improvements

* Allow long strings in the JSON to be read as streams themselves
* Allow transient mode on seekable streams to seek to data earlier in
the stream instead of raising a `TransientAccessException`
* A more efficient tokenizer?

# Alternatives

## NAYA

[NAYA](https://github.com/danielyule/naya) is a pure python JSON parser for
parsing a simple JSON list as a stream.

### Why not NAYA?

* It can only stream JSON containing a top-level list 
* It does not provide a pythonic `dict`/`list`-like interface 

## Yajl-Py

[Yajl-Py](https://pykler.github.io/yajl-py/) is a wrapper around the Yajl JSON library that can be used to 
generate SAX style events while parsing JSON.

### Why not Yajl-Py?

* It's not pure python
* It does not provide a pythonic `dict`/`list`-like interface 

# Build
```bash
cd ~/sources/json-stream/
python3 -m venv ~/build/
. ~/build/bin/activate
pip install --upgrade build twine
python -m build
twine upload dist/*
```

# Donations

[![PayPal](https://www.paypalobjects.com/webstatic/mktg/Logo/pp-logo-100px.png)](https://paypal.me/JCockburn307?country.x=GB&locale.x=en_GB)

OR

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/daggaz)

# Acknowledgements

The JSON tokenizer used in the project was taken from the
[NAYA](https://github.com/danielyule/naya) project.
