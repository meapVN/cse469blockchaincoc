"""
commands.py - Implements blockchain commands (init, add, checkout, checkin)
Author: Tolani (implemented by Jacob)
"""

import os
import struct
import time


def command_init(filepath, create_genesis_func, write_block_func, read_blocks_func):
    """
    Initialize the blockchain by creating the genesis block
    
    Args:
        filepath: Path to blockchain file
        create_genesis_func: Function to create genesis block (from blockchain_core)
        write_block_func: Function to write block to file (from blockchain_core)
        read_blocks_func: Function to read all blocks (from blockchain_core)
    
    Returns:
        0 on success, 1 on error
    """
    # Check if blockchain file already exists
    if not os.path.exists(filepath):
        # Create the genesis block
        genesis_block = create_genesis_func()
        
        # Write it to the file
        write_block_func(genesis_block, filepath)
        
        print("Blockchain file not found. Created INITIAL block.")
        return 0
    else:
        # File exists, check if it has valid genesis block
        blocks = read_blocks_func(filepath)
        
        if len(blocks) > 0:
            print("Blockchain file found with INITIAL block.")
            return 0
        else:
            print("Error: Blockchain file exists but is invalid.")
            return 1


def command_add(case_id, item_ids, creator, password, filepath, 
                encrypt_case_func, encrypt_item_func, validate_pass_func, 
                read_blocks_func, write_block_func, calc_hash_func):
    """
    Add new evidence items to a case
    
    Args:
        case_id: UUID string for the case
        item_ids: List of integers (item IDs to add)
        creator: String name of creator
        password: Password for validation
        filepath: Path to blockchain file
        encrypt_case_func: Function to encrypt case ID (from encryption)
        encrypt_item_func: Function to encrypt item ID (from encryption)
        validate_pass_func: Function to validate password (from encryption)
        read_blocks_func: Function to read blocks (from blockchain_core)
        write_block_func: Function to write blocks (from blockchain_core)
        calc_hash_func: Function to calculate hash (from blockchain_core)
    
    Returns:
        0 on success, 1 on error
    """
    # Validate password - must be CREATOR role
    if not validate_pass_func(password, "CREATOR"):
        print("Error: Invalid password for CREATOR role")
        return 1
    
    # Encrypt the case ID
    case_id_encrypted = encrypt_case_func(case_id)
    
    # Read existing blocks to get the previous hash
    blocks = read_blocks_func(filepath)
    
    if len(blocks) == 0:
        print("Error: Blockchain not initialized. Run 'bchoc init' first.")
        return 1
    
    # Get the last block to calculate its hash
    # For now, we'll use a simplified approach - calculate hash of the entire last block
    # You'll need to reconstruct the last block as bytes
    last_block = blocks[-1]
    
    # Reconstruct last block as bytes to hash it
    last_block_bytes = struct.pack(
        "32s d 32s 32s 12s 12s 12s I",
        last_block['prev_hash'],
        last_block['timestamp'],
        last_block['case_id'],
        last_block['evidence_id'],
        last_block['state'],
        last_block['creator'],
        last_block['owner'],
        last_block['data_length']
    ) + last_block['data']
    
    # Calculate hash of previous block
    prev_hash = calc_hash_func(last_block_bytes)
    
    # Add each item as a new block
    for item_id in item_ids:
        # Encrypt the item ID
        item_id_encrypted = encrypt_item_func(item_id)
        
        # Create timestamp
        timestamp = time.time()
        
        # State: CHECKEDIN (padded to 12 bytes)
        state = b'CHECKEDIN\x00\x00\x00'
        
        # Creator: padded to 12 bytes
        creator_bytes = creator.encode('utf-8')[:12].ljust(12, b'\x00')
        
        # Owner: same as creator initially
        owner_bytes = creator_bytes
        
        # Data field
        data = b'Added to chain\x00'
        data_length = len(data)
        
        # Pack the block header
        block_header = struct.pack(
            "32s d 32s 32s 12s 12s 12s I",
            prev_hash,
            timestamp,
            case_id_encrypted,
            item_id_encrypted,
            state,
            creator_bytes,
            owner_bytes,
            data_length
        )
        
        # Combine header and data
        full_block = block_header + data
        
        # Write the block to file
        write_block_func(full_block, filepath)
        
        # Update prev_hash for next item (chain them together)
        prev_hash = calc_hash_func(full_block)
        
        # Print confirmation
        print(f"Added item: {item_id}")
        print(f"Status: CHECKEDIN")
        print(f"Time of action: {timestamp}")
    
    return 0


