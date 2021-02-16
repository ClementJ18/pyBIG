from collections import namedtuple
import os
import struct
import io
import json
import logging

"""
Based of the BIG-file decoder by aderyn@gmail.com
"""

Entry = namedtuple("Entry", "name position size")

class Decoder:
    def __init__(self, file, target_dir=None):
        self.path = file
        self.file = open(file, "rb")
        self.target_dir = target_dir

        header = self.file.read(4).decode("utf-8")
        logging.debug(f"header: {header}")
        if header != "BIG4":
            logging.error("Invalid file format.")
        self.entries = []

    def unpack(self):
        logging.debug(f"Processing {self.path}")
        file_size = struct.unpack("I", self.file.read(4))[0]
        logging.debug(f"size: {file_size}")
        self.file_count, index_size = struct.unpack(">II", self.file.read(8))
        logging.debug(f"entry count: {self.file_count}")
        logging.debug(f"index size: {index_size}")

        if file_size != os.path.getsize(self.path):
            logging.error(f"File size and actual file size do not match: {file_size} vs {os.path.getsize(self.path)}")


        self.entries = []
        for _ in range(self.file_count):
            position, entry_size = struct.unpack(">II", self.file.read(8))

            name = b""
            while True:
                n = self.file.read(1)
                if ord(n) == 0:
                    break

                name += n
            
            logging.debug(f"name: {name}")
            logging.debug(f"position: {position}")
            logging.debug(f"file size: {entry_size}")
            e = Entry(name=name.decode('latin-1'), position=position, size=entry_size)   
            self.entries.append(e)

    def extract(self, entry):
        if self.target_dir is None:
            raise ValueError
        
        path = os.path.join(self.target_dir, entry.name)
        
        # create the directories if they don't exist.
        file_dir = path[:path.rfind("\\")]
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
            
        # # skip files that already exist.
        # if os.path.exists(path):
        #     # logging.debug(f"{path} exists. Skipping.")
        #     return
        
        # logging.debug(f"Opening {path} for writing")
        f = open(path, "wb")
        
        # logging.debug(f"Seeked to {entry.position}")
        self.file.seek(entry.position)
        
        # logging.debug("Starting data transfer")
        for _ in range(0, entry.size):
            byte = self.file.read(1)
            f.write(byte)
            
        # logging.debug(f"Wrote {entry.size} bytes")
        
        logging.debug("DONE")
        f.close()
        
        # logging.debug()

    def get_file(self, entry):
        string = ""
        
        # logging.debug(f"Seeked to {entry.position}")
        self.file.seek(entry.position)
        
        # logging.debug("Starting data transfer")
        for _ in range(0, entry.size):
            byte = self.file.read(1)
            string += byte.decode("latin-1")
            
        # logging.debug(f"Wrote {entry.size} bytes")
        
        return string

    def extract_all(self):
        for entry in self.entries:
            self.extract(entry)

    def get_strings(self):
        self.unpack()

        entry = [entry for entry in self.entries if "lotr.str" in entry.name][0]
        file = self.get_file(entry)

        return file

    def generate_tree(self):
        with open("tree.json", "r") as f:
            tree = json.load(f)

        tree[self.path.split("\\")[-1]] = [x.name for x in self.entries]

        with open(f"tree.json", "w") as f:
            json.dump(tree, f, indent=4)

    def close(self):
        self.file.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    dec = Decoder("English.big", "extract")
    dec.unpack()
    # dec.extract_all()
    dec.generate_tree()
    dec.close()
