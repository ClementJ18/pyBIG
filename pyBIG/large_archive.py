import os
import shutil
from .base_archive import BaseArchive
import logging
import struct
from .base_archive import Entry, FileAction
import tempfile


class LargeArchive(BaseArchive):
    """If an archive is too large to load into memory, you can instead use this class. It expects a file path
    rather than raw bytes and doesn't store the entire file into memory. Rather it simply reads the headers
    to obtain the list file and then stream data from the file when it needs to. Packing a file automatically
    saves it and overwrites the existing file.

    TODO: Additionally, this class can be used to construct and archive from a large directory.

    Params
    -------
    file_path : str
        The path to the archive.
    """

    def __init__(self, file_path: str, *, entries=None):
        self.file_path = file_path
        self.modified_entries = {}

        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} not found")

        if entries is None:
            with open(self.file_path, "rb") as f:
                self.entries = self._unpack(f)
        else:
            self.entries = entries

    def __repr__(self):
        return f"< LargeArchive path={self.file_path} entries={len(self.entries)} dirty={bool(self.modified_entries)}"

    def _pack(self):
        """Rewrite the archive with the modifications stores
        in self.modified_entries."""
        binary, total_size, file_count = self._create_file_list()

        with tempfile.NamedTemporaryFile(delete=False) as fp:
            self.entries = self._pack_file_list(fp, binary, total_size, file_count)
            name = fp.name

        shutil.move(name, self.file_path)
        self.modified_entries = {}

    def _pack_file_list(self, archive, binary, total_size, file_count):
        """Index the files and append the raw data to create a complete archive"""
        entries = {}

        # header, charstring, 4 bytes - always BIG4 or something similiar
        header = "BIG4"
        archive.write(struct.pack("4s", header.encode("utf-8")))

        # https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        # /* 8 bytes for every entry + 20 at the start and end. */
        first_entry = (len(binary) * 8) + 20

        for file in binary:
            first_entry += len(file[0]) + 1

        # total file size, unsigned integer, 4 bytes, little endian byte order
        size = total_size + first_entry + 1
        logging.info(f"size: {size}")
        archive.write(struct.pack("<I", size))

        # number of embedded files, unsigned integer, 4 bytes, big endian byte order
        logging.info(f"entry count: {file_count}")
        archive.write(struct.pack(">I", file_count))

        # total size of index table in bytes, unsigned integer, 4 bytes, big endian byte order
        logging.info(f"index size: {first_entry}")
        archive.write(struct.pack(">I", first_entry))

        position = 1

        logging.info("packing files...")
        for file in binary:
            # position of embedded file within BIG-file, unsigned integer, 4 bytes, big endian byte order
            # size of embedded data, unsigned integer, 4 bytes, big endian byte order
            pos_size = struct.pack(">II", first_entry + position, file[1])

            # file name, cstring, ends with null byte
            name = file[0].encode("latin-1") + b"\x00"
            packed_name = struct.pack(f"{len(name)}s", name)
            archive.write(pos_size + packed_name)
            entries[file[0]] = Entry(file[0], first_entry + position, file[1])

            position += file[1]

        # not sure what's this but I think we need it see:
        # https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        archive.write(b"L253")
        archive.write(b"\0")

        # raw file data at the positions specified in the index
        for file in binary:
            archive.write(self.read_file(file[0]))

        logging.debug("DONE")

        return entries

    @staticmethod
    def _create_file_list_from_directory(path):
        # TODO: Fix this
        """Gather the necessary information on each file in the directory to
        prepare for packing."""
        binary_files = []
        file_count = 0
        total_size = 0

        for dir_name, _, file_list in os.walk(path):
            for filename in file_list:
                file_path = os.path.join(dir_name, filename)
                name = file_path.replace(path, "")[1:].replace("/", "\\")

                with open(file_path, "rb") as f:
                    contents = f.read()
                    size = len(contents)

                logging.debug(f"name: {name}")
                logging.debug("position: ???")
                logging.debug(f"file size: {size}")
                binary_files.append((name, size, contents))

                file_count += 1
                total_size += size

        binary_files.sort(key=lambda x: x[0])
        return binary_files, total_size, file_count

    def _create_file_list(self):
        """Re-gather the necessary information on each file in the archive
        while taking into account the modifications made by the user since
        then.
        """
        binary_files = []
        file_count = 0
        total_size = 0

        for name in self.entries:
            if name in self.modified_entries:
                entry = self.modified_entries[name]
                entry_bytes = entry.content

                if entry.action is FileAction.REMOVE:
                    logging.info(f"removing {name}")
                    continue

                logging.info(f"editing {name}")
            else:
                entry = self.entries[name]
                entry_bytes = self._get_file(name)

            binary_files.append((entry.name, len(entry_bytes)))
            file_count += 1
            total_size += len(entry_bytes)

        for entry in [x for x in self.modified_entries.values() if x.action is FileAction.ADD]:
            logging.info(f"adding {entry.name}")
            entry_bytes = entry.content
            binary_files.append((entry.name, len(entry_bytes)))
            file_count += 1
            total_size += len(entry_bytes)

        binary_files.sort(key=lambda x: x[0])
        return binary_files, total_size, file_count

    def _get_file(self, name: str) -> bytes:
        """Get the contents of a specific file in the big based on file name"""
        entry = self.entries[name]
        with open(self.file_path, "rb") as f:
            f.seek(entry.position)
            return f.read(entry.size)

    def save(self, path: str):
        """Save the archive to a file.

        Params
        -------
        path : str
            The path to save to. Something like 'path/to/file/test.big'
        """
        self._pack()

    @classmethod
    def from_directory(cls, path: str, file_path: str) -> "LargeArchive":
        """Generate a BIG archive from a directory. This is useful for
        compiling an archive without adding each file manually. You simply
        give the top level directory and every file will be added recursively.

        Params
        -------
        path : str
            Path to the top level folder of the files you wish to compile
        file_path : str
            Path to save the new archive

        Returns
        --------
        Archive
            Compiled archived
        """
        binary_files, total_size, file_count = cls._create_file_list_from_directory(path)
        entries = cls._pack_file_list_from_directory(binary_files, total_size, file_count)

        return cls(file_path, entries=entries)

    @classmethod
    def empty(cls, file_path):
        """Generate an empty archive.

        Params
        -------
        file_path : str
            Path to save the archive to once it becomes used.

        """
        if os.path.exists(file_path):
            raise ValueError(f"File {file_path} already exists.")

        with open(file_path, "wb") as f:
            f.write(b"")

        return cls(file_path, entries={})