def command_checkout(item_id, password, filepath, encrypt_item_func, 
                    validate_pass_func, read_blocks_func, write_block_func, 
                    decrypt_item_func, calc_hash_func):
    """
    Check out an evidence item (change state to CHECKEDOUT)
    
    Args:
        item_id: Integer item ID to checkout
        password: Password for validation
        filepath: Path to blockchain file
        encrypt_item_func: Function to encrypt item ID (from encryption)
        validate_pass_func: Function to validate password (from encryption)
        read_blocks_func: Function to read blocks (from blockchain_core)
        write_block_func: Function to write blocks (from blockchain_core)
        decrypt_item_func: Function to decrypt item ID (from encryption)
        calc_hash_func: Function to calculate hash (from blockchain_core)
    
    Returns:
        0 on success, 1 on error
    """
    # Validate password - must be OWNER role
    if not validate_pass_func(password, "OWNER"):
        print("Error: Invalid password for OWNER role")
        return 1
    
    # Read all blocks
    blocks = read_blocks_func(filepath)
    
    if len(blocks) == 0:
        print("Error: Blockchain not initialized.")
        return 1
    
    # Find the most recent block for this item
    found = False
    last_case_id = None
    last_state = None
    last_creator = None
    
    for block in blocks:
        try:
            # Decrypt the item ID to check if it matches
            decrypted_item = decrypt_item_func(block['evidence_id'])
            
            if decrypted_item == item_id:
                found = True
                last_case_id = block['case_id']
                last_state = block['state'].decode('utf-8').rstrip('\x00')
                last_creator = block['creator']
        except:
            # Skip blocks we can't decrypt (like genesis)
            pass
    
    # Check if item was found
    if not found:
        print(f"Error: Item {item_id} not found in blockchain")
        return 1
    
    # Check if item is currently CHECKEDIN
    if last_state != "CHECKEDIN":
        print(f"Error: Item {item_id} is {last_state}, cannot checkout")
        return 1
    
    # Create new block with CHECKEDOUT state
    # Get last block for prev_hash
    last_block = blocks[-1]
    last_block_bytes = struct.pack(
        "32s d 32s 32s 12s 12s 12s I",
        last_block['prev_hash'],
        last_block['timestamp'],
        last_block['case_id'],
        last_block['evidence_id'],
        last_block['state'],
        last_block['creator'],
        last_block['owner'],
        last_block['data_length']
    ) + last_block['data']
    
    prev_hash = calc_hash_func(last_block_bytes)
    
    # Encrypt item ID
    item_id_encrypted = encrypt_item_func(item_id)
    
    # Create timestamp
    timestamp = time.time()
    
    # State: CHECKEDOUT (padded to 12 bytes)
    state = b'CHECKEDOUT\x00\x00'
    
    # Owner: whoever is checking it out (we'll use a generic "OWNER" for now)
    owner_bytes = b'OWNER\x00\x00\x00\x00\x00\x00\x00'
    
    # Data
    data = b'Checked out\x00'
    data_length = len(data)
    
    # Pack the block
    block_header = struct.pack(
        "32s d 32s 32s 12s 12s 12s I",
        prev_hash,
        timestamp,
        last_case_id,  # Same case ID
        item_id_encrypted,
        state,
        last_creator,  # Keep original creator
        owner_bytes,
        data_length
    )
    
    full_block = block_header + data
    
    # Write block
    write_block_func(full_block, filepath)
    
    print(f"Checked out item: {item_id}")
    print(f"Status: CHECKEDOUT")
    print(f"Time of action: {timestamp}")
    
    return 0


def command_checkin(item_id, password, filepath, encrypt_item_func, 
                   validate_pass_func, read_blocks_func, write_block_func, 
                   decrypt_item_func, calc_hash_func):
    """
    Check in an evidence item (change state to CHECKEDIN)
    
    Args:
        item_id: Integer item ID to checkin
        password: Password for validation
        filepath: Path to blockchain file
        encrypt_item_func: Function to encrypt item ID (from encryption)
        validate_pass_func: Function to validate password (from encryption)
        read_blocks_func: Function to read blocks (from blockchain_core)
        write_block_func: Function to write blocks (from blockchain_core)
        decrypt_item_func: Function to decrypt item ID (from encryption)
        calc_hash_func: Function to calculate hash (from blockchain_core)
    
    Returns:
        0 on success, 1 on error
    """
    # Validate password - must be OWNER role
    if not validate_pass_func(password, "OWNER"):
        print("Error: Invalid password for OWNER role")
        return 1
    
    # Read all blocks
    blocks = read_blocks_func(filepath)
    
    if len(blocks) == 0:
        print("Error: Blockchain not initialized.")
        return 1
    
    # Find the most recent block for this item
    found = False
    last_case_id = None
    last_state = None
    last_creator = None
    
    for block in blocks:
        try:
            # Decrypt the item ID to check if it matches
            decrypted_item = decrypt_item_func(block['evidence_id'])
            
            if decrypted_item == item_id:
                found = True
                last_case_id = block['case_id']
                last_state = block['state'].decode('utf-8').rstrip('\x00')
                last_creator = block['creator']
        except:
            # Skip blocks we can't decrypt
            pass
    
    # Check if item was found
    if not found:
        print(f"Error: Item {item_id} not found in blockchain")
        return 1
    
    # Check if item is currently CHECKEDOUT
    if last_state != "CHECKEDOUT":
        print(f"Error: Item {item_id} is {last_state}, cannot checkin")
        return 1
    
    # Create new block with CHECKEDIN state
    # Get last block for prev_hash
    last_block = blocks[-1]
    last_block_bytes = struct.pack(
        "32s d 32s 32s 12s 12s 12s I",
        last_block['prev_hash'],
        last_block['timestamp'],
        last_block['case_id'],
        last_block['evidence_id'],
        last_block['state'],
        last_block['creator'],
        last_block['owner'],
        last_block['data_length']
    ) + last_block['data']
    
    prev_hash = calc_hash_func(last_block_bytes)
    
    # Encrypt item ID
    item_id_encrypted = encrypt_item_func(item_id)
    
    # Create timestamp
    timestamp = time.time()
    
    # State: CHECKEDIN (padded to 12 bytes)
    state = b'CHECKEDIN\x00\x00\x00'
    
    # Owner: back to original creator
    owner_bytes = last_creator
    
    # Data
    data = b'Checked in\x00'
    data_length = len(data)
    
    # Pack the block
    block_header = struct.pack(
        "32s d 32s 32s 12s 12s 12s I",
        prev_hash,
        timestamp,
        last_case_id,  # Same case ID
        item_id_encrypted,
        state,
        last_creator,  # Keep original creator
        owner_bytes,
        data_length
    )
    
    full_block = block_header + data
    
    # Write block
    write_block_func(full_block, filepath)
    
    print(f"Checked in item: {item_id}")
    print(f"Status: CHECKEDIN")
    print(f"Time of action: {timestamp}")
    
    return 0