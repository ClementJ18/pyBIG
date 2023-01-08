import pstats
import pyBIG
import logging
import cProfile

logging.basicConfig(level=logging.INFO)

with open("__edain_data.big", "rb") as f:
    archive = pyBIG.Archive(f.read())

archive.add_file("tico.txt", b"")
pr = cProfile.Profile()

#unwrap pack
# binary, total_size, file_count = archive._create_file_list()
# pr.enable()
# archive._pack_file_list(binary, total_size, file_count)
# pr.disable()

pr.enable()
archive.repack()
pr.disable()

p = pstats.Stats(pr)
p.sort_stats('cumulative').print_stats()
