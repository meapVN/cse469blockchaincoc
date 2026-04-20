import struct
import hashlib
import time
import os
from Crypto.Cipher import AES   # pip install pycryptodome if needed

AES_KEY = b"R0chLi4uLi4uLi4="

class Block:
    # struct format for the fixed part (first 0x8c bytes)
    # "32s d 32s 32s 12s 12s 12s I" exactly as recommended in the PDF
    FORMAT = "32s d 32s 32s 12s 12s 12s I"
    FIXED_SIZE = struct.calcsize(FORMAT)   # should be 140 bytes (0x8c)

    def __init__(self, prev_hash, timestamp, case_id, item_id, state, creator, owner, data):
        self.prev_hash = prev_hash          # 32 bytes (SHA-256 of previous block)
        self.timestamp = float(timestamp)   # Unix timestamp (UTC)
        self.case_id_raw = case_id          # bytes (UUID) - will be encrypted
        self.item_id_raw = item_id          # bytes (4-byte int) - will be encrypted
        self.state = state                  # e.g. b"CHECKEDIN" padded to 12 bytes
        self.creator = creator              # max 12 bytes
        self.owner = owner                  # Police/Lawyer/Analyst/Executive, max 12 bytes
        self.data = data.encode('utf-8') if isinstance(data, str) else data

    def _encrypt(self, data: bytes) -> bytes:
        """AES-ECB encryption. Project stores 32-byte encrypted values."""
        cipher = AES.new(AES_KEY, AES.MODE_ECB)
        # Pad to multiple of 16 bytes
        pad_len = 16 - (len(data) % 16)
        padded = data + b'\0' * pad_len
        encrypted = cipher.encrypt(padded)
        return encrypted[:32]  # project uses 32-byte fields

    def to_bytes(self) -> bytes:
        """Pack the block exactly as the spec requires (binary)."""
        encrypted_case = self._encrypt(self.case_id_raw)
        encrypted_item = self._encrypt(self.item_id_raw)

        packed_fixed = struct.pack(
            self.FORMAT,
            self.prev_hash,
            self.timestamp,
            encrypted_case,
            encrypted_item,
            self.state.ljust(12, b'\0')[:12],
            self.creator.ljust(12, b'\0')[:12],
            self.owner.ljust(12, b'\0')[:12],
            len(self.data)
        )
        return packed_fixed + self.data

    @classmethod
    def from_bytes(cls, block_bytes: bytes):
        """Unpack a binary block (used when reading the file)."""
        fixed = block_bytes[:cls.FIXED_SIZE]
        data = block_bytes[cls.FIXED_SIZE:]

        (prev_hash, timestamp, enc_case, enc_item,
         state, creator, owner, data_len) = struct.unpack(cls.FORMAT, fixed)

        # TODO: decrypt case_id and item_id when password is valid (you'll need this for show commands)
        # For now you can store the encrypted values and decrypt later

        return cls(
            prev_hash=prev_hash,
            timestamp=timestamp,
            case_id=enc_case,      # encrypted in file
            item_id=enc_item,
            state=state.rstrip(b'\0'),
            creator=creator.rstrip(b'\0'),
            owner=owner.rstrip(b'\0'),
            data=data[:data_len]   # respect data length
        )

    def calculate_block_hash(self) -> bytes:
        """This is what you put in the NEXT block's prev_hash field."""
        return hashlib.sha256(self.to_bytes()).digest()