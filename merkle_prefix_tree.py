from nodes import InteriorNode, DataNode
from utils import hash_hashes


class MerklePrefixTree:
    def __init__(self, height, hash_func, k_data=None, k_empty=None):
        self.root_node = InteriorNode()
        self.height = height
        self.hash_func = hash_func

        self.k_empty = self._compute_k_empty(k_empty)
        self.k_data = self._compute_k_data(k_data)
        self.empty_tree_hash_dict = self._precompute_empty_hashes()

    def _compute_k_empty(self, k_empty):
        if not k_empty:
            # Compute k_empty digest
            k_empty = b'0'
        return k_empty

    def _compute_k_data(self, k_data):
        if not k_data:
            # Compute k_data
            k_data = b'1'
        return k_data

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

    def append(self, prefix, to_append):
        new_data_node = DataNode(to_append, self.hash_func)
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
            curr_node.hash = hash_hashes(left_hash, right_hash, self.hash_func)

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
