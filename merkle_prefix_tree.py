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

    def __init__(self, height, hash_func=None, serialize_func=None):
        self.root_node = InteriorNode()
        self.height = height
        self.hash_func = hash_func if hash_func else self.default_hash_func
        self.serialize_func = serialize_func if serialize_func else self.json_serialize
        self.empty_tree_hash_dict = self._precompute_empty_hashes()

    def _precompute_empty_hashes(self):
        k_empty = bin(0)    # k_empty is used in the calculation of an EmptyNode that doesn't exist yet
        curr_hash = self.hash_func(k_empty)
        hash_dict = {self.height: curr_hash}    # Init hash_dict with the leaf EmptyNode
        for i in range(self.height):
            curr_hash = self.hash_func(curr_hash + curr_hash)
            curr_height = self.height - i - 1   # Traversing the tree down up when calculating these hashes
            hash_dict[curr_height] = curr_hash
        self.root_node.hash = curr_hash     # When the tree is empty, the root will have an empty hash
        return hash_dict

    def get_root_hash(self):
        return self.root_node.hash

    def get_data_node(self, prefix):
        if len(prefix) != self.height:
            raise Exception('invalid prefix length. Must be length of ' + str(self.height))
        curr_node = self.root_node
        for bit in prefix:
            curr_node = curr_node.left if bit == '0' else curr_node.right

            # Return None when the data_node is not found
            if curr_node is None:
                return None
        return curr_node

    def append(self, prefix, to_append):
        new_data_node = DataNode(prefix[-1], to_append, self.hash_func, self.serialize_func)
        curr_node = self.root_node
        # Add nodes to the tree
        for i in range(self.height):
            bit = prefix[i] # Find the next bit of the prefix on the path within the tree
            prev_node = curr_node
            curr_node = curr_node.left if bit == '0' else curr_node.right

            # If the next node in prefix doesn't exist create new InteriorNode or add DataNode
            if not curr_node:
                new_node = InteriorNode(bit) if i < self.height - 1 else new_data_node
                new_node.parent = prev_node
                if bit == '0':
                    new_node.parent.left = new_node
                elif bit == '1':
                    new_node.parent.right = new_node
                else:
                    raise Exception('invalid prefix:' + prefix)
                curr_node = new_node

        # Update the hashes of the impacted nodes
        self.rehash(curr_node)
    
    def rehash(self, leaf_node):
        """Re-hashes the hashes of the nodes on the path 
        from the given leaf_node to the root of the tree.
        """

        if not isinstance(leaf_node, DataNode):
            raise Exception('cannot re_hash. leaf_node is not DataNode')
        curr_node = leaf_node
        for i in range(self.height - 1, -1, -1):
            curr_node = curr_node.parent
            empty_tree_hash = self.empty_tree_hash_dict[i + 1]
            left_hash = curr_node.left.hash if curr_node.left else empty_tree_hash
            right_hash = curr_node.right.hash if curr_node.right else empty_tree_hash
            curr_node.hash = self.hash_hashes(left_hash, right_hash, self.hash_func)

    def produce_inclusion_proof(self, prefix):
        curr_node = self.root_node
        inclusion_proof = []
        for i in range(self.height):
            bit = prefix[i]
            opp_node = curr_node.right if bit == '0' else curr_node.left
            curr_node = curr_node.left if bit == '0' else curr_node.right

            # Return empty list when data node is not included in tree
            if not curr_node:
                return []
            empty_tree_hash = self.empty_tree_hash_dict[i + 1]
            new_proof_hash = opp_node.hash if opp_node else empty_tree_hash
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
        curr_node = self.curr_node

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
        recurse_tree(curr_node)

    def get_prefix_path_lst(self, prefix):
        curr_node = self.root_node
        path_lst = [str(curr_node)]
        for bit in prefix:
            curr_node = curr_node.left if bit == '0' else curr_node.right
            path_lst.append(str(curr_node))
        return path_lst

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