from collections import namedtuple
import os
import struct
import io
import json
import logging

from decoder import Decoder

#https://opensage.readthedocs.io/file-formats/big/index.html

class Encoder:
    def __init__(self, directory):
        self.directory = directory

    def pack(self, filename, file_restrictions):
        offset = 0
        f = open(f"output/{filename}", "wb")

        logging.debug(f"Processing {filename}")

        if file_restrictions:
            with open("tree.json", "r") as tree:
                file_list = json.load(tree)[filename]
                # logging.debug(file_list)

        #header, charstring, 4 bytes - always BIG4 or something similiar
        header = "BIG4"
        f.write(struct.pack("4s", header.encode("utf-8")))
        offset += 4


        binary, total_size, file_count = self.dir_to_binary(self.directory, file_list)

        #https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        #/* 8 bytes for every entry + 20 at the start and end. */
        first_entry = (len(binary) * 8) + 20

        for file in binary:
            if file["name"] not in file_list:
                continue

            first_entry += len(file["name"]) + 1

        #total file size, unsigned integer, 4 bytes, little endian byte order
        size = total_size + first_entry + 1
        logging.debug(f"size: {size}")
        f.write(struct.pack("<I", size))
        offset += 4

        #number of embedded files, unsigned integer, 4 bytes, big endian byte order
        logging.debug(f"entry count: {file_count}")
        f.write(struct.pack(">I", file_count))
        offset += 4

        # total size of index table in bytes, unsigned integer, 4 bytes, big endian byte order
        logging.debug(f"index size: {first_entry}")
        f.write(struct.pack(">I", first_entry))
        offset += 4

        raw_data = b""
        position = 1

        for file in binary:
            # position of embedded file within BIG-file, unsigned integer, 4 bytes, big endian byte order
            # size of embedded data, unsigned integer, 4 bytes, big endian byte order
            f.write(struct.pack(">II", first_entry + position, file["size"]))

            # file name, cstring, ends with null byte
            name = file["name"].encode("latin-1") + b"\x00"
            f.write(struct.pack(f"{len(name)}s", name))


            with open(file["path"], "rb") as b:
                raw_data += b.read()

            position += file["size"]

        #not sure what's this but I think we need it see:
        #https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        f.write(b"L253")
        f.write(b"\0")

        # raw file data at the positions specified in the index
        f.write(raw_data)
        f.close()
        logging.debug("DONE")


    def dir_to_binary(self, directory, restricted_files):
        binary_files = []
        file_count = 0
        total_size = 0

        for dir_name, sub_dir_list, file_list in os.walk(directory):
            for filename in file_list:
                complete_name = f'{dir_name}\\{filename}'
                sage_name = complete_name.replace(f"{directory}\\", "", 1)
                if os.path.normpath(sage_name) not in restricted_files and restricted_files:
                    continue

                size = os.path.getsize(complete_name)

                logging.debug(f"name: {complete_name}")
                logging.debug(f"position: ???")
                logging.debug(f"file size: {size}")
                binary_files.append({
                    "name": sage_name,
                    "size": size,
                    "path": complete_name,
                })

                file_count += 1
                total_size += size

        binary_files.sort(key=lambda x: x["name"])

        return binary_files, total_size, file_count

if __name__ == '__main__':
    file_name = "__edain_data.big"

    logging.basicConfig(level=logging.DEBUG)
    enc = Encoder("extract")
    enc.pack(file_name, True)

    # dec = Decoder(f"output/{file_name}")
    # dec.unpack()
    # dec.close()
