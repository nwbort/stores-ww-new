#!/usr/bin/env python3
"""
Test store details API for the first store of each type in woolworths.com.au-stores.json.

Division mapping:
  supermarket (no type field) -> SUPERMARKETS
  ampol                       -> ampol
  eg                          -> eg
"""

import json
import subprocess
import sys
import os

STORES_JSON = os.path.join(os.path.dirname(__file__), "woolworths.com.au-stores.json")
GET_DETAILS_SCRIPT = os.path.join(os.path.dirname(__file__), "get_store_details.sh")

DIVISION_MAP = {
    "supermarket": "SUPERMARKETS",
    "ampol": "ampol",
    "eg": "eg",
}


def find_first_of_each_type(stores):
    seen = {}
    for store in stores:
        t = store.get("type", "supermarket")
        if t not in seen:
            seen[t] = store
    return seen


def fetch_store_details(division, store_no):
    result = subprocess.run(
        ["bash", GET_DETAILS_SCRIPT, division, str(store_no)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"get_store_details.sh failed: {result.stderr}")
    return result.stdout.strip()


def validate_response(raw, store_type, store_id, store_name):
    """Parse and validate the API response. Returns (passed, message)."""
    if not raw:
        return False, "Empty response"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        snippet = raw[:200].replace("\n", " ")
        return False, f"Invalid JSON: {e} — response starts with: {snippet!r}"

    if not isinstance(data, dict):
        return False, f"Expected JSON object, got {type(data).__name__}"

    # The API wraps the store in a top-level object; surface whatever keys we get
    # so CI logs show what was returned even if field names change.
    keys = list(data.keys())

    # Look for a store number / name in common field locations
    store_no_found = None
    name_found = None
    for k, v in data.items():
        kl = k.lower()
        if kl in ("storeno", "store_no", "storenumber"):
            store_no_found = v
        if kl in ("name", "storename", "store_name"):
            name_found = v

    if not keys:
        return False, "Response is an empty JSON object {}"

    msg = f"OK — top-level keys: {keys}"
    if store_no_found is not None:
        msg += f", StoreNo={store_no_found}"
    if name_found is not None:
        msg += f", Name={name_found!r}"
    return True, msg


def main():
    with open(STORES_JSON) as f:
        stores = json.load(f)

    first_by_type = find_first_of_each_type(stores)
    print(f"Found {len(first_by_type)} store types: {sorted(first_by_type)}\n")

    failures = []

    for store_type in sorted(first_by_type):
        store = first_by_type[store_type]
        division = DIVISION_MAP.get(store_type, store_type)
        store_id = store["id"]
        store_name = store["name"]

        print(f"[{store_type}] {store_name} (id={store_id}, division={division})")
        try:
            raw = fetch_store_details(division, store_id)
        except RuntimeError as e:
            print(f"  FAIL — {e}\n")
            failures.append((store_type, store_id, str(e)))
            continue

        passed, message = validate_response(raw, store_type, store_id, store_name)
        status = "PASS" if passed else "FAIL"
        print(f"  {status} — {message}")
        if not passed:
            print(f"  Raw response (first 500 chars): {raw[:500]!r}")
            failures.append((store_type, store_id, message))
        print()

    if failures:
        print(f"FAILED: {len(failures)} test(s) failed:")
        for t, sid, msg in failures:
            print(f"  [{t}] id={sid}: {msg}")
        sys.exit(1)
    else:
        print(f"All {len(first_by_type)} tests passed.")


if __name__ == "__main__":
    main()
