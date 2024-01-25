import logging
import os
import shutil
import unittest

from pyBIG import Archive, LargeArchive

logging.basicConfig(level=logging.INFO)

TEST_FILE = "data\\ini\\weapon.ini"
TEST_CONTENT = "john"
TEST_ENCODING = "latin-1"
TEST_ARCHIVE = "test_data/empty_archive.big"


class BaseTestCases:
    class BaseTest(unittest.TestCase):
        def test_decode(self):
            contents = self.archive.read_file(TEST_FILE)

            with open("test_data/weapon.ini", "rb") as f:
                self.assertEqual(f.read(), contents)

            self.assertEqual(len(self.archive.entries), 1236)

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
            self.archive.add_file(f"{TEST_FILE}.inc", TEST_CONTENT.encode(TEST_ENCODING))
            self.archive.repack()

            contents = self.archive.read_file(f"{TEST_FILE}.inc").decode(TEST_ENCODING)

            self.assertEqual(contents, TEST_CONTENT)

        def test_extract_and_load(self):
            self.archive.extract("test_data/output")
            self.assertTrue(os.path.exists("test_data/output/data/ini/weapon.ini"))

            new_archive = Archive.from_directory("test_data/output")
            self.assertIn(TEST_FILE, new_archive.entries)

            new_archive.save("test_data/output/test.big")
            self.assertTrue(os.path.exists("test_data/output/test.big"))

            shutil.rmtree("test_data/output/data")
            os.remove("test_data/output/test.big")

        def test_utils(self):
            self.archive.file_list()


class TestArchive(BaseTestCases.BaseTest):
    def setUp(self):
        with open("test_data/__edain_data.big", "rb") as f:
            self.archive = Archive(f.read())

    def test_empty_archive(self):
        archive = Archive.empty()
        archive.add_file(f"{TEST_FILE}.inc", TEST_CONTENT.encode(TEST_ENCODING))
        archive.repack()

        self.assertIn(f"{TEST_FILE}.inc", archive.entries)


class TestLargeArchive(BaseTestCases.BaseTest):
    def setUp(self):
        self.archive = LargeArchive("test_data/__edain_data.big")

        if self.archive.file_exists(f"{TEST_FILE}.inc"):
            self.archive.remove_file(f"{TEST_FILE}.inc")

        if not self.archive.file_exists(TEST_FILE):
            with open("test_data/weapon.ini", "rb") as f:
                self.archive.add_file(TEST_FILE, f.read())

        self.archive.repack()

    def test_empty_archive(self):
        archive = LargeArchive.empty(TEST_ARCHIVE)
        archive.add_file(f"{TEST_FILE}.inc", TEST_CONTENT.encode(TEST_ENCODING))
        archive.repack()

        self.assertIn(f"{TEST_FILE}.inc", archive.entries)
        os.remove(TEST_ARCHIVE)


if __name__ == "__main__":
    # python -m unittest
    unittest.main()
