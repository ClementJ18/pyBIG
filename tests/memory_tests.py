import os
import sys
from gc import get_referents
from types import FunctionType, ModuleType
import unittest

from pyBIG import Archive, LargeArchive

# Custom objects know their class.
# Function objects seem to know way too much, including modules.
# Exclude modules as well.
BLACKLIST = type, ModuleType, FunctionType


def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('getsize() does not take argument of type: '+ str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size


class MemoryTests(unittest.TestCase):
    def test_1(self):
        archive = Archive.empty()
        archive.add_file("test_file.txt", b"Clement1"*1250000)

        in_memory_size = getsize(archive)

        archive = LargeArchive.empty("big_big.big")
        archive.add_file("test_file.txt", b"Clement1"*1250000)

        on_disk_size = getsize(archive)

        os.remove("big_big.big")

        assert in_memory_size > on_disk_size

    def test_2(self):
        archive = LargeArchive.empty("big_big.big")
        archive.add_file("test_file.txt", b"Clement1"*1250000)

        pre_save_size = getsize(archive)

        archive.save()

        post_save_size = getsize(archive)

        archive = LargeArchive("big_big.big")
        
        loaded_size = getsize(archive)

        os.remove("big_big.big")

        assert pre_save_size == post_save_size == loaded_size

if __name__ == "__main__":
    # python -m unittest
    unittest.main()