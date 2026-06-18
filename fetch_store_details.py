#!/usr/bin/env python3
"""
Fetch and cache Woolworths store details from the StoreLocator API.

Reads woolworths.com.au-stores.json, fetches details for each store in
parallel, writes individual files to store-details/{id}.json, then
rebuilds woolworths.com.au-store-details.json from those files.

Usage:
  python3 fetch_store_details.py           # new stores only (default)
  python3 fetch_store_details.py --all     # refresh every store
"""

import json
import os
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

STORES_JSON = "woolworths.com.au-stores.json"
DETAILS_DIR = "store-details"
COMBINED_JSON = "woolworths.com.au-store-details.json"
API_BASE = "https://www.woolworths.com.au/apis/ui/StoreLocator/Store"
MAX_WORKERS = 20

DIVISION_MAP = {
    "supermarket": "SUPERMARKETS",
    "ampol": "ampol",
    "eg": "eg",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Referer": "https://www.woolworths.com.au/shop/storelocator",
}


def detail_path(store_id):
    return os.path.join(DETAILS_DIR, f"{store_id}.json")


def fetch_store(store):
    store_id = store["id"]
    store_type = store.get("type", "supermarket")
    division = DIVISION_MAP.get(store_type, store_type)
    url = f"{API_BASE}?Division={division}&StoreNo={store_id}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict) or not data:
            return store_id, None, "empty or non-object response"
        return store_id, data, None
    except urllib.error.HTTPError as e:
        return store_id, None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return store_id, None, f"URL error: {e.reason}"
    except json.JSONDecodeError as e:
        return store_id, None, f"invalid JSON: {e}"
    except Exception as e:
        return store_id, None, str(e)


def rebuild_combined(current_store_ids):
    details = []
    if not os.path.isdir(DETAILS_DIR):
        return 0
    for fname in os.listdir(DETAILS_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            store_id = int(fname[:-5])
        except ValueError:
            continue
        if store_id not in current_store_ids:
            continue
        with open(os.path.join(DETAILS_DIR, fname)) as f:
            details.append(json.load(f))
    details.sort(key=lambda d: d.get("StoreNo", 0))
    with open(COMBINED_JSON, "w") as f:
        json.dump(details, f, indent=2)
    return len(details)


def main():
    fetch_all = "--all" in sys.argv

    os.makedirs(DETAILS_DIR, exist_ok=True)

    with open(STORES_JSON) as f:
        stores = json.load(f)

    current_store_ids = {s["id"] for s in stores}

    if fetch_all:
        to_fetch = stores
        print(f"Mode: all — {len(to_fetch)} stores to fetch")
    else:
        to_fetch = [s for s in stores if not os.path.exists(detail_path(s["id"]))]
        cached = len(stores) - len(to_fetch)
        print(f"Mode: new-only — {len(to_fetch)} to fetch, {cached} already cached")

    if to_fetch:
        success = 0
        failed = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_store, s): s for s in to_fetch}
            for i, future in enumerate(as_completed(futures), 1):
                store_id, data, error = future.result()
                if data is not None:
                    with open(detail_path(store_id), "w") as f:
                        json.dump(data, f, indent=2)
                    success += 1
                else:
                    failed.append((store_id, error))
                if i % 100 == 0 or i == len(to_fetch):
                    print(f"  {i}/{len(to_fetch)} — {success} ok, {len(failed)} failed")

        print(f"\nResult: {success} fetched, {len(failed)} failed")
        if failed:
            for sid, err in failed[:20]:
                print(f"  store {sid}: {err}")
            if len(failed) > 20:
                print(f"  ... and {len(failed) - 20} more")
    else:
        print("Nothing to fetch.")

    n = rebuild_combined(current_store_ids)
    print(f"Rebuilt {COMBINED_JSON} with {n} stores.")


if __name__ == "__main__":
    main()
