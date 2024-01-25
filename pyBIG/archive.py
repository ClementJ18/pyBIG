import io
import logging
import os
import struct

from .base_archive import BaseArchive, Entry, FileAction


class Archive(BaseArchive):
    """The core of the library, represents a BIG file and allows
    the user to mainpulate it programatically

    Params
    -------
    content : Optional[bytes]
        Raw bytes of the original big file

    """

    def __init__(self, content: bytes = b"", *, entries=None):
        self.archive = io.BytesIO(content)

        self.header = self.archive.read(4).decode("utf-8")

        self.entries = entries or {}
        self.modified_entries = {}

        if entries is None:
            self.entries = self._unpack(self.archive)

    def __repr__(self):
        return f"< Archive entries={len(self.entries)} dirty={bool(self.modified_entries)}"

    def _pack(self):
        """Rewrite the archive with the modifications stores
        in self.modified_entries."""
        binary, total_size, file_count = self._create_file_list()
        self.archive, self.entries = self._pack_file_list(binary, total_size, file_count)
        self.archive.seek(0)
        self.modified_entries = {}

    @staticmethod
    def _pack_file_list(binary, total_size, file_count):
        """Index the files and append the raw data to create a complete archive"""
        archive = io.BytesIO()
        raw_data = io.BytesIO()
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

            raw_data.write(file[2])

            entries[file[0]] = Entry(file[0], first_entry + position, file[1])

            position += file[1]

        # not sure what's this but I think we need it see:
        # https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        archive.write(b"L253")
        archive.write(b"\0")

        # raw file data at the positions specified in the index
        raw_data.seek(0)
        archive.write(raw_data.read())
        logging.debug("DONE")

        return archive, entries

    @staticmethod
    def _create_file_list_from_directory(path):
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

            binary_files.append((entry.name, len(entry_bytes), entry_bytes))
            file_count += 1
            total_size += len(entry_bytes)

        for entry in [x for x in self.modified_entries.values() if x.action is FileAction.ADD]:
            logging.info(f"adding {entry.name}")
            entry_bytes = entry.content
            binary_files.append((entry.name, len(entry_bytes), entry_bytes))
            file_count += 1
            total_size += len(entry_bytes)

        binary_files.sort(key=lambda x: x[0])
        return binary_files, total_size, file_count

    def _get_file(self, name: str) -> bytes:
        """Get the contents of a specific file in the big based on file name"""
        entry = self.entries[name]
        self.archive.seek(entry.position)
        return self.archive.read(entry.size)

    def save(self, path: str):
        """Save the archive to a file.

        Params
        -------
        path : str
            The path to save to. Something like 'path/to/file/test.big'
        """
        self._pack()
        with open(path, "wb") as f:
            f.write(self.archive.getbuffer())

    @classmethod
    def from_directory(cls, path: str) -> "Archive":
        """Generate a BIG archive from a directory. This is useful for
        compiling an archive without adding each file manually. You simply
        give the top level directory and every file will be added recursively.

        Params
        -------
        path : str
            Path to the top level folder of the files you wish to compile

        Returns
        --------
        Archive
            Compiled archived
        """
        binary_files, total_size, file_count = cls._create_file_list_from_directory(path)
        archive, entries = cls._pack_file_list(binary_files, total_size, file_count)
        archive.seek(0)

        return cls(archive.read(), entries=entries)

    @classmethod
    def empty(cls):
        """Generate an empty archive."""
        return cls(entries={})
