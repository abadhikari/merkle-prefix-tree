#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a Merkle Prefix Tree, a variation of the Merkle Tree.

Properties of a Merkle Prefix Tree:
    1) The height of a Merkle Prefix Tree is fixed from when it is
        first created
    2) When an element is appended to the tree, a prefix is needed
        to specify the path where the element will be appended as a
        leaf DataNode
    3) Prefixes are strings that only contain either a 0 or 1
        character. A 0 corresponds to a left subtree and a 1
        corresponds to a right subtree
    4) The length of a prefix must be equivalent to the height of the tree
    5) When appending an element to the tree, InteriorNodes are created as
        needed until the height of the tree is reached and the leaf DataNode
        is appended
    6) Since InteriorNodes are added only as needed, large amounts of the
        tree will contain EmptyNodes. These EmptyNodes are purely conceptual,
        meaning there aren't concrete nodes that are created for EmptyNodes.
        To do hash calculations with EmptyNodes, the _empty_tree_hash_dict
        dictionary is used. This contains precomputed hash values of the
        EmptyNodes at the various levels of the tree from the root to the
        height of the tree based on an empty tree.

There are three types of nodes within the tree:
    1) InteriorNode
        a) Hash Equation: h_interior = H(h_child.0 || h_child.1)
        b) Only created when leaf DataNodes are being appended
    2) DataNode
        a) Hash Equation: h_data = H(data)
        b) Leaf nodes that will always have a depth of the height of the tree
    3) EmptyNode
        a) Hash Equation: h_empty = H(k_empty)
        b) Conceptual nodes that will theoretically compose a majority
            of the tree
