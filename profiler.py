import pyBIG
import logging

logging.basicConfig(level=logging.INFO)

with open("__edain_data.big", "rb") as f:
    archive = pyBIG.Archive(f.read())

archive.add_file("tico.txt", b"")
archive.repack()