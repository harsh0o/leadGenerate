import hashlib

def compute_checksum(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def verify_row(key: str, value: str, checksum: str) -> bool:
    return compute_checksum(value) == checksum
