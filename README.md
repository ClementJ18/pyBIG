# pyBIG
Python library to programatically manipulate .big files, the archive format used in many of the game titles created by EA studios.

This library is largely possible due to the work done by the OpenSage team ([Link](https://github.com/OpenSAGE/Docs/blob/master/file-formats/big/index.rst)). Eseentially this library is a python wrapper around the knowledge they gathered with some helper functions.

## Usage
The library is based on the pyBIG.Archive object. This objects takes raw bytes representing a BIG archive. The decision to take raw bytes allow the user to decide where those bytes come from, whether a file stored in memory or on disk. There is also a class method, Archive.from_directory that allows you to load a directory on the disk painlessly.

You can modify the archive in memory with the following methods:
 - Archive.edit_file(str, bytes)
 - Archive.add_file(str, bytes)
 - Archive.remove_file(str)

Each method takes a name which is the windows-format path to the file in the archive so something like 'data\ini\weapon.ini'. The methods that takes bytes represent the new contents of the file as bytes.

It is important to note that these methods do not actually modify the archive but it is as if. This does not update the entries or the raw bytes. If you want to update the archive you need to call Archive.repack(). This is an expensive operation which is only called automatically when the archive is saved or extracted. The rest is up to the user.

You can look at the tests for more examples.

```
from pyBIG import Archive

with open("test.big", "rb") as f:
    archive = Archive(f.read())

```