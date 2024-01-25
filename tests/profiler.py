import pstats
import objsize
import pyBIG
import logging
import cProfile

logging.basicConfig(level=logging.INFO)


def speed():
    with open("test_data/__edain_data.big", "rb") as f:
        archive = pyBIG.Archive(f.read())

    archive.add_file("weapons.ini", b"")
    pr = cProfile.Profile()

    # unwrap pack
    # binary, total_size, file_count = archive._create_file_list()
    # pr.enable()
    # archive._pack_file_list(binary, total_size, file_count)
    # pr.disable()

    pr.enable()
    archive.repack()
    pr.disable()

    p = pstats.Stats(pr)
    p.sort_stats("cumulative").print_stats()


def size():
    with open("test_data/__edain_data.big", "rb") as f:
        archive = pyBIG.Archive(f.read())

    large_archive = pyBIG.LargeArchive("test_data/__edain_data.big")

    logging.info(f"Archive: {objsize.get_deep_size(archive)}")
    logging.info(f"Large Archive: {objsize.get_deep_size(large_archive)}")


if __name__ == "__main__":
    size()
    # speed()
