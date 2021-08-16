#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class TreeNode:
    def __init__(self, p_bit):
        self.p_bit = p_bit
        self.left = None
        self.right = None
        self.parent = None
        self.hash = None
    
    def __repr__(self):
        class_name = self.__class__.__name__
        return f'{class_name}: {self.p_bit}: {self.hash}'


class InteriorNode(TreeNode):
    def __init__(self, p_bit=None):
        TreeNode.__init__(self, p_bit)


class DataNode(TreeNode):
    def __init__(self, p_bit, data, hash_func, serialize_func):
        TreeNode.__init__(self, p_bit)
        self.data = data
        self._hash_data(hash_func, serialize_func)

    def _hash_data(self, hash_func, serialize_func):
        serialized_data = serialize_func(self.data)
        self.hash = hash_func(serialized_data)
