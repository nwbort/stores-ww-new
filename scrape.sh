#!/bin/bash
XML_URL='https://www.woolworths.com.au/sitemap-store-locator.xml'
XML_FILE='woolworths.com.au-sitemap-store-locator.xml.xml'
JSON_FILE='woolworths.com.au-stores.json'

./download.sh "$XML_URL"
./parse.sh "$XML_FILE" "$JSON_FILE"
