from collections import namedtuple
import enum
import io
import logging
import os
import struct

Entry = namedtuple("Entry", "name position size")
EntryEdit = namedtuple("EntryEdit", "name action content")

class FileAction(enum.Enum):
    ADD =    0
    REMOVE = 1
    EDIT =   2

class Archive:
    def __init__(self, content: bytes, *, encoding: str ='latin-1'):
        self.archive = io.BytesIO(content)
        self.encoding = encoding

        self.header = self.archive.read(4).decode("utf-8")

        self.entries = {}
        self.modified_entries = {}

        self._unpack()

    def _unpack(self):
        """Get a list of files in the big"""
        self.entries = {}
        self.archive.seek(0)

        #header
        self.archive.read(4)

        file_size = struct.unpack("I", self.archive.read(4))[0]
        logging.info(f"size: {file_size}")
        self.archive_count, index_size = struct.unpack(">II", self.archive.read(8))
        logging.info(f"entry count: {self.archive_count}")
        logging.info(f"index size: {index_size}")

        for _ in range(self.archive_count):
            position, entry_size = struct.unpack(">II", self.archive.read(8))

            name = b""
            while True:
                n = self.archive.read(1)
                if ord(n) == 0:
                    break

                name += n
            
            name = name.decode(self.encoding)
            logging.debug(f"name: {name}")
            logging.debug(f"position: {position}")
            logging.debug(f"file size: {entry_size}")

            self.entries[name] = Entry(name, position, entry_size)

    def _pack(self):
        binary, total_size, file_count = self._create_file_list()
        self.archive = self._pack_file_list(binary, total_size, file_count)
        self.archive.seek(0)
        self.modified_entries = {}

    @staticmethod
    def _pack_file_list(binary, total_size, file_count):
        offset = 0
        archive = io.BytesIO()

        #header, charstring, 4 bytes - always BIG4 or something similiar
        header = "BIG4"
        archive.write(struct.pack("4s", header.encode("utf-8")))
        offset += 4

        #https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        #/* 8 bytes for every entry + 20 at the start and end. */
        first_entry = (len(binary) * 8) + 20

        for file in binary:
            first_entry += len(file[0]) + 1

        #total file size, unsigned integer, 4 bytes, little endian byte order
        size = total_size + first_entry + 1
        logging.info(f"size: {size}")
        archive.write(struct.pack("<I", size))
        offset += 4

        #number of embedded files, unsigned integer, 4 bytes, big endian byte order
        logging.info(f"entry count: {file_count}")
        archive.write(struct.pack(">I", file_count))
        offset += 4

        # total size of index table in bytes, unsigned integer, 4 bytes, big endian byte order
        logging.info(f"index size: {first_entry}")
        archive.write(struct.pack(">I", first_entry))
        offset += 4

        raw_data = b""
        position = 1

        logging.info("packing files...")
        for file in binary:
            # position of embedded file within BIG-file, unsigned integer, 4 bytes, big endian byte order
            # size of embedded data, unsigned integer, 4 bytes, big endian byte order
            archive.write(struct.pack(">II", first_entry + position, file[1]))

            # file name, cstring, ends with null byte
            name = file[0].encode("latin-1") + b"\x00"
            archive.write(struct.pack(f"{len(name)}s", name))
            raw_data += file[2]

            position += file[1]

        #not sure what's this but I think we need it see:
        #https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        archive.write(b"L253")
        archive.write(b"\0")

        # raw file data at the positions specified in the index
        archive.write(raw_data)
        logging.debug("DONE")

        return archive

    @staticmethod
    def _gather_directory_files(path):
        binary_files = []
        file_count = 0
        total_size = 0

        for dir_name, sub_dir_list, file_list in os.walk(path):
            for filename in file_list:
                file_path = os.path.join(dir_name, filename)
                name = file_path.replace(path, "")[1:].replace("/", "\\")

                with open(file_path, "rb") as f:
                    contents = f.read()
                    size = len(contents)


                logging.debug(f"name: {name}")
                logging.debug(f"position: ???")
                logging.debug(f"file size: {size}")
                binary_files.append((name, size, contents))

                file_count += 1
                total_size += size

        binary_files.sort(key=lambda x: x[0])
        return binary_files, total_size, file_count

    def _create_file_list(self):
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
        """Get a specific file in the big based on file name"""
        entry = self.entries[name]
        self.archive.seek(entry.position)        
        return self.archive.read(entry.size)
        

    def file_exists(self, name: str) -> bool:
        if name in self.modified_entries:
            return not self.modified_entries[name].action is FileAction.REMOVE

        return name in self.entries
    

    def read_file(self, name: str):
        if not self.file_exists(name):
            raise ValueError(f"File '{name}' does not exist.")

        if name in self.modified_entries:
            return self.modified_entries["name"].file

        return self._get_file(name)

    def add_file(self, name: str, content: bytes):
        if self.file_exists(name):
            raise ValueError(f"File '{name}' already exists.")

        if "/" in name:
            raise ValueError(f"File '{name}' cannot contain '/', use '\\' instead.")

        self.modified_entries[name] = EntryEdit(name, FileAction.ADD, content)

    def edit_file(self, name: str, content: bytes):
        if not self.file_exists(name):
            raise ValueError(f"File '{name}' does not exist.")

        self.modified_entries[name] = EntryEdit(name, FileAction.EDIT, content)

    def remove_file(self, name: str):
        if not self.file_exists(name):
            raise ValueError(f"File '{name}' does not exist.")

        self.modified_entries[name] = EntryEdit(name, FileAction.REMOVE, None)

    def extract(self, output: str):
        self._pack()
        self._unpack()
        for entry in self.entries.values():
            path = os.path.normpath(os.path.join(output, entry.name).replace("\\", "/"))
        
            # create the directories if they don't exist.
            file_dir = os.path.dirname(path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

            with open(path, "wb") as f:
                f.write(self._get_file(entry.name))

    def repack(self):
        self._pack()
        self._unpack()

    def save(self, path):
        self._pack()
        with open(path, "wb") as f:
            f.write(self.archive.getbuffer())

    @classmethod
    def from_directory(cls, path):
        binary_files, total_size, file_count = cls._gather_directory_files(path)
        archive = cls._pack_file_list(binary_files, total_size, file_count)
        archive.seek(0)

        return cls(archive.read())


