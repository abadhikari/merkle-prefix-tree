import json


def json_serialize(to_serialize):
    return json.dumps(to_serialize) if not isinstance(to_serialize, str) else to_serialize


def hash_nodes(node_1, node_2, hash_func):
    hash_1, hash_2 = node_1.hash, node_2.hash
    return hash_hashes(hash_1, hash_2, hash_func)


def hash_hashes(hash_1, hash_2, hash_func):
    concat_hash = hash_1 + hash_2
    return hash_func(concat_hash)

