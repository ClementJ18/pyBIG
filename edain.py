from decoder import Decoder
from encoder import Encoder

import os
import json
import logging

def generate_tree(directory):
    for dir_name, sub_dir_list, file_list in os.walk(directory):
        for filename in file_list:
            complete_name = f'{dir_name}\\{filename}'

            dec = Decoder(complete_name)
            dec.unpack()
            dec.generate_tree()

def pack(directory):
    with open("tree.json", "r") as f:
        files = list(json.load(f).keys())

    enc = Encoder(directory)
    for file in files:
        enc.pack(file, True)

def unpack(directory):
    for dir_name, sub_dir_list, file_list in os.walk(directory):
        for filename in file_list:
            complete_name = f'{dir_name}\\{filename}'

            dec = Decoder(complete_name)
            dec.unpack()
            dec.extract_all()
            dec.close()

def clear_tree():
    with open("tree.json", "w") as f:
        json.dump({}, f)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # generate_tree("edain_files")

    # pack("extract")

    # unpack("edain_files")

    #clear_tree()
