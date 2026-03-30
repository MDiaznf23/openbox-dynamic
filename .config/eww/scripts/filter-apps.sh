#!/bin/bash
CATEGORY="${1:-Internet}"
python3 - <<EOF
import json, sys
with open("/home/diaz/.cache/eww-menu.json") as f:
    data = json.load(f)
for cat in data.get("categories", []):
    if cat.get("category") == """$CATEGORY""":
        print(json.dumps(cat.get("apps", [])))
        sys.exit(0)
print("[]")
EOF
