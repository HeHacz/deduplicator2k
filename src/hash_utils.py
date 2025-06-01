import hashlib

def get_file_hash(file_path, hash_algorithm='blake2b', chunk_size=16777216):
    hasher = hashlib.new(hash_algorithm)

    with open(file_path, 'rb') as file:
        while chunk := file.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()