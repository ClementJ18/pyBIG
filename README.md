# pyBIG
Python library to programatically manipulate .big files, the archive format used in many of the game titles created by EA studios.

This library is largely possible due to the work done by the OpenSage team ([Link](https://github.com/OpenSAGE/Docs/blob/master/file-formats/big/index.rst)). Eseentially this library is a python wrapper around the knowledge they gathered with some helper functions.

## Usage
The library allows you to mix and match in-memory and on-disk for the source and destination of the `pack` and `unpack` methods. It is up to the user to be careful not to load any large files into memory. 


### Decoding
```
import pyBIG

# save to disk from disk
with open("test.big", "r") as f:
    file_paths = pyBIG.unpack(f.read(), output="save/files/here/")

# save to memory from memory
# e.g. if we have a bytesIO from pyBIG.pack
directory = {}
pyBIG.unpack(a_bytes_io, to_memory=directory)
```

### Encoding
```
import pyBIG

import io

# save to disk from disk
with open("test.big", "w") as f:
    pyBIG.pack(f, input="load/files/here/")

    #can also be a single file
    pyBIG.pack(f, input="load/files/here/lotr.str")

# save to memory (BytesIO) from memory
f = BytesIO()
pyBIG.pack(f, from_memory=directory)
```