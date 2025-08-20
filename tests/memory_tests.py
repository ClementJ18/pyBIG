import os
import sys
import unittest
from gc import get_referents
from types import FunctionType, ModuleType

from pyBIG import InDiskArchive, InMemoryArchive

# Custom objects know their class.
# Function objects seem to know way too much, including modules.
# Exclude modules as well.
BLACKLIST = type, ModuleType, FunctionType


def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError("getsize() does not take argument of type: " + str(type(obj)))
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
        archive = InMemoryArchive.empty()
        archive.add_file("test_file.txt", b"Clement1" * 1250000)

        in_memory_size = getsize(archive)

        archive = InDiskArchive.empty(file_path="big_big.big")
        archive.add_file("test_file.txt", b"Clement1" * 1250000)
        archive.save()

        on_disk_size = getsize(archive)

        os.remove("big_big.big")

        assert in_memory_size > on_disk_size

    def test_2(self):
        archive = InDiskArchive.empty(file_path="big_big.big")
        archive.add_file("test_file.txt", b"Clement1" * 1250000)
        archive.save()

        post_save_size = getsize(archive)

        archive = InDiskArchive("big_big.big")

        loaded_size = getsize(archive)

        os.remove("big_big.big")

        assert post_save_size == loaded_size


if __name__ == "__main__":
    # python -m unittest
    unittest.main()
