# cse469blockchaincoc
A program that uses block chain technology to maintain Chain of Custody

HOW TO USE BLOCK.PY:
First, import block into the main code:

from block import Block, create_genesis_block

When making the first entry, call create_genesis_block() first to create a genesis block

genesis = create_genesis_block()

Then, create a block class using:
 block1 = Block(
        prev_hash                                   # must link to previous block
        timestamp=time.time(),                      # current UTC time
        case_id=test_case_id,                       # Must be in byte
        item_id=test_item_id,                       # Must be in byte
        state=b"CHECKEDIN",                         # must be bytes
        creator=b"Police",                          # max 12 chars
        owner=b"Analyst",                           # must be one of the allowed owners
        data="Evidence collected at crime scene"    # free-form text
    )

We will have a Block class to use (named block1)
To calculate the next hash, use calculate_block_hash():
next_prev_hash = block1.calculate_block_hash()

test.py will have example of how to use the block.py