# json-stream

Simple streaming JSON parser.

`json-stream` is a JSON parser just like the standard library's
 [`json.load()`](https://docs.python.org/3/library/json.html#json.load). It 
 will read a JSON document and convert it into native python types.

```python
import json_stream
data = json_stream.load(f)
```

Features:
* stream all JSON data types (objects or lists)
* stream nested data
* simple pythonic `list`-like/`dict`-like interface
* stream truncated or malformed JSON data (up to the first error)
* pure python
* no dependencies

Unlike `json.load()`, `json-stream` can _stream_ JSON data from a file-like
object. This has the following benefits:

* It does not require the whole json document to be into memory up-front
* It can start producing data before the entire document has finished loading
* It only requires enough memory to hold the data currently being parsed

## What are the problems with standard `json.load()`?

The problem with the `json.load()` stem from the fact that it must read
the whole JSON document into memory before parsing it.

### Memory usage

`json.load()` first reads the whole document into memory as a string. It
then starts parsing that string and converting the whole document into python
types again stored in memory. For a very large document, this could be more
memory than you have available to your system.

`json_stream.load()` does not read the whole document into memory, it only
buffers enough from the stream to produce the next item of data.

Additionally, in transient mode (see below) `json-stream` also doesn't store 
up all of the parsed data in memory.

### Latency

`json.load()` produces all the data after parsing the whole document. If you
only care about the first 10 items in a list of 2 million items, then you
have wait until all 2 million items have been parsed first.

`json_stream.load()` produces data as soon as it is available in the stream.

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

# attempt to read from list that has already be iterated
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

# Acknowledgements

The JSON tokenizer used in the project was taken from the
[NAYA](https://github.com/danielyule/naya) project.
 