#!/usr/bin/env bash
#
# parse - Extract store names and URLs from a Woolworths sitemap XML file into JSON
# Usage: ./parse.sh <xml-file> [output-json-file]

set -e

if [ $# -lt 1 ]; then
  echo "Usage: $0 <xml-file> [output-json-file]"
  exit 1
fi

XML_FILE="$1"
OUTPUT_FILE="${2:-}"

if [ ! -f "$XML_FILE" ]; then
  echo "Error: File not found: $XML_FILE"
  exit 1
fi

JSON=$(python3 - "$XML_FILE" <<'PYEOF'
import xml.etree.ElementTree as ET
import json
import sys

KNOWN_SUFFIXES = {'ampol'}

def extract_store(url):
    slug = url.rstrip('/').split('/')[-1]
    if not slug:
        return None
    parts = slug.split('-')
    # Strip a known brand suffix (e.g. -ampol) before parsing id and name
    store_type = None
    if parts[-1].lower() in KNOWN_SUFFIXES:
        store_type = parts[-1].lower()
        parts = parts[:-1]
    # Expect at least: {state}-{name}-{id}
    if len(parts) < 3 or not parts[-1].isdigit():
        return None
    store_id = int(parts[-1])
    name = ' '.join(p.title() for p in parts[1:-1])
    return store_id, name, store_type

tree = ET.parse(sys.argv[1])
root = tree.getroot()
ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

stores = []
for url_elem in root.findall('sm:url', ns):
    loc_elem = url_elem.find('sm:loc', ns)
    if loc_elem is None:
        continue
    loc = loc_elem.text
    if '/storelocator/' not in loc:
        continue
    result = extract_store(loc)
    if result:
        store_id, name, store_type = result
        entry = {'id': store_id, 'name': name, 'url': loc}
        if store_type:
            entry['type'] = store_type
        stores.append(entry)

print(json.dumps(stores, indent=2))
PYEOF
)

if [ -n "$OUTPUT_FILE" ]; then
  echo "$JSON" > "$OUTPUT_FILE"
  echo "Saved $(echo "$JSON" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))') stores to $OUTPUT_FILE"
else
  echo "$JSON"
fi
