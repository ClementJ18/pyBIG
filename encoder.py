from collections import namedtuple
import os
import struct
import io
import json
import logging

from decoder import Decoder

class Encoder:
    def __init__(self, directory):
        self.directory = directory

    def pack(self, filename, file_restrictions):
        offset = 0
        f = open(f"output/{filename}", "wb")

        if file_restrictions:
            with open("tree.json", "r") as tree:
                file_list = json.load(tree)[filename]
                # logging.debug(file_list)

        #header, charstring, 4 bytes - always BIG4 or something similiar
        header = "BIG4"
        f.write(struct.pack("4s", header.encode("utf-8")))
        offset += 4


        binary, total_size, file_count = self.dir_to_binary(self.directory, file_list)

        #total file size, unsigned integer, 4 bytes, little endian byte order
        f.write(struct.pack("<I", total_size))
        offset += 4

        #number of embedded files, unsigned integer, 4 bytes, big endian byte order
        f.write(struct.pack(">I", file_count))
        offset += 4

        # total size of index table in bytes, unsigned integer, 4 bytes, big endian byte order
        # total_size = sum([8 + len(x["name"].encode("latin-1")) for x in binary])
        index_size = 0
        for file in binary:
            if file["name"] not in file_list:
                continue

            name = file["name"].encode("latin-1") + b"\x00"

            #position and entry size
            index_size += 8
            index_size += len(struct.pack(f"{len(name)}s", name))


        f.write(struct.pack(">I", index_size))
        offset += 4
        raw_data = b""
        position = 1

        for file in binary:
            # position of embedded file within BIG-file, unsigned integer, 4 bytes, big endian byte order
            # size of embedded data, unsigned integer, 4 bytes, big endian byte order
            f.write(struct.pack(">II", offset+index_size+position, file["size"]))

            # file name, cstring, ends with null byte
            name = file["name"].encode("latin-1") + b"\x00"
            f.write(struct.pack(f"{len(name)}s", name))

            raw_data += file["binary"]

            position += file["size"]

        # raw file data at the positions specified in the index
        f.write(raw_data)
        f.close()


    def dir_to_binary(self, directory, restricted_files):
        binary_files = []
        file_count = 0
        total_size = 0

        for dir_name, sub_dir_list, file_list in os.walk(directory):
            for filename in file_list:
                complete_name = f'{dir_name}\\{filename}'
                sage_name = complete_name.replace(f"{directory}\\", "", 1)
                if os.path.normpath(sage_name) not in restricted_files and restricted_files:
                    # logging.debug(sage_name)
                    continue

                size = os.path.getsize(complete_name)

                with open(complete_name, "rb") as f:
                    binary = f.read()

                binary_files.append({
                    "name": sage_name,
                    "size": size,
                    "binary": binary,
                })

                file_count += 1
                total_size += size

        binary_files.sort(key=lambda x: x["name"])

        return binary_files, total_size, file_count

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    enc = Encoder("test")
    enc.pack("English.big", True)

    dec = Decoder("output/English.big")
    dec.unpack()
    dec.close()