"""

import json
import hashlib

from .nodes import InteriorNode, DataNode
from .exceptions import AppendOnlyError


class MerklePrefixTree:
    """Representation of a Merkle Prefix Tree."""

    def __init__(self,
                 height,
                 append_only=False,
                 hash_func=None,
                 serialize_func=None):
        """Construct a MerklePrefixTree with the given or default attributes.

        Args:
            height: The maximum height of the merkle prefix tree.
            append_only: The boolean that determines if the tree is
                append-only or not.
            hash_func: The hash function used to do any hash calculations.
            serialize_func: The serialze function used to do any
                serialization.

        Raises:
            ValueError: If height of tree is less than 1.
        """
        self._height = height

        # Verify that height of tree is greater than 0
        if height < 1:
            error_msg = 'invalid height of tree. Height must be greater than 0'
            raise ValueError(error_msg)

        self._append_only = append_only
        self._hash_func = hash_func if hash_func else self.default_hash_func
        self._serialize_func = serialize_func if serialize_func else self.default_serialize_func

        self._root_node = InteriorNode()
        self._empty_tree_hash_dict = self._precompute_empty_hashes()

    def _precompute_empty_hashes(self):
        """Precompute hashes of theoretical empty nodes at each level in tree.

        Returns:
            hash_dict: A dictionary that contains the theorical hash of a
                subtree.
            that contains strictly empty nodes at each level within the tree.
        """
        # k_empty is used in the calculation of an EmptyNode
        k_empty = bin(0)
        curr_hash = self._hash_func(k_empty)

        # Init hash_dict with the leaf EmptyNode
        hash_dict = {self._height: curr_hash}
        for i in range(self._height):
            curr_hash = self._hash_func(curr_hash + curr_hash)

            # Traversing the tree down up when calculating these hashes
            curr_height = self._height - i - 1
            hash_dict[curr_height] = curr_hash

        # When the tree is empty, the root will have an empty hash
        self._root_node.hash = curr_hash
        return hash_dict

    def get_root_hash(self):
        """Return the hash of the root_node of the MerklePrefixTree.

        Returns:
            A bytes object.
        """
        return self._root_node.hash

    def get_data_node(self, prefix):
        """Return the DataNode at the given prefix within the tree.

        Args:
            prefix: A string of 0's and 1's that maps to a leaf in the tree.

        Returns:
            curr_node: A DataNode object or None if DataNode that corresponds
                to the prefix doesn't exist yet.

        Raises:
            ValueError: If length of prefix is not equivalent to height of
                the tree or prefix contains characters not in the set
                {'0', '1'}.
        """
        self._verify_prefix(prefix)

        # Traverse the tree following the prefix bit by bit
        curr_node = self._root_node
        for bit in prefix:
            curr_node = curr_node.left if bit == '0' else curr_node.right

            # Return None when the data_node is not found
            if curr_node is None:
                return None
        return curr_node

    def append(self, prefix, to_append):
        """Append the DataNode to_append to the tree at the given prefix.

        Args:
            prefix: A string of 0's and 1's that maps to a leaf in the tree.
            to_append: The object that will be appended to the tree at the
            given prefix.

        Raises:
            ValueError: If length of prefix is not equivalent to height of
                the tree or prefix contains characters not in the set
                {'0', '1'}.
            AppendOnlyError: If trying to append to existing prefix when
                append_only instance variable is set to True.
        """
        self._verify_prefix(prefix)

        # Create the new DataNode that will be appended
        new_data_node = DataNode(prefix[-1],
                                 to_append,
                                 self._hash_func,
                                 self._serialize_func)

        # Add nodes to the tree
        curr_node = self._root_node
        for i in range(self._height):

            # Find the next bit of the prefix on the path within the tree
            bit = prefix[i]
            prev_node = curr_node
            curr_node = curr_node.left if bit == '0' else curr_node.right

            # Set the parent and the parent's left and right node pointers
            new_node = InteriorNode(bit)
            if i == self._height - 1:
                new_node = new_data_node
            new_node.parent = prev_node
            if bit == '0':
                new_node.parent.left = new_node
            else:
                new_node.parent.right = new_node

            # Add node depending on the current level within the tree
            if i < self._height - 1:
                if not curr_node:
                    curr_node = new_node
            else:
                if not self._append_only:
                    curr_node = new_node
                else:
                    error_msg = ("cannot append because DataNode"
                                 "already exists at prefix. Tree"
                                 "is append_only")
                    raise AppendOnlyError(error_msg)

        # Update the hashes of the impacted nodes
        self._rehash(curr_node)
    
    def _verify_prefix(self, prefix):
        """Verify if prefix is valid length and contains valid character.
        
        A valid prefix will have a length that is equivalent to the height
        of the tree. A valid prefix will also only have characters in the
        set {'0', '1'}.

        Args:
            prefix: A string of 0's and 1's that maps to a leaf in the tree.

        ValueError: If length of prefix is not equivalent to height of
            the tree or prefix contains characters not in the set
            {'0', '1'}.
        """
        if len(prefix) != self._height:
            height = str(self._height)
            error_msg = 'invalid prefix length. Must be length of ' + height
            raise ValueError(error_msg)
        
        # Iterate through prefix and verify that it only contains valid chars
        for char in prefix:
            if char not in ('0', '1'):
                error_msg = ('invalid prefix: ' + prefix +
                             '. Permitted characters are in set {0, 1}')
                raise ValueError(error_msg)

    def _rehash(self, leaf_node):
        """Rehash the hashes of the nodes from leaf_node to root_node.

        Starting at the leaf_node, the rehash function will travel
        up the tree by looking at each node's parent. Each parent
        node that is visited will recalculate its hash with the new
        children node hash values.

        Args:
            leaf_node: The leaf node that the rehashing to the root will begin.

        Raises:
            TypeError: If leaf_node is not of type DataNode.
        """
        if not isinstance(leaf_node, DataNode):
            raise TypeError('cannot re_hash. leaf_node is not a DataNode')

        curr_node = leaf_node
        for i in range(self._height - 1, -1, -1):
            curr_node = curr_node.parent
            empty_hash = self._empty_tree_hash_dict[i + 1]

            # Using left and right node hash, recompute the hash of curr_node
            left_hash = curr_node.left.hash if curr_node.left else empty_hash
            right_hash = curr_node.right.hash if curr_node.right else empty_hash
            curr_node.hash = self._hash_hashes(left_hash,
                                              right_hash,
                                              self._hash_func)

    def produce_inclusion_proof(self, prefix):
        """Produce proof that DataNode at prefix is included within the tree.

        As this method travels down the tree using the given prefix, the hash
        of the opposite node to the one that will be traversed is added to
        the inclusion proof.

        Example: When we traverse down the tree to the the left node because
        the bit is 0, the right node's hash is added to the proof of inclusion.

        Args:
            prefix: A string of 0's and 1's that maps to a leaf in the tree.

        Returns:
            inclusion_proof: A list of hashes of the nodes along the path from
                the given DataNode (DataNode hash not included) that
                corresponds to the prefix to the root_node of the tree.

        ValueError: If length of prefix is not equivalent to height of
            the tree or prefix contains characters not in the set
            {'0', '1'}.
        """
        self._verify_prefix(prefix)

        curr_node = self._root_node
        inclusion_proof = []
        for i in range(self._height):
            bit = prefix[i]
            opp_node = curr_node.right if bit == '0' else curr_node.left
            curr_node = curr_node.left if bit == '0' else curr_node.right

            # Return empty list when data node is not included in tree
            if not curr_node:
                return []
            empty_tree_hash = self._empty_tree_hash_dict[i + 1]
            new_proof_hash = opp_node.hash if opp_node else empty_tree_hash
            inclusion_proof.append(new_proof_hash)
        return inclusion_proof

    def validate_inclusion_proof(self,
                                 prefix,
                                 inclusion_proof,
                                 included_hash,
                                 root_hash):
        """Validate a given proof of inclusion using inputs.

        The hashes of the inclusion proof along with the included_hash are
        used to calculate the hash of the root_node that the proof of
        inclusion was generated in. If this calculated root hash is
        equivalent to the given root_hash, then the proof of inclusion
        is valid, otherwise it is not.

        Args:
            prefix: A string of 0's and 1's that maps to a leaf in the tree.
            inclusion_proof: A list of hashes of the nodes along the path
                from the given DataNode (DataNode hash not included) that
                corresponds to the prefix to the root_node of the tree.
            included_hash: A bytes object that contains the hash of the
                DataNode that the inclusion_proof is trying to prove
                is within the tree.
            root_hash: A bytes object that contains the hash of the root_node
                of the tree that the proof of inclusion is generated from.

        Returns:
            A boolean that confirms if the given proof of inclusion is valid
                or not.

        ValueError: If length of prefix is not equivalent to height of
            the tree or prefix contains characters not in the set
            {'0', '1'}.
        """
        self._verify_prefix(prefix)

        calculated_hash = included_hash
        for i in range(len(inclusion_proof) - 1, -1, -1):
            bit = prefix[i]
            left_hash = calculated_hash if bit == '0' else inclusion_proof[i]
            right_hash = calculated_hash if bit == '1' else inclusion_proof[i]
            calculated_hash = self._hash_hashes(left_hash,
                                          right_hash,
                                          self._hash_func)
        return calculated_hash == root_hash

    def pretty_print(self):
        """Recursively traverse the tree and pretty-print the node hashes.

        When pretty-printing the tree, the levels and distinction between
        left and right subtree are clearly seen through the use of '├── '
        for left subtrees and '└── ' for right subtrees.
        """
        curr_node = self._root_node

        def recurse_tree(root,
                         level=0,
                         subtree=None,
                         prefix_print=''):
            level_divider = ''
            if subtree == 'l':
                level_divider = prefix_print + '├── '
                prefix_print += '|   '
            elif subtree == 'r':
                level_divider = prefix_print + '└── '
                prefix_print += '    '
            if not root:
                if level <= self._height:
                    empty_hash = str(self._empty_tree_hash_dict[level])
                    print(level_divider + empty_hash)
                return
            print(level_divider + str(root.hash))
            recurse_tree(root.left, level + 1, 'l', prefix_print)
            recurse_tree(root.right, level + 1, 'r', prefix_print)
        recurse_tree(curr_node)

    def get_prefix_path_lst(self, prefix):
        """Return a list of nodes on the path corresponding to the prefix.

        Method used for debugging purposes.

        Args:
            prefix: A string of 0's and 1's that maps to a leaf in the tree.

        Returns:
            path_lst: A list of InteriorNodes and one leaf DataNode.

        ValueError: If length of prefix is not equivalent to height of
            the tree or prefix contains characters not in the set
            {'0', '1'}.
        """
        self._verify_prefix(prefix)

        curr_node = self._root_node
        path_lst = [curr_node]
        for bit in prefix:
            curr_node = curr_node.left if bit == '0' else curr_node.right
            path_lst.append(curr_node)
        return path_lst

    def get_tree_height(self):
        """Return the height of the MerklePrefixTree."""
        return self._height

    def get_hash_func(self):
        """Return the hash function that is currently used."""
        return self._hash_func

    def get_serialize_func(self):
        """Return the serialize function that is currently used."""
        return self._serialize_func

    def is_append_only(self):
        """Return if MerklePrefixTree is append_only or not."""
        return self._append_only

    def _hash_hashes(self,
                    hash_1,
                    hash_2,
                    hash_func):
        """Concat two given hashes and hash the result using the hash_func.

        When the hashes are concatenated, hash_1 is on the left and hash_2 is
        on the right.

        Args:
            hash_1: The first hash value.
            hash_2: The second hash value.
            hash_func: The hash function used to do any hash calculations.

        Returns:
            A bytes object that contains the hash of the concatenated hashes.
        """
        concat_hash = hash_1 + hash_2
        return hash_func(concat_hash)

    @staticmethod
    def default_hash_func(to_hash):
        """Hash the given to_hash input.

        Before hashing, the input to_hash is encoded. This default function
        uses utf-8 and sha256 hash.

        Args:
            to_hash: Any object that will be hashed.

        Returns:
            digest: A bytes object that contains the hash of to_hash.
        """

        def encode(to_encode,
                   encoding='utf-8',
                   errors='strict'):
            if isinstance(to_encode, str):
                return to_encode.encode(encoding, errors)
            return to_encode

        def sha256(to_hash):
            new_hash = hashlib.sha256()
            new_hash.update(to_hash)
            return new_hash.digest()
        to_hash = encode(to_hash)
        digest = sha256(to_hash)
        return digest

    @staticmethod
    def default_serialize_func(to_serialize):
        """Serialize the to_serialize input using json.

        Args:
            to_serialize: Any object that will be serialized.

        Returns:
            A string of the serialized data.
        """
        if not isinstance(to_serialize, str):
            return json.dumps(to_serialize, default=lambda obj: obj.__dict__)
        return to_serialize
