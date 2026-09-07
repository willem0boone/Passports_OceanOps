import os
import json
import requests
from pathlib import Path

from utils import (
    create_passport,
    build_full_passport,
    extract_wigos_id,
    safe_chr
)


# setup dir
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR.parent / "passports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARM_EXPORT_PATH = SCRIPT_DIR.parent / "etn_arms_export" / "deployments_ARMS.json"
CONFIG_PATH = SCRIPT_DIR / "config" / "config_passports.json"

for passport_path in OUTPUT_DIR.glob("*.json"):
    passport_path.unlink()

# OceanOPS API settings
OCEANOPS_API_ENDPOINT = "https://www.ocean-ops.org/api/data/passports/search"
PROGRAM = "1006674"   # OceanOps VLIZ-ARMS-MBON

# get ARMS info
with open(ARM_EXPORT_PATH, "r") as f:
    arms = json.load(f)

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# loop over every ARMS deployment
for row in arms:

    print("-"*20)
    print(row)
    print("-"*20)

    deployment_id = safe_chr(row.get("deployment_id"))

    if not deployment_id:
        print("Skipping row: missing deployment_id")
        continue

    print(f"\nProcessing ETN: {deployment_id}")

    receiver_id = row.get("receiver_id")

    # Query OceanOPS API for existing passport
    if receiver_id:
        try:
            payload = {
                "internalIds": [receiver_id],
                "filters": {
                    "programs": PROGRAM
                }
            }
            response = requests.post(OCEANOPS_API_ENDPOINT, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            # Extract first passport if found
            passport = data.get("items", [])[0] if data.get("items") else None
        except Exception as e:
            print(f"Error querying OceanOPS API: {e}")
            passport = None
    else:
        print("Skipping row: missing receiver_id")
        continue

    # ---------------------------------------------------------------
    # CASE 1: Exists in database - update with deployment data & save
    # ---------------------------------------------------------------
    if passport:
        print(f"Match found in OceanOPS - updating with deployment data")
        wigos_id = extract_wigos_id(passport)
        passport = build_full_passport(row, config, wigos_id=wigos_id)

        etn_id = deployment_id
        filename = f"ETN_{etn_id}_WIGOS_{passport.get('platform', {}).get('match', {}).get('wigosId', 'NONE')}.json"
        filepath = OUTPUT_DIR / filename
        
        create_passport(filepath, passport)
        continue

    # ---------------------------------------------------------------
    # CASE 2: New - create WITHOUT WIGOS
    # ---------------------------------------------------------------
    print("No match found in OceanOPS - creating NEW (no WIGOS yet)")

    etn_id = deployment_id
    json_obj = build_full_passport(row, config, wigos_id=None)
    filename = f"ETN_{etn_id}_WIGOS_NONE.json"
    filepath = OUTPUT_DIR / filename
    create_passport(filepath, json_obj)
