import os
import unittest

from pyBIG import Archive, LargeArchive
from pyBIG.utils import getsize


class MemoryTests(unittest.TestCase):
    def test_1(self):
        archive = Archive.empty()
        archive.add_file("test_file.txt", b"Clement1"*1250000)

        in_memory_size = getsize(archive)

        archive = LargeArchive.empty("big_big.big")
        archive.add_file("test_file.txt", b"Clement1"*1250000)
        archive.save()

        on_disk_size = getsize(archive)

        os.remove("big_big.big")

        assert in_memory_size > on_disk_size

    def test_2(self):
        archive = LargeArchive.empty("big_big.big")
        archive.add_file("test_file.txt", b"Clement1"*1250000)
        archive.save()

        post_save_size = getsize(archive)

        archive = LargeArchive("big_big.big")
        
        loaded_size = getsize(archive)

        os.remove("big_big.big")

        assert post_save_size == loaded_size

if __name__ == "__main__":
    # python -m unittest
    unittest.main()