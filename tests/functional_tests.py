import os
from typing import Union
import unittest

from pyBIG import Archive, LargeArchive


TEST_FILE = "read_me_for_test.txt"
TEST_CONTENT = "john"
TEST_ENCODING = "latin-1"
TEST_ARCHIVE = "tests/test_data/empty_archive.big"


class BaseTestCases:
    class BaseTest(unittest.TestCase):
        archive: Union[Archive, LargeArchive]
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

            new_archive = Archive.from_directory("tests/test_data/output")
            self.assertIn(TEST_FILE, new_archive.entries)

            new_archive.save("tests/test_data/output/test.big")
            self.assertTrue(os.path.exists("tests/test_data/output/test.big"))

            os.remove(f"tests/test_data/output/{TEST_FILE}")
            os.remove("tests/test_data/output/test.big")

        def test_utils(self):
            self.archive.file_list()


class TestArchive(BaseTestCases.BaseTest):
    def setUp(self):
        with open("tests/test_data/test_big.big", "rb") as f:
            self.archive = Archive(f.read())

    def test_empty_archive(self):
        archive = Archive.empty()
        archive.add_file(TEST_FILE, TEST_CONTENT.encode(TEST_ENCODING))
        archive.repack()

        self.assertIn(TEST_FILE, archive.entries)


class TestLargeArchive(BaseTestCases.BaseTest):
    def setUp(self):
        self.archive = LargeArchive("tests/test_data/test_big.big")

        if self.archive.file_exists(TEST_FILE):
            self.archive.remove_file(TEST_FILE)

        if not self.archive.file_exists(TEST_FILE):
            with open(f"tests/test_data/{TEST_FILE}", "rb") as f:
                self.archive.add_file(TEST_FILE, f.read())

        self.archive.repack()

    def test_empty_archive(self):
        archive = LargeArchive.empty(TEST_ARCHIVE)
        archive.add_file(TEST_FILE, TEST_CONTENT.encode(TEST_ENCODING))
        archive.repack()

        self.assertIn(TEST_FILE, archive.entries)
        os.remove(TEST_ARCHIVE)


if __name__ == "__main__":
    # python -m unittest
    unittest.main()
