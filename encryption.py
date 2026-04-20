
#imports
import uuid
import struct
from Crypto.Cipher import AES


# Hardcoded passkey
_KEY = b"R0chLi4uLi4uLi4="

# Role Passwords
_ROLE_PASSWORDS = {
    "CREATOR":   "C67C",
    "POLICE":    "P80P",
    "LAWYER":    "L76L",
    "ANALYST":   "A65A",
    "EXECUTIVE": "E69E",
}

# Helper Functions

def get_cipher() -> AES:
    """Makes fresh AES lock using hardcoded key in ECB MOde"""
    return AES.new(_KEY, AES.MODE_ECB)


def pad(data: bytes) -> bytes:
    """Pads data so its multiple of 16 (required for AES blocks)"""
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len] * pad_len)


def unpad(data: bytes) -> bytes:
    """"Removes the padding from pad"""
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Invalid padding byte — data may be corrupted or wrong key.")
    return data[:-pad_len]


# Encrypt Case ID
def encrypt_case_id(case_id_string: str) -> bytes:
    """"Encrypts a UUID string to raw 16 byte string, then pads to 32 bytes and encrypted"""
    try:
        parsed = uuid.UUID(case_id_string)
    except ValueError:
        raise ValueError(f"Invalid UUID format: '{case_id_string}'")

    raw = parsed.bytes
    padded = pad(raw)
    return get_cipher().encrypt(padded)


# Encrypt Item ID
def encrypt_item_id(item_id_int: int) -> bytes:
    """ Takes an int and packs it to 8 bytes (big endian) then pads to 16 bytes and encrypts"""
    if not isinstance(item_id_int, int):
        raise TypeError(f"item_id must be an int, got {type(item_id_int).__name__}")
    if item_id_int < 0:
        raise ValueError("item_id must be non-negative.")

    raw = struct.pack(">Q", item_id_int)
    padded = pad(raw)
    return get_cipher().encrypt(padded)


# Decrypt case ID

def decrypt_case_id(encrypted_bytes: bytes) -> str:
    """ Decrypts the 32 bytes, removes padding then reconstructs UUID"""
    decrypted = get_cipher().decrypt(encrypted_bytes)
    raw = unpad(decrypted)

    if len(raw) != 16:
        raise ValueError(f"Decrypted data is {len(raw)} bytes; expected 16 for a UUID.")

    return str(uuid.UUID(bytes=raw))

# Decrypt Item ID

def decrypt_item_id(encrypted_bytes: bytes) -> int:
    """ Decrypts the 16 bytes, strips the 8 byte padding, and finally unpacks the int"""
    decrypted = get_cipher().decrypt(encrypted_bytes)
    raw = unpad(decrypted)

    if len(raw) != 8:
        raise ValueError(f"Decrypted data is {len(raw)} bytes; expected 8 for an item ID.")

    return struct.unpack(">Q", raw)[0]


# Password Validation

def validate_password(password: str, role: str) -> bool:
    """Checks password against known passwords stored, if match return true else false"""

    normalised_role = role.strip().upper()
    expected = _ROLE_PASSWORDS.get(normalised_role)

    if expected is None:
        return False

    return password == expected
