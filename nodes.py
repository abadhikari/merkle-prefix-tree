from utils import json_serialize


class TreeNode:
    def __init__(self):
        self.left = None
        self.right = None
        self.parent = None
        self.hash = None


class InteriorNode(TreeNode):
    def __init__(self):
        TreeNode.__init__(self)


class DataNode(TreeNode):
    def __init__(self, data, hash_func):
        TreeNode.__init__(self)
        self.data = data
        self._hash_data(hash_func)

    def _hash_data(self, hash_func):
        serialized_data = json_serialize(self.data)
        self.hash = hash_func(serialized_data)
