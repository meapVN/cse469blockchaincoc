# Kevin Arrieta, 1222710515
#
# This is the queries portion :)
#
#
# Primary functions:
#   - show_cases(...)
#   - show_items(...)
#   - show_history(...)
# (functions are at the bottom hehe)

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional


def _get_value(block: Any, *names: str, default: Any = None) -> Any:
    # This is a fetcher. It grabs the value from a dict or object.
    for name in names:
        if isinstance(block, dict) and name in block:
            return block[name]
        if hasattr(block, name):
            return getattr(block, name)
    return default



def _strip_bytes(value: Any) -> Any:
    # Padding may be in the byte field, this removes any trailing null padding. (not always required.)
    if isinstance(value, bytes):
        return value.rstrip(b"\x00")
    return value



def _decode_text(value: Any) -> str:
    # Convert any byte values into string. 
    value = _strip_bytes(value)

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)



def _fallback_identifier(value: Any) -> str:
    # If case/item cannot be decrupted, call this fallback.
    value = _strip_bytes(value)

    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.hex()
    return str(value)



def _maybe_decrypt(value: Any, can_decrypt: bool, decrypt_func: Optional[Callable[[Any], Any]]) -> str:
    # perchance decrypt some field, if allowed. if try fails, fallback is called to display some representation (rather than crashing).
    if can_decrypt and decrypt_func is not None:
        try:
            return _decode_text(decrypt_func(value))
        except Exception:
            pass
    return _fallback_identifier(value)



def _normalize_state(block: Any) -> str:
    return _decode_text(_get_value(block, "state")).strip()



def _is_genesis(block: Any) -> bool:
    # INITIAL block is treated as metadata, not as evidence history.
    # sega genesis
    return _normalize_state(block) == "INITIAL"


# I feel these are self explanatory right? They are just the fields.
def _case_field(block: Any) -> Any:
    return _get_value(block, "case_id", "case")



def _item_field(block: Any) -> Any:
    return _get_value(block, "evidence_id", "item_id", "item")



def _timestamp_field(block: Any) -> Any:
    return _get_value(block, "timestamp", default=0.0)



def _creator_field(block: Any) -> Any:
    return _get_value(block, "creator", default=b"")



def _owner_field(block: Any) -> Any:
    return _get_value(block, "owner", default=b"")



def _data_field(block: Any) -> Any:
    return _get_value(block, "data", default=b"")
# Self explanation ends here.


def _build_history_rows(
    blocks: Iterable[Any],
    has_valid_password: bool,
    decrypt_case_func: Optional[Callable[[Any], Any]],
    decrypt_item_func: Optional[Callable[[Any], Any]],
) -> List[dict]:
    # Converts raw blocks into a normal looking list of rows. displays nicely. Call when the row list needs to be built...
    rows: List[dict] = []

    for index, block in enumerate(blocks):
        if _is_genesis(block):
            continue

        rows.append(
            {
                "index": index,
                "case": _maybe_decrypt(_case_field(block), has_valid_password, decrypt_case_func),
                "item": _maybe_decrypt(_item_field(block), has_valid_password, decrypt_item_func),
                "action": _normalize_state(block),
                "time": _timestamp_field(block),
                "creator": _decode_text(_creator_field(block)),
                "owner": _decode_text(_owner_field(block)),
                "data": _decode_text(_data_field(block)),
            }
        )

    return rows


#
# This is the main functions themselves. This is what you came here for. perchance.
#

def show_cases(blocks, has_valid_password, decrypt_func):
    # blocks: list of blocks (normally dicts from read_all_blocks)
    # has_valid_password: simply tells if decryption is allowed.
    # decrypt_func: function that is used to decrupt case IDs.

    # return: ordered list of case IDs. all unique IDs found in the blockchain are printed accordingly

    seen = set()
    ordered_cases: List[str] = []

    for block in blocks:
        if _is_genesis(block):
            continue

        case_value = _maybe_decrypt(_case_field(block), has_valid_password, decrypt_func)
        if case_value not in seen:
            seen.add(case_value)
            ordered_cases.append(case_value)

    if not ordered_cases:
        print("No cases found.")
        return []

    for case_id in ordered_cases:
        label = "Case" if has_valid_password else "Case (encrypted)"
        print(f"{label}: {case_id}")

    return ordered_cases



def show_items(blocks, case_id_filter, has_valid_password, decrypt_case_func, decrypt_item_func):
    # blocks: list of blocks
    # case_id_filter: The case ID to match. If none, then all items are shown.
    # has_valid_password: whether decryption is allowed.
    # decrypt_case_func: function that is used to decrypt case IDs.
    # decrypt_item_func: function that is ued to decrypt item IDs.

    #return: a cool ordered list of all displayed item IDs.

    items: List[str] = []
    seen = set()

    for block in blocks:
        if _is_genesis(block):
            continue

        case_value = _maybe_decrypt(_case_field(block), has_valid_password, decrypt_case_func)
        item_value = _maybe_decrypt(_item_field(block), has_valid_password, decrypt_item_func)

        if case_id_filter is not None and str(case_value) != str(case_id_filter):
            continue

        if item_value not in seen:
            seen.add(item_value)
            items.append(item_value)

    if not items:
        if case_id_filter is None:
            print("No items found.")
        else:
            print(f"No items found for case: {case_id_filter}")
        return []

    if case_id_filter is not None:
        label = "Items for case" if has_valid_password else "Items for encrypted case"
        print(f"{label}: {case_id_filter}")

    for item_id in items:
        item_label = "Item" if has_valid_password else "Item (encrypted)"
        print(f"{item_label}: {item_id}")

    return items



def show_history(
    blocks,
    case_filter,
    item_filter,
    num_entries,
    reverse,
    has_valid_password,
    decrypt_case_func,
    decrypt_item_func,
):
    # blocks: List of blocks.
    # case_filter: (optional) case ID filter
    # item_filter: (optional) item ID filter
    # num_entries: (optiomal) max number of entries to display.
    # reverse: True!?!?!? then show newest entries first. Fake!?!?! show oldest first.
    # has_valid_password: whether decryption is allowed. (yeah third time listed yup yup).
    # decrypt_case_func: fuincton that is used to decrypt case IDs.
    # decrypt_item_func: function that is used to decrypt item IDs.

    # return: a list of normalized history rows that were displayed.

    rows = _build_history_rows(blocks, has_valid_password, decrypt_case_func, decrypt_item_func)

    if case_filter is not None:
        rows = [row for row in rows if str(row["case"]) == str(case_filter)]

    if item_filter is not None:
        rows = [row for row in rows if str(row["item"]) == str(item_filter)]

    if reverse:
        rows = list(reversed(rows))

    if num_entries is not None:
        try:
            limit = int(num_entries)
            if limit >= 0:
                rows = rows[:limit]
        except (TypeError, ValueError):
            pass

    if not rows:
        print("No history entries found.")
        return []

    case_label = "Case" if has_valid_password else "Case (encrypted)"
    item_label = "Item" if has_valid_password else "Item (encrypted)"

    for i, row in enumerate(rows):
        print(f"{case_label}: {row['case']}")
        print(f"{item_label}: {row['item']}")
        print(f"Action: {row['action']}")
        print(f"Time: {row['time']}")

        if row["creator"]:
            print(f"Creator: {row['creator']}")
        if row["owner"]:
            print(f"Owner: {row['owner']}")
        if row["data"]:
            print(f"Data: {row['data']}")

        if i != len(rows) - 1:
            print("-" * 40)

    return rows

# Does the output look professional enough? :^)