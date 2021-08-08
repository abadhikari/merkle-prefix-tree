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
    def __init__(self, data, hash_func, serialize_func):
        TreeNode.__init__(self)
        self.data = data
        self._hash_data(hash_func, serialize_func)

    def _hash_data(self, hash_func, serialize_func):
        serialized_data = serialize_func(self.data)
        self.hash = hash_func(serialized_data)
