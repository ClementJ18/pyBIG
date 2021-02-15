from collections import namedtuple
import os
import struct
import io

from decoder import Decoder

class Encoder:
    def __init__(self, directory):
        self.directory = directory

    def pack(self, filename):
        offset = 0
        f = open(filename, "wb")

        #header, charstring, 4 bytes - always BIG4 or something similiar
        header = "BIG4"
        f.write(struct.pack("4s", header.encode("utf-8")))
        offset += 4


        binary, total_size, file_count = self.dir_to_binary(self.directory)

        #total file size, unsigned integer, 4 bytes, little endian byte order
        f.write(struct.pack("<I", total_size))
        offset += 4

        #number of embedded files, unsigned integer, 4 bytes, big endian byte order
        f.write(struct.pack(">I", file_count))
        offset += 4

        # total size of index table in bytes, unsigned integer, 4 bytes, big endian byte order
        # total_size = sum([8 + len(x["name"].encode("latin-1")) for x in binary])
        total_size = 0
        for file in binary:
            name = file["name"].encode("latin-1") + b"\x00"

            #position and entry size
            total_size += len(struct.pack(">II", file["position"], file["size"]))
            total_size += len(struct.pack(f"{len(name)}s", name))


        f.write(struct.pack(">I", total_size))
        offset += 4
        raw_data = b""

        for file in binary:
            # position of embedded file within BIG-file, unsigned integer, 4 bytes, big endian byte order
            # size of embedded data, unsigned integer, 4 bytes, big endian byte order
            f.write(struct.pack(">II", file["position"]+total_size, file["size"]))

            # file name, cstring, ends with null byte
            name = file["name"].encode("latin-1") + b"\x00"
            f.write(struct.pack(f"{len(name)}s", name))

            raw_data += file["binary"]

        # raw file data at the positions specified in the index
        f.write(raw_data)
        f.close()


    def dir_to_binary(self, directory):
        binary_files = []
        position = 0
        file_count = 0

        for dir_name, sub_dir_list, file_list in os.walk(directory):
            for filename in file_list:
                complete_name = f'{dir_name}\\{filename}'
                size = os.path.getsize(complete_name)

                with open(complete_name, "rb") as f:
                    binary = f.read()

                binary_files.append({
                    "name": complete_name.replace(f"{directory}\\", "", 1),
                    "size": size,
                    "binary": binary,
                    "position": position
                })

                position += size
                file_count += 1


        return binary_files, position, file_count

if __name__ == '__main__':
    enc = Encoder("test")
    enc.pack("test.big")

    dec = Decoder("test.big")
    dec.unpack()
