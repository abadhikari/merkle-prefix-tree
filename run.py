#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json

from merkle_prefix_tree import MerklePrefixTree


def encode(to_encode, encoding='utf-8', errors='strict'):
    return to_encode.encode(encoding, errors) if isinstance(to_encode, str) else to_encode


def sha256(to_hash):
    new_hash = hashlib.sha256()
    new_hash.update(to_hash)
    return new_hash.digest()


def default_hash_func(to_hash):
    to_hash = encode(to_hash)
    digest = sha256(to_hash)
    return digest

def json_serialize(to_serialize):
    return json.dumps(to_serialize, default=lambda obj: obj.__dict__) if not isinstance(to_serialize, str) else to_serialize

class RandObj:
    def __init__(self, data):
        self.data = data

class TestObj:
    def __init__(self):
        self.list = self.fill_list()
    
    def fill_list(self):
        lst = []
        for i in range(10):
            lst.append(RandObj(i))
        return lst

if __name__ == '__main__':
    m = MerklePrefixTree(4, False, default_hash_func, json_serialize)
    print(type(m.get_root_hash()))
    prefix = '0001'
    obj = TestObj()
    m.append(prefix, obj)
    poi = m.produce_inclusion_proof(prefix)
    data_node = m.get_data_node(prefix)
    m.pretty_print()
    path_lst = m.get_prefix_path_lst(prefix)
    for node in path_lst:
        print(node)

    # TODO make sure to add a serialize_func that can serialize deep objects
    #t = TestObj()
    #print(json_serialize(t))