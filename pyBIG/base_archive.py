import enum
from collections import namedtuple
from typing import Dict, List
import logging
import struct
import os


Entry = namedtuple("Entry", "name position size")
EntryEdit = namedtuple("EntryEdit", "name action content")


class FileAction(enum.Enum):
    ADD = 0
    REMOVE = 1
    EDIT = 2


class BaseArchive:
    modified_entries: Dict[str, EntryEdit]

    def _pack(self):
        """Rewrite the archive with the modifications stores
        in self.modified_entries."""

        raise NotImplementedError

    @staticmethod
    def _unpack(file):
        """Get a list of files in the big"""
        entries = {}
        file.seek(0)

        # header
        file.read(4)

        file_size = struct.unpack("I", file.read(4))[0]
        logging.info(f"size: {file_size}")
        archive_count, index_size = struct.unpack(">II", file.read(8))
        logging.info(f"entry count: {archive_count}")
        logging.info(f"index size: {index_size}")

        for _ in range(archive_count):
            position, entry_size = struct.unpack(">II", file.read(8))

            name = b""
            while True:
                n = file.read(1)
                if ord(n) == 0:
                    break

                name += n

            name = name.decode("latin-1")
            logging.debug(f"name: {name}")
            logging.debug(f"position: {position}")
            logging.debug(f"file size: {entry_size}")

            entries[name] = Entry(name, position, entry_size)

        return entries

    def file_exists(self, name: str) -> bool:
        """Check if a file exists

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini

        Returns
        --------
        bool
            True if the file exists, else false
        """
        if name in self.modified_entries:
            return self.modified_entries[name].action is not FileAction.REMOVE

        return name in self.entries

    def file_list(self) -> List[str]:
        """Return a list of files, compiling both actual files
        and new/removed files

        Returns
        --------
        List[str]
            The list of files
        """
        file_list = list(
            {
                *[
                    name
                    for name in self.entries.keys()
                    if self.modified_entries.get(name, EntryEdit(name, None, None)).action
                    is not FileAction.REMOVE
                ],
                *[
                    name
                    for name, file in self.modified_entries.items()
                    if file.action is not FileAction.REMOVE
                ],
            }
        )
        file_list.sort()

        return file_list

    def read_file(self, name: str):
        """Get the raw bytes of the file if the file exists. This method has the
        advantage over simply accessing Archive.entries that it will
        also check pending modified entries

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini

        Returns
        -------
        bytes
            File bytes

        Raises
        ------
            KeyError
                File not found
        """
        if not self.file_exists(name):
            raise KeyError(f"File '{name}' does not exist.")

        if name in self.modified_entries:
            return self.modified_entries[name].content

        return self._get_file(name)

    def add_file(self, name: str, content: bytes):
        """Mark a file to be added. This does not modify the archive itself yet.
        You need to call Archive.repack for the archive to be actually modified.
        However, the get methods of the class take in account modified entries.

        The method will not permit adding a file that already exists.

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini
        content : bytes
            File bytes to be added

        Raises
        ------
            KeyError
                File already exists
            ValueError
                File name contains forbidden characters
        """
        if self.file_exists(name):
            raise KeyError(f"File '{name}' already exists.")

        if "/" in name:
            raise ValueError(f"File '{name}' cannot contain '/', use '\\' instead.")

        self.modified_entries[name] = EntryEdit(name, FileAction.ADD, content)

    def edit_file(self, name: str, content: bytes):
        """Edit an existing file with new content. This does not actually modify
        the file yet. The method cannot edit a file that hasn't been added yet, either
        as a modified entry or already present in the archive.

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini
        content : bytes
            File bytes

        Raises
        ------
            KeyError
                File not found
        """
        if not self.file_exists(name):
            raise KeyError(f"File '{name}' does not exist.")

        self.modified_entries[name] = EntryEdit(name, FileAction.EDIT, content)

    def remove_file(self, name: str):
        """Mark as existing file for deletion. The deletion will only happen once
        the archive has been repacked.

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini

        Raises
        ------
            KeyError
                File not found
        """
        if not self.file_exists(name):
            raise KeyError(f"File '{name}' does not exist.")

        self.modified_entries[name] = EntryEdit(name, FileAction.REMOVE, None)

    def extract(self, output: str, *, files: List[str] = ()):
        """Extract the contents of the archive to a folder.

        Params
        -------
        output : str
            The folder to extract everything to
        files : Optional[List[str]]
            The list of files to extract
        """
        if not files:
            files = self.file_list()

        for name in files:
            file = self.read_file(name)
            path = os.path.normpath(os.path.join(output, name).replace("\\", "/"))

            # create the directories if they don't exist.
            file_dir = os.path.dirname(path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

            with open(path, "wb") as f:
                f.write(file)

    def repack(self):
        """Update the archive to include all the modified entries. This clears
        the list and updates the archive with the new data.
        """
        if not self.modified_entries:
            return

        self._pack()

    def save(self, path: str):
        """Save the archive to a file.

        Params
        -------
        path : str
            The path to save to. Something like 'path/to/file/test.big'
        """
        raise NotImplementedError

    @classmethod
    def from_directory(cls, path: str) -> "BaseArchive":
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
        raise NotImplementedError
