#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class TreeNode:
    def __init__(self, bit):
        self.bit = bit
        self.left = None
        self.right = None
        self.parent = None
        self.hash = None
    
    def __repr__(self):
        class_name = self.__class__.__name__
        return '%s: %s: %s' % (class_name, self.bit, self.hash)


class InteriorNode(TreeNode):
    def __init__(self, bit=None):
        TreeNode.__init__(self, bit)


class DataNode(TreeNode):
    def __init__(self, bit, data, hash_func, serialize_func):
        TreeNode.__init__(self, bit)
        self.data = data
        self._hash_data(hash_func, serialize_func)

    def _hash_data(self, hash_func, serialize_func):
        serialized_data = serialize_func(self.data)
        self.hash = hash_func(serialized_data)
