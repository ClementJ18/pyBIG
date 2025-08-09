import logging
import os
from typing import Union
import unittest

from pyBIG import InMemoryArchive, InDiskArchive
from pyBIG.refpack import compress, decompress, has_refpack_header

logging.basicConfig(level=logging.INFO)


TEST_FILE = "read_me_for_test.txt"
TEST_CONTENT = "john"
TEST_ENCODING = "latin-1"
TEST_ARCHIVE = "tests/test_data/empty_archive.big"


class BaseTestCases:
    class BaseTest(unittest.TestCase):
        archive: Union[InMemoryArchive, InDiskArchive]

        def tearDown(self):
            for file in [
                f"tests/test_data/output/{TEST_FILE}",
                "tests/test_data/output/test.big",
                TEST_ARCHIVE,
                "tests/test_data/test_big_type.big",
            ]:
                try:
                    os.remove(file)
                except OSError:
                    pass

        def test_decode(self):
            contents = self.archive.read_file(TEST_FILE)

            with open(f"tests/test_data/{TEST_FILE}", "rb") as f:
                self.assertEqual(f.read(), contents)

            self.assertEqual(len(self.archive.entries), 1)

        def test_remove_file(self):
            self.archive.remove_file(TEST_FILE)
            self.archive.repack()

            self.assertEqual(self.archive.modified_entries, {})
            self.assertNotIn(TEST_FILE, self.archive.entries)

        def test_edit_file(self):
            self.archive.edit_file(TEST_FILE, TEST_CONTENT.encode(TEST_ENCODING))
            self.archive.repack()

            contents = self.archive.read_file(TEST_FILE).decode(TEST_ENCODING)

            self.assertEqual(contents, TEST_CONTENT)

        def test_add_file(self):
            if self.archive.file_exists(TEST_FILE):
                self.archive.remove_file(TEST_FILE)
                self.archive.repack()

            self.archive.add_file(TEST_FILE, TEST_CONTENT.encode(TEST_ENCODING))
            self.archive.repack()

            contents = self.archive.read_file(TEST_FILE).decode(TEST_ENCODING)

            self.assertEqual(contents, TEST_CONTENT)

        def test_extract_and_load(self):
            self.archive.extract("tests/test_data/output")
            self.assertTrue(os.path.exists(f"tests/test_data/output/{TEST_FILE}"))

            new_archive = InMemoryArchive.from_directory("tests/test_data/output")
            self.assertIn(TEST_FILE, new_archive.entries)

            new_archive.save("tests/test_data/output/test.big")
            self.assertTrue(os.path.exists("tests/test_data/output/test.big"))

        def test_utils(self):
            self.archive.file_list()

        def test_archive_memory_size(self):
            archive = InDiskArchive.empty(file_path=TEST_ARCHIVE)
            file_bytes = TEST_CONTENT.encode(TEST_ENCODING)
            archive.add_file(TEST_FILE, file_bytes)

            size = archive.archive_memory_size()

            self.assertEqual(size, len(file_bytes))

        def test_archive_bytes(self):
            data = self.archive.bytes()
            self.assertIsInstance(data, bytes)


class TestArchive(BaseTestCases.BaseTest):
    def setUp(self):
        with open("tests/test_data/test_big.big", "rb") as f:
            self.archive = InMemoryArchive(f.read())

    def test_empty_archive(self):
        archive = InMemoryArchive.empty()
        archive.add_file(TEST_FILE, TEST_CONTENT.encode(TEST_ENCODING))
        archive.repack()

        self.assertIn(TEST_FILE, archive.entries)

    def test_archive_type(self):
        path = "tests/test_data/test_big_type.big"

        for header in ["BIG4", "BIGF"]:
            archive = InMemoryArchive.empty(header)
            archive.add_file(TEST_FILE, TEST_CONTENT.encode(TEST_ENCODING))
            archive.save(path)

            with open(path, "rb") as f:
                archive = InMemoryArchive(f.read())

            self.assertEqual(archive.header, header)
            os.remove("tests/test_data/test_big_type.big")


class TestLargeArchive(BaseTestCases.BaseTest):
    def setUp(self):
        self.archive = InDiskArchive("tests/test_data/test_big.big")

        if self.archive.file_exists(TEST_FILE):
            self.archive.remove_file(TEST_FILE)

        if not self.archive.file_exists(TEST_FILE):
            with open(f"tests/test_data/{TEST_FILE}", "rb") as f:
                self.archive.add_file(TEST_FILE, f.read())

        self.archive.repack()

    def test_empty_archive(self):
        archive = InDiskArchive.empty(file_path=TEST_ARCHIVE)
        archive.add_file(TEST_FILE, TEST_CONTENT.encode(TEST_ENCODING))
        archive.repack()

        self.assertIn(TEST_FILE, archive.entries)

    def test_archive_type(self):
        path = "tests/test_data/test_big_type.big"

        for header in ["BIG4", "BIGF"]:
            archive = InDiskArchive.empty(header, file_path=path)
            archive.add_file(TEST_FILE, TEST_CONTENT.encode(TEST_ENCODING))
            archive.save()
            archive = InDiskArchive(path)
            self.assertEqual(archive.header, header)
            os.remove("tests/test_data/test_big_type.big")


class TestRefPack(unittest.TestCase):
    def test_refpack_check_valid_data(self):
        data = b"Sample data for testing."
        compressed = compress(data)
        self.assertTrue(has_refpack_header(compressed))

    def test_refpack_check_invalid_magic(self):
        invalid_data = b"\x00\x00\x00\x00"
        self.assertFalse(has_refpack_header(invalid_data))

    def test_refpack_check_invalid_size(self):
        # Construct data with valid magic but invalid size (0)
        data = b"\x10\xfb\x00\x00"
        self.assertFalse(has_refpack_header(data))

    def test_compress_decompress_roundtrip(self):
        data = b"Example data to compress and decompress."
        compressed = compress(data)
        decompressed = decompress(compressed)
        self.assertEqual(decompressed, data)

    def test_decompress_size_mismatch_raises(self):
        data = b"Test data with mismatch"
        compressed = compress(data)
        corrupted = bytearray(compressed)
        corrupted[2:5] = b"\x00\x00\x00"  # corrupt expected size
        with self.assertRaises(ValueError):
            decompress(bytes(corrupted), ignore_mismatch=False)

    def test_decompress_size_mismatch_ignore(self):
        data = b"Test data with mismatch"
        compressed = compress(data)
        corrupted = bytearray(compressed)
        corrupted[2:5] = b"\x00\x00\x00"
        decompressed = decompress(bytes(corrupted), ignore_mismatch=True)
        self.assertTrue(decompressed)  # decompress returns bytes even if size mismatch ignored

    def test_empty_data(self):
        data = b""
        compressed = compress(data)
        decompressed = decompress(compressed)
        self.assertEqual(decompressed, data)

    def test_large_data(self):
        data = b"A" * 10_000
        compressed = compress(data)
        decompressed = decompress(compressed)
        self.assertEqual(decompressed, data)


if __name__ == "__main__":
    # python -m unittest
    unittest.main()
