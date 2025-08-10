# pyBIG
Python library to programatically manipulate .big files, the archive format used in many of the game titles created by Westwood studios.

This library is largely possible due to the work done by the OpenSage team ([Link](https://github.com/OpenSAGE/Docs/blob/master/file-formats/big/index.rst)). Essentially this library is a python wrapper around the knowledge they gathered with some helper functions.

## Installation

You can get it from Pypi: https://pypi.org/project/pyBIG/

```
pip install pyBIG
```

## Usage
This library offers a few different implementations of BaseArchive that all represent a .BIG archive. Their main difference is how they manipulate the data. Read below to select the best one for your use case. All these objects have the same or very similar interface. Namely:
 - BaseArchive.edit_file(str, bytes)
 - BaseArchive.add_file(str, bytes)
 - BaseArchive.remove_file(str)

Each method takes a name which is the windows-format path to the file in the archive so something like 'data\ini\weapon.ini'. The methods that takes bytes represent the new contents of the file as bytes. To apply the changes you need to use BaseARchuve.repack().

There are also a few utility functions
 - BaseArchive.from_directory(str, str, **kwargs)
 - BaseArchive.empty(str, **kwargs)

Below is a more in depth explaination. You can look at the tests for more examples.

### InMemoryArchive
As the name implies, the InMemoryArchive loads the entire archive into memory and keeps it there, doing all manipulations from there. You can save it back to disk with InMemoryArchive.save(str).

```python
from pyBIG import InMemoryArchive

with open("test.big", "rb") as f:
    archive = InMemoryArchive(f.read())

# get the contents of a file as bytes
contents = archive.read_file("data\\ini\\weapon.ini")

#add a new file
archive.add_file("data\\ini\john.ini", b"this is the story of a man named john")
archive.repack()

#remove a file
archive.remove_file("data\\ini\\john.ini")
archive.repack()

#save the big file back to disk, this will also take care of repacking
# the file with the latest modified entries
archive.save("test.big")

# extract all the files in the archive
archive.extract("output/")

# load an archive from a directory
archive = InMemoryArchive.from_directory("output/")

```

### InDiskArchive
The InDiskArchive does not store the entire file into memory, allowing for manipulation of larger files. It works essentially the same except that reading is done from the file present on disk and functions are tied to that location. Repacking does the same as save on this object but it is recommended to instead use the save function.

It is important to note that adding and editing files in a InDiskArchive stores them in memory. As such it is recommended to save at regular interval to commit these changes to disk. The BaseArchive object exposes `archive_memory_size` as a simple way of seeing how many bytes are currently stored directly on the object. 

```python
from pyBIG import InDiskArchive

archive = InDiskArchive("test.big")
```

## RefPack

The library grossly implements the refpack compression algorithm which allows users to compress and decompress files to and from that format. This is done very simply:
```python

from pyBIG import refpack

to_compress = b"My bytes to compress"
compressed = refpack.compress(to_compress)
decompressed = refpack.decompress(compressed)


assert to_compress == decompressed
```

You can also check if data has the refpack header which is a potential indicator that the data is refpack encoded using `refpack.has_refpack_header`. Data without the header could still be encoded, just without the header. Best way to try is to just attempt to decompress, python zen and all.

For clarity, you must compressed individual files before adding them to the the .big file, is is entirely left up to the reponsibility of the user to do this. If you have done so then the SAGE engine games will be able to read the compressed files flawlessly.

## Tests

Tests must be run from root directory
* `python -m unittest tests.functional_tests`
* `python -m unittest tests.memory_tests`
* `python -m unittest tests.profiler`


## TODO
- [x] Investigate and implement proper compression (refpack)


## Changelog
### v0.6.2
- `InDiskArchive.empty()` now allows overwriting existing files

### v0.6.1
- Type hinted `BaseArchive.bytes()`

### v0.6.0
- Archive renamed to InMemoryArchive (alias remains for backwards compatibility)
- LargeArchive renamed to InDiskArchive (alias remains for backward comaptibility)
- Backend reworked to be cleaner
- Archives now handle different .big types
- `InDiskArchive.from_directory` implemented but not very efficient yet
- Added more typing
- Added `BaseArchive.bytes`
- Inmplemented refpack compression

