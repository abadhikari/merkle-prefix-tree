#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the test for the MerklePrefixTree module.

More information about the tests can be found in the docstrings
within each test method below.
"""

import pytest

from merkle_prefix_tree import MerklePrefixTree
from exceptions import AppendOnlyError


class TestMerklePrefixTree:
    """Test all the methods within the MerklePrefixTree module."""

    _test_height = 4
    _test_prefix = '0' * _test_height
    _test_to_append = 3

    @pytest.fixture
    def setup(self):
        """Create instance of MerklePrefixTree for testing purposes."""
        def _setup_merkle_prefix_tree(height,
                                      append_only=False,
                                      hash_func=None,
                                      serialize_func=None):
            return MerklePrefixTree(height,
                                    append_only,
                                    hash_func,
                                    serialize_func)
        return _setup_merkle_prefix_tree

    @pytest.mark.parametrize("height", [-1, 0])
    def test_init_height_raises_exc(self, setup, height):
        """Test invalid heights and see if exception is raised."""
        with pytest.raises(ValueError) as exc:
            setup(height)

    def test_init_default_func_args(self, setup):
        """Test default args in __init__ method and tree height."""
        tree = setup(self._test_height)

        # When args not given, verify that the default funcs are used
        assert None not in [tree._hash_func, tree._serialize_func]

        # The height of the tree excludes the root node
        assert tree.get_tree_height() == self._test_height

    def test__precompute_empty_hashes(self, setup):
        """Test if empty tree hashes are correctly computed."""
        tree = setup(self._test_height)
        empty_tree_hash_dict = tree._empty_tree_hash_dict

        # len should be _test_height + 1 since height doesn't include the root
        assert len(empty_tree_hash_dict) == self._test_height + 1

        # Compute the root hash of an empty tree
        hash_func = tree.get_hash_func()
        curr_hash = hash_func(bin(0))
        for i in range(self._test_height):
            curr_hash = hash_func(curr_hash + curr_hash)

        # Verify computed root hash is equal to empty_tree_hash_dict root hash
        assert curr_hash == empty_tree_hash_dict[0]

    def test_append_get_data_node_roundtrip(self, setup):
        """Test if rountrip of append and get_data_node functions correctly."""
        tree = setup(self._test_height)

        # Append _test_to_append to tree and retrieve it
        tree.append(self._test_prefix, self._test_to_append)
        retrieved_node = tree.get_data_node(self._test_prefix)

        # Verify that the retreived node contains _test_to_append
        assert retrieved_node.data == self._test_to_append

    def test_get_data_node_nonexisting(self, setup):
        """Test if get_data_node call for nonexisting node returns None."""
        tree = setup(self._test_height)

        # Try to retrieve a node at prefix that hasn't been appended yet
        retrieved_node = tree.get_data_node(self._test_prefix)
        assert retrieved_node is None

    def test_append_when_append_only_raises_exc(self, setup):
        """Test if append to same prefix when append_only raises exc."""
        # Set append-only to True
        tree = setup(self._test_height, True)

        # Append to same prefix twice should raise exception
        with pytest.raises(AppendOnlyError) as exc:
            tree.append(self._test_prefix, self._test_to_append)
            tree.append(self._test_prefix, self._test_to_append)

    def test_produce_inclusion_proof_validate_roundtrip(self, setup):
        """Test if rountrip of produce and validate poi functions correctly."""
        tree = setup(self._test_height)
        tree.append(self._test_prefix, self._test_to_append)

        # Prepare the inputs to validate_inclusion_proof
        poi = tree.produce_inclusion_proof(self._test_prefix)
        hash_func = tree.get_hash_func()
        serial_func = tree.get_serialize_func()
        included_hash = hash_func(serial_func(self._test_to_append))
        root_hash = tree.get_root_hash()

        # Validate the poi using above inputs
        is_valid = tree.validate_inclusion_proof(self._test_prefix,
                                                 poi,
                                                 included_hash,
                                                 root_hash)
        assert is_valid == True

    def test_produce_inclusion_proof_validate_roundtrip_fail(self,
                                                             setup):
        """Test if rountrip of produce and validate poi fails correctly."""
        tree = setup(self._test_height)

        # Prepare the inputs to validate_inclusion_proof
        poi = tree.produce_inclusion_proof(self._test_prefix)
        hash_func = tree.get_hash_func()
        serial_func = tree.get_serialize_func()
        included_hash = hash_func(serial_func(self._test_to_append))
        root_hash = tree.get_root_hash()

        # Validate the poi using above inputs
        is_valid = tree.validate_inclusion_proof(self._test_prefix,
                                                 poi,
                                                 included_hash,
                                                 root_hash)
        # Should be False since poi isn't valid
        assert is_valid == False

    def test_produce_inclusion_proof_empty_proof(self, setup):
        """Test if invalid produce poi call results in empty poi."""
        tree = setup(self._test_height)

        # Produce poi of prefix that doesn't currently exist
        poi = tree.produce_inclusion_proof(self._test_prefix)

        # poi should be empty list
        assert poi == []

    @pytest.mark.parametrize("prefix", [_test_prefix * (_test_height - 1),
                                        _test_prefix * (_test_height + 1),
                                        'a' * _test_height])
    def test_produce_inclusion_proof_prefix_raises_exc(self, setup, prefix):
        """Test if invalid prefix raises exception."""
        tree = setup(self._test_height)

        # Incorrect prefix lens or incorrect chars will raise exception
        with pytest.raises(ValueError) as exc:
            tree.produce_inclusion_proof(prefix)

    @pytest.mark.parametrize("prefix", [_test_prefix * (_test_height - 1),
                                        _test_prefix * (_test_height + 1),
                                        'a' * _test_height])
    def test_get_data_node_prefix_raises_exc(self, setup, prefix):
        """Test if invalid prefix raises exception."""
        tree = setup(self._test_height)

        # Incorrect prefix lens or incorrect chars will raise exception
        with pytest.raises(ValueError) as exc:
            tree.get_data_node(prefix)

    @pytest.mark.parametrize("prefix", [_test_prefix * (_test_height - 1),
                                        _test_prefix * (_test_height + 1),
                                        'a' * _test_height])
    def test_append_prefix_raises_exc(self, setup, prefix):
        """Test if invalid prefix raises exception."""
        tree = setup(self._test_height)

        # Incorrect prefix lens or incorrect chars will raise exception
        with pytest.raises(ValueError) as exc:
            tree.append(prefix, self._test_to_append)
