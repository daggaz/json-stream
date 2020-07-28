# json-stream

Simple streaming JSON parser.

`json-stream` is a JSON parser just like the standard library's
 [`json.load()`](https://docs.python.org/3/library/json.html#json.load). It 
 will read a JSON document and convert it into native python types.

Features:
* stream all JSON data types (objects or lists)
* stream nested data
* simple pythonic `list`-like/`dict`-like interface

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
then starts parsing that string and converting the whole document into python types
again stored in memory. For a very large document, this could be more memory
than you have available to your system.

`json-stream` does not read the whole document into memory, it only buffers
enough from the stream to produce the next item of data.

In transient mode (see below) `json-stream` also doesn't store up all of
the parsed data is memory.

### Latency

`json.load()` produces all the data after parsing the whole document. If you
only care about the first 10 items in a list of 2 million items, then you
have wait until all 2 million items have been parsed first.

`json-stream` produces data as soon as it is available in the stream.

## Usage

`json_stream.load()` has two modes of operation, controlled by
the `persistent` argument (default false).

### Transient mode (default)

This mode is appropriate if you can consume the data iteratively. It is also
the mode you must use if you do not want to use the all memory required to store
the entire parsed result.

In transient mode, only the data currently being read is stored in memory. Any
data previously read from the stream is discarded (it's up to you what to do 
with it) and attempting to access this data results in a `TransientAccessException`.

```python
import json_stream

# JSON: {"x": 1, "y": ["a", "b", "c"]}
data = json_stream.load(f)  # {"x": 1, "y": ['a', 'b', 'c']}

# use data like a list or dict
y = data["y"]

# already read past "x" in stream -> exception
x = data["x"]

# iterate
for c in y:
    print(c)  # prints a, b, c

# already read from list -> exception
for c in y: pass
```

### Persistent mode

In persistent mode all previously read data is stored in memory as
it is parsed. The returned `dict`-like or `list`-like objects
can be used just like normal data structures.

If you request an index or key that has already been read from the stream
then it is retrieved from memory. If you request an index or key that has
not yet been read from the stream, then the request blocks until that item
is found in the stream.

```python
import json_stream

# JSON: {"x": 1, "y": ["a", "b", "c"]}
data = json_stream.load(f, persistent=True)

# use data like a list or dict
# stream is read up to the middle of list
b = data["y"][1]  # b = "b"

# read from memory
x = data["x"]  # x = 1
```

Persistent mode is not appropriate if you care about memory consumption, but
provides an identical experience compared to `json.load()`.

## visitor pattern

You can also parse using a visitor-style approach where a function you supply
is called for each data item as it is parsed (depth-first).

This uses a transient parser under the hood, so does not consume memory for
the whole document.

```python
import json_stream

# JSON: {"x": 1, "y": {}, "xxxx": [1,2, {"yyyy": 1}, "z", 1, []]}

def visitor(path, data):
    print(f"{path}: {data}")

json_stream.visit(f, visitor)
```

Output:
```
('x',): 1
('y',): {}
('xxxx', 0): 1
('xxxx', 1): 2
('xxxx', 2, 'yyyy'): 1
('xxxx', 3): z
('xxxx', 4): 1
('xxxx', 5): []
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

[Yajl-Py]() is a wrapper around the Yajl JSON library that can be used to 
generate SAX style events while parsing JSON.

### Why not Yajl-Py?

* It's not pure python
* It does not provide a pythonic `dict`/`list`-like interface 

# Acknowledgements

The JSON tokenizer used in the project was taken from the [NAYA](https://github.com/danielyule/naya) project.
