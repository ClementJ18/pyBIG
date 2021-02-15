from collections import namedtuple
import os
import struct
import io

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
        print(f"header: {header}")
        # if header != "BIGF":
            # print("Invalid file format.")
        self.entries = []

    def unpack(self):
        print(f"Processing {self.path}")
        file_size = struct.unpack("I", self.file.read(4))[0]
        print(f"size: {file_size}")
        self.file_count, index_size = struct.unpack(">II", self.file.read(8))
        print(f"entry count: {self.file_count}")
        print(f"index size: {index_size}")

        self.entries = []
        for _ in range(self.file_count):
            position, entry_size = struct.unpack(">II", self.file.read(8))

            name = ""
            while True:
                n = self.file.read(1)
                if ord(n) == 0:
                    break

                name += n.decode('latin-1')
            
            print(name)
            print(position)
            print(entry_size)
            e = Entry(name=name, position=position, size=entry_size)   
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
        #     # print(f"{path} exists. Skipping.")
        #     return
        
        # print(f"Opening {path} for writing")
        f = open(path, "wb")
        
        # print(f"Seeked to {entry.position}")
        self.file.seek(entry.position)
        
        # print("Starting data transfer")
        for _ in range(0, entry.size):
            byte = self.file.read(1)
            f.write(byte)
            
        # print(f"Wrote {entry.size} bytes")
        
        # print("Done, closing file.")
        f.close()
        
        # print()

    def get_file(self, entry):
        string = ""
        
        # print(f"Seeked to {entry.position}")
        self.file.seek(entry.position)
        
        # print("Starting data transfer")
        for _ in range(0, entry.size):
            byte = self.file.read(1)
            string += byte.decode("latin-1")
            
        # print(f"Wrote {entry.size} bytes")
        
        return string

    def extract_all(self):
        for entry in self.entries:
            self.extract(entry)

    def get_strings(self):
        self.unpack()

        entry = [entry for entry in self.entries if "lotr.str" in entry.name][0]
        file = self.get_file(entry)

        return file

if __name__ == '__main__':
    dec = Decoder("English.big", "fake_test")
    dec.unpack()
    dec.extract_all()
