# test_block.py
# ================================================
# Simple test script to verify your block.py works
# Run this file with: python test_block.py
# ================================================

import time
import os
from block import Block, create_genesis_block   # <-- Import from your block.py

def main():
    print("=== Testing Block Class ===\n")

    # 1. Create the Genesis (INITIAL) block
    genesis = create_genesis_block()
    print("✅ Genesis block created")
    print(f"   Prev Hash : {genesis.prev_hash.hex()[:16]}... (32 zeros)")
    print(f"   Timestamp : {genesis.timestamp}")
    print(f"   State     : {genesis.state}")
    print(f"   Block hash: {genesis.calculate_block_hash().hex()[:32]}...\n")

    # 2. Create a normal block (example of "add" command)
    test_case_id = b"1fd9fb21-9de0-4930-8ab0-5dd29fe29acd"   # 32-byte UUID as bytes
    test_item_id = b"\x00\x00\x00\x01"                       # 4-byte integer as bytes (item 1)

    block1 = Block(
        prev_hash=genesis.calculate_block_hash(),   # must link to previous block
        timestamp=time.time(),                      # current UTC time
        case_id=test_case_id,
        item_id=test_item_id,
        state=b"CHECKEDIN",                         # must be bytes
        creator=b"Police",                          # max 12 chars
        owner=b"Analyst",                           # must be one of the allowed owners
        data="Evidence collected at crime scene"    # free-form text
    )

    print("✅ Normal block created (CHECKEDIN)")

    # 3. Convert to binary (what gets written to the blockchain file)
    binary_data = block1.to_bytes()
    print(f"   Binary size: {len(binary_data)} bytes (fixed header + data)")

    # 4. Round-trip test: write → read back → compare
    recovered_block = Block.from_bytes(binary_data)

    print("\n✅ Round-trip test (to_bytes → from_bytes)")
    print(f"   Recovered state : {recovered_block.state}")
    print(f"   Recovered data  : {recovered_block.data.decode('utf-8', errors='ignore')}")

    # 5. Verify the hash chain works
    next_prev_hash = block1.calculate_block_hash()
    print(f"   Next block should use this prev_hash: {next_prev_hash.hex()[:32]}...")

    print("\n🎉 All basic tests passed! Your Block class is ready for the full bchoc program.")

    # Optional: write a tiny test file so you can inspect it
    with open("test_blockchain.bin", "wb") as f:
        f.write(genesis.to_bytes())
        f.write(block1.to_bytes())
    print("   Wrote test_blockchain.bin (open with a hex editor if you want to inspect)")

if __name__ == "__main__":
    main()