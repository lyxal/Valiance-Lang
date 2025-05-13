def merge_bytes(bytes: list[int]) -> int:
    """
    Takes a list of ints and merges them into a single int by
    combining bits.
    """
    result: int = 0
    for byte in bytes:
        result = (result << 8) | byte
    return result


def encode_multibyte(n: int) -> list[int]:
    """Encodes an integer as a multibyte sequence."""
    bytes_out: list[int] = []
    while n >= 0x80:
        bytes_out.append((n & 0x7F) | 0x80)
        n >>= 7
    bytes_out.append(n)  # Last byte with MSB 0
    return bytes_out


def decode_multibyte(bytes: list[int]) -> int:
    """Decodes a multibyte sequence into an integer."""
    result: int = 0
    shift: int = 0
    for byte in bytes:
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result
