import hashlib
import re


def tokenize(content: str) -> list[str]:
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\s]", content)


def simhash(tokens: list[str], bits: int = 64) -> str:
    vector = [0] * bits
    for token in tokens:
        value = int.from_bytes(hashlib.sha256(token.encode()).digest()[: bits // 8], "big")
        for bit in range(bits):
            vector[bit] += 1 if value & (1 << bit) else -1
    result = sum((1 << bit) for bit, weight in enumerate(vector) if weight >= 0)
    return f"{result:0{bits // 4}x}"


def minhash(tokens: list[str], permutations: int = 64) -> list[int]:
    shingles = {"\0".join(tokens[index:index + 5]) for index in range(max(1, len(tokens) - 4))}
    if not shingles:
        shingles = {""}
    return [min(int.from_bytes(hashlib.sha256(f"{seed}\0{value}".encode()).digest()[:8], "big") for value in shingles) for seed in range(permutations)]


def tlsh_hash(content: str) -> str:
    try:
        import tlsh  # type: ignore[import-not-found]
    except ImportError:
        return ""
    value = tlsh.hash(content.encode())
    return "" if value in {None, "TNULL"} else value


def simhash_similarity(left: str, right: str) -> float:
    distance = (int(left, 16) ^ int(right, 16)).bit_count()
    return 1 - distance / (len(left) * 4)


def minhash_similarity(left: list[int], right: list[int]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    return sum(a == b for a, b in zip(left, right)) / len(left)


def build_fingerprint(content: str):
    tokens = tokenize(content)
    return {
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "token_count": len(tokens),
        "simhash": simhash(tokens),
        "minhash": minhash(tokens),
        "tlsh": tlsh_hash(content),
    }
