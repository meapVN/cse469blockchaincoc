import time
import hash

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        # Combine fields and hash
        block_string = (
            str(self.index) +
            str(self.timestamp) +
            str(self.data) +           # str() works even if data is a dict/list
            str(self.previous_hash) +
            str(self.nonce)
        )
        return hash.hashing(block_string)

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        # Return first block
        return Block(0, time.time(), "Genesis Block", "0")

    def add_block(self, data):
        # Mine and append new block
        pass

    def is_chain_valid(self):
        # Check all links and hashes
        pass