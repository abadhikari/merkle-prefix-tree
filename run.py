import hashlib

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


if __name__ == '__main__':
    m = MerklePrefixTree(4, default_hash_func)
    prefix = '0001'
    m.append(prefix, 3)
    poi = m.produce_inclusion_proof(prefix)
    data_node = m.get_data_node(prefix)
    m.print_tree()

