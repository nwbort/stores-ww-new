#!/usr/bin/env bash
#
# get_store_details - Fetch details for a single store from Woolworths StoreLocator API
# Usage: ./get_store_details.sh <division> <store_no>
#
# Division values:
#   SUPERMARKETS  - regular Woolworths supermarkets
#   ampol         - stores with Ampol fuel
#   eg            - stores with EG Group fuel
#
# Example: ./get_store_details.sh SUPERMARKETS 1002
#          ./get_store_details.sh ampol 10006

set -e

DIVISION="${1:?Usage: $0 <division> <store_no>}"
STORE_NO="${2:?Usage: $0 <division> <store_no>}"

API_URL="https://www.woolworths.com.au/apis/ui/StoreLocator/Store?Division=${DIVISION}&StoreNo=${STORE_NO}"

curl -s -L \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" \
  -H "Accept: application/json, text/plain, */*" \
  -H "Accept-Language: en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "Cache-Control: no-cache" \
  -H "Pragma: no-cache" \
  -H "sec-ch-ua: \"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"" \
  -H "sec-ch-ua-mobile: ?0" \
  -H "sec-ch-ua-platform: \"macOS\"" \
  -H "Sec-Fetch-Dest: empty" \
  -H "Sec-Fetch-Mode: cors" \
  -H "Sec-Fetch-Site: same-origin" \
  -H "Referer: https://www.woolworths.com.au/shop/storelocator" \
  --compressed \
  "$API_URL"
