from pathlib import Path
from pprint import pprint

from OceanOpsClient import OceanOpsClient

client = OceanOpsClient.from_env()

SCRIPT_DIR = Path(__file__).resolve().parent
PASSPORT_DIR = SCRIPT_DIR.parent / "passports"

passports = sorted(PASSPORT_DIR.glob("*.json"))
for passport_path in passports:

    passport = str(passport_path)

    # status = client.validate_passport_json(passport)
    # pprint(status)
    m = client.post_passport(passport, dry_run=False)
    pprint(m)

