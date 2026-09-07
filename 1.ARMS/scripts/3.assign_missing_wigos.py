import os
import json
from pathlib import Path

from utils import request_wigos_id

PASSPORT_DIR = Path(__file__).resolve().parent.parent / "passports"


def _extract_summary(passport):
    """
    Extract human-readable summary fields.
    """
    try:
        patch = passport.get("platform", {}).get("patch", {})
        dep = patch.get("deployment", {})

        name = patch.get("name")
        date = dep.get("date")
        lat = dep.get("latitude")
        lon = dep.get("longitude")

        return name, date, lat, lon

    except Exception:
        return None, None, None, None


def _ask_confirmation():
    """
    Robust Y/n input loop.
    """
    while True:
        user_input = input("Assign new WIGOS ID? [y/n]: ").strip().lower()

        if user_input in ("y", "yes"):
            return True
        elif user_input in ("n", "no"):
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def assign_wigos_ids():

    if not os.path.exists(PASSPORT_DIR):
        print("No passports directory found.")
        return

    files = [f for f in os.listdir(PASSPORT_DIR) if f.endswith(".json")]

    for filename in files:

        # -----------------------------------------------------------
        # Validate filename format
        # -----------------------------------------------------------
        if "_" not in filename:
            print(f"Skipping malformed filename: {filename}")
            continue

        etn_id = filename.split("_")[1]

        filepath = PASSPORT_DIR / filename

        try:
            with open(filepath, "r") as f:
                passport = json.load(f)
        except Exception:
            print(f"Skipping invalid JSON: {filename}")
            continue

        wigos_id = (
            passport.get("platform", {})
            .get("match", {})
            .get("wigosId")
        )

        # -----------------------------------------------------------
        # Skip already assigned
        # -----------------------------------------------------------
        if wigos_id:
            continue

        name, date, lat, lon = _extract_summary(passport)

        print("\n----------------------------------------")
        print(f"File: {filename}")
        print("Candidate for NEW WIGOS ID:")
        print(f"  ETN: {etn_id}")
        print(f"  Name: {name}")
        print(f"  Date: {date}")
        print(f"  Location: ({lat}, {lon})")
        print("----------------------------------------")

        # -----------------------------------------------------------
        # Ask user
        # -----------------------------------------------------------
        if not _ask_confirmation():
            print("Skipped.")
            continue

        # -----------------------------------------------------------
        # Assign WIGOS via OceanOPS request-id API
        # -----------------------------------------------------------
        try:
            new_wigos = request_wigos_id(passport)
        except Exception as exc:
            print(f"Failed to request WIGOS ID for {filename}: {exc}")
            continue

        passport["platform"]["match"]["wigosId"] = new_wigos

        new_filename = f"ETN_{etn_id}_WIGOS_{new_wigos}.json"
        new_filepath = PASSPORT_DIR / new_filename

        try:
            with open(new_filepath, "w") as f:
                json.dump(passport, f, indent=2)

            os.remove(filepath)

            print(f"Assigned → {new_filename}")

        except Exception as e:
            print(f"Failed to assign WIGOS for {filename}: {e}")


if __name__ == "__main__":
    assign_wigos_ids()