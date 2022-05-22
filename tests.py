import logging
import os
import shutil
import unittest

from pyBIG import Archive

# logging.basicConfig(level=logging.INFO)

TEST_FILE = "data\\ini\\weapon.ini"
TEST_CONTENT = "john"
TEST_ENCODING = "latin-1"

class TestArchive(unittest.TestCase):
    def setUp(self):
        with open("test_data/__edain_data.big", "rb") as f:
            self.archive = Archive(f.read())        

    def test_decode(self):
        contents = self.archive.read_file(TEST_FILE)

        with open("test_data/weapon.ini", "rb") as f:
            self.assertEqual(f.read(), contents)

        self.assertEqual(len(self.archive.entries), 1152)

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

    def test_empty_archive(self):
        archive = Archive()
        archive.add_file(f"{TEST_FILE}.inc", TEST_CONTENT.encode(TEST_ENCODING))
        archive.repack()

        self.assertIn(f"{TEST_FILE}.inc", archive.entries)


if __name__ == '__main__':
    unittest.main()
