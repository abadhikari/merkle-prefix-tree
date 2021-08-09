#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains a Merkle Prefix Tree, a variation of the traditional
Merkle Tree. 

Properties of a Merkle Prefix Tree:
1) The height of a Merkle Prefix Tree is fixed from when it is first created
2) When an element is appended to the tree, a prefix is needed to specify 
the path where the element will be appended as a leaf DataNode
3) Prefixes are strings that only contain either a 0 or 1 character. A 0 corresponds
to a left subtree and a 1 corresponds to a right subtree
4) The length of a prefix must be equivalent to the height of the tree  
5) When appending an element to the tree, InteriorNodes are created as 
needed until the height of the tree is reached and the leaf DataNode
is appended
6) Since InteriorNodes are added only as needed, large amounts of the tree
will contain EmptyNodes. These EmptyNodes are purely conceptual, meaning there
aren't concrete nodes that are created for EmptyNodes. To do hash calculations with 
EmptyNodes, the _empty_tree_hash_dict dictionary is used. This contains
precomputed hash values of the EmptyNodes at the various levels of the tree 
from the root to the height of the tree based on an empty tree. 

There are three types of nodes within the tree:
1) InteriorNode
    a) Hash Equation: hinterior = H(hchild.0 || hchild.1)
    b) Only created when leaf DataNodes are being appended
2) DataNode
    a) Hash Equation: hdata = H(data)
    b) Leaf nodes that will always have a depth of the height of the tree
3) EmptyNode
    a) Hash Equation: hempty = H(kempty)
    b) Conceptual nodes that will compose most of the tree
"""


import json
import hashlib

from nodes import InteriorNode, DataNode


class MerklePrefixTree:

    k_empty = bin(0)  # The hash of k_empty is equal to the hash of a leaf node that doesn't exist yet

    def __init__(self, height, hash_func=None, serialize_func=None):
        self.root_node = InteriorNode()
        self.height = height
        self.hash_func = hash_func if hash_func else self.default_hash_func
        self.serialize_func = serialize_func if serialize_func else self.json_serialize
        self.empty_tree_hash_dict = self._precompute_empty_hashes()

    def _precompute_empty_hashes(self):
        hash_dict = {}
        curr_hash = None
        for i in range(self.height, -1, -1):
            curr_hash = self.hash_func(self.k_empty) if not curr_hash else self.hash_func(curr_hash + curr_hash)
            hash_dict[i] = curr_hash
        self.root_node.hash = curr_hash     # When the tree is empty, the root will have an empty hash
        return hash_dict

    def get_root_hash(self):
        return self.root_node.hash

    def get_data_node(self, prefix):
        curr_node = self.root_node
        for bit in prefix:
            curr_node = curr_node.left if bit == '0' else curr_node.right
        return curr_node

    def append(self, prefix, to_append):
        new_data_node = DataNode(to_append, self.hash_func, self.serialize_func)
        curr_node = self.root_node
        # Add nodes to the tree
        for i in range(self.height):
            bit = prefix[i]
            prev_node = curr_node
            curr_node = curr_node.left if bit == '0' else curr_node.right
            # If the next node in prefix doesn't exist
            if not curr_node:
                new_node = InteriorNode() if i < self.height - 1 else new_data_node
                new_node.parent = prev_node
                if bit == '0':
                    new_node.parent.left = new_node
                elif bit == '1':
                    new_node.parent.right = new_node
                else:
                    raise Exception('invalid prefix:' + prefix)
                curr_node = new_node

        # Update the hashes of the impacted nodes
        for i in range(self.height - 1, -1, -1):
            curr_node = curr_node.parent
            left_hash = curr_node.left.hash if curr_node.left else self.empty_tree_hash_dict[i + 1]
            right_hash = curr_node.right.hash if curr_node.right else self.empty_tree_hash_dict[i + 1]
            curr_node.hash = self.hash_hashes(left_hash, right_hash, self.hash_func)

    def produce_inclusion_proof(self, prefix):
        curr_node = self.root_node
        inclusion_proof = []
        for i in range(self.height):
            bit = prefix[i]
            opp_node = curr_node.right if bit == '0' else curr_node.left
            curr_node = curr_node.left if bit == '0' else curr_node.right
            if not curr_node:
                return []
            new_proof_hash = opp_node.hash if opp_node else self.empty_tree_hash_dict[i + 1]
            inclusion_proof.append(new_proof_hash)
        return inclusion_proof

    def validate_inclusion_proof(self, prefix, inclusion_proof, included_hash, root_hash):
        calculated_hash = included_hash
        for i in range(len(inclusion_proof) - 1, -1, -1):
            bit = prefix[i]
            left_hash = calculated_hash if bit == '0' else inclusion_proof[i]
            right_hash = calculated_hash if bit == '1' else inclusion_proof[i]
            calculated_hash = hash_hashes(left_hash, right_hash, self.hash_func)
        return calculated_hash == root_hash

    def print_tree(self):
        root_node = self.root_node

        def recurse_tree(root, level=0, subtree=None, prefix_print=''):
            level_divider = ''
            if subtree == 'l':
                level_divider = prefix_print + '├── '
                prefix_print += '|   '
            elif subtree == 'r':
                level_divider = prefix_print + '└── '
                prefix_print += '    '
            if not root:
                if level <= self.height:
                    print(level_divider + str(self.empty_tree_hash_dict[level]))
                return
            print(level_divider + str(root.hash))
            recurse_tree(root.left, level + 1, 'l', prefix_print)
            recurse_tree(root.right, level + 1, 'r', prefix_print)
        recurse_tree(root_node)

    def print_prefix_path(self, prefix):
        curr_node = self.root_node
        print('Root Node:', curr_node, ' Root Hash:', curr_node.hash)
        for bit in prefix:
            curr_node = curr_node.left if bit == '0' else curr_node.right
            print('Node:', curr_node, ' Bit:', bit, ' Hash:', curr_node.hash)

    @staticmethod
    def json_serialize(to_serialize):
        return json.dumps(to_serialize) if not isinstance(to_serialize, str) else to_serialize

    @staticmethod
    def hash_hashes(hash_1, hash_2, hash_func):
        concat_hash = hash_1 + hash_2
        return hash_func(concat_hash)

    @staticmethod
    def default_hash_func(to_hash):
        def encode(to_encode, encoding='utf-8', errors='strict'):
            return to_encode.encode(encoding, errors) if isinstance(to_encode, str) else to_encode
        def sha256(to_hash):
            new_hash = hashlib.sha256()
            new_hash.update(to_hash)
            return new_hash.digest()
        to_hash = encode(to_hash)
        digest = sha256(to_hash)
        return digest