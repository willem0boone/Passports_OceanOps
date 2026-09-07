import os
import json
from datetime import datetime, timezone
from dateutil import parser

from OceanOpsClient import OceanOpsClient


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------
def _now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_iso(x):
    if x is None or x == "" or (isinstance(x, float) and str(x) == "nan"):
        return None
    try:
        dt = parser.parse(str(x))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


# -------------------------------------------------------------------
# Public helpers
# -------------------------------------------------------------------
def safe_chr(x):
    if x is None or x == "" or (isinstance(x, float) and str(x) == "nan"):
        return None
    return str(x)


def extract_wigos_id(passport):
    """Extract a WIGOS ID from either passport schema returned by OceanOPS."""
    candidates = [
        passport.get("platform", {}).get("match", {}).get("wigosId"),
        passport.get("passport", {}).get("identification", {}).get("passportId"),
        passport.get("passport", {}).get("identification", {}).get("reference"),
        passport.get("identification", {}).get("passportId"),
        passport.get("wigosId"),
    ]

    for candidate in candidates:
        if candidate:
            return str(candidate)

    return None


def request_wigos_id(passport, program="VLIZ-ARMS-MBON"):
    """Request a real WIGOS ID from OceanOPS for the given passport."""
    platform = passport.get("platform", {})
    patch = platform.get("patch", {})
    deployment = patch.get("deployment", {})

    start_date = deployment.get("date")
    latitude = deployment.get("latitude")
    longitude = deployment.get("longitude")

    if not start_date:
        raise ValueError("Passport deployment date is missing; cannot request WIGOS ID")

    try:
        from datetime import datetime
        # OceanOPS expects a plain ISO datetime without timezone suffix.
        normalized_start = start_date.replace("Z", "+00:00")
        start_date = datetime.fromisoformat(normalized_start).strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        start_date = start_date.rstrip("Z")

    try:
        client = OceanOpsClient.from_env()
        result = client.post_get_id(
            program=program,
            start_date=start_date,
            longitude=longitude,
            latitude=latitude,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to request WIGOS ID from OceanOPS: {exc}") from exc

    if isinstance(result, dict):
        for key in ("wigosRef", "wigosId", "wigosID", "wigos_id"):
            value = result.get(key)
            if value:
                return str(value)

        candidate = result.get("platform") or result.get("platformInfo") or {}
        if isinstance(candidate, dict):
            for key in ("wigosRef", "wigosId", "wigosID", "wigos_id"):
                value = candidate.get(key)
                if value:
                    return str(value)

    raise ValueError(f"OceanOPS did not return a WIGOS ID in the response: {result}")


# -------------------------------------------------------------------
# Create passport
# -------------------------------------------------------------------
def create_passport(filepath, json_obj):
    with open(filepath, "w") as f:
        json.dump(json_obj, f, indent=2)
    print(f"Created: {os.path.basename(filepath)}")


# -------------------------------------------------------------------
# Update passport object (in-memory)
# -------------------------------------------------------------------
def apply_passport_updates(passport, csv_row, config):
    """Update passport object with CSV row data and config."""
    
    update_fields = {
        "name": safe_chr(csv_row.get("station_name")),
        "latitude": csv_row.get("deploy_latitude"),
        "longitude": csv_row.get("deploy_longitude"),
        "date": _to_iso(csv_row.get("deploy_date_time")),
        "endDate": _to_iso(csv_row.get("recover_date_time")),
    }

    platform = passport.setdefault("platform", {})
    patch = platform.setdefault("patch", {})

    if "deployment" in patch:
        if update_fields["date"]:
            patch["deployment"]["date"] = update_fields["date"]

        if update_fields["latitude"] is not None:
            patch["deployment"]["latitude"] = update_fields["latitude"]

        if update_fields["longitude"] is not None:
            patch["deployment"]["longitude"] = update_fields["longitude"]

    if "retrieval" in patch and update_fields["endDate"]:
        patch["retrieval"]["endDate"] = update_fields["endDate"]

    if update_fields["name"]:
        patch["name"] = update_fields["name"]

    internal_id = safe_chr(csv_row.get("receiver_id"))
    if internal_id:
        patch.setdefault("identification", {})["internalId"] = internal_id

    passport = apply_config_updates(passport, config)
    
    return passport


# -------------------------------------------------------------------
# Update passport (with change detection on disk)
# -------------------------------------------------------------------
def update_passport(filepath, csv_row, config):

    print(f"Validating changes for: {os.path.basename(filepath)}")

    with open(filepath, "r") as f:
        passport = json.load(f)

    original = json.loads(json.dumps(passport))
    passport = apply_passport_updates(passport, csv_row, config)

    if passport == original:
        print("No changes found.")
        return

    print("Changes detected → updating file")

    with open(filepath, "w") as f:
        json.dump(passport, f, indent=2)

    print(f"Updated: {os.path.basename(filepath)}")


# -------------------------------------------------------------------
# Build new passport
# -------------------------------------------------------------------
def build_full_passport(row, config, wigos_id):

    contact_contributions, agency_contributions = build_contributions(config)
    internal_id = safe_chr(row.get("receiver_id"))

    patch = {
        "name": safe_chr(row.get("station_name")),
        "deployment": {
            "date": _to_iso(row.get("deploy_date_time")),
            "latitude": row.get("deploy_latitude"),
            "longitude": row.get("deploy_longitude"),
        },
        "retrieval": {
            "endDate": _to_iso(row.get("recover_date_time"))
        }
    }

    if internal_id:
        patch["identification"] = {
            "internalId": internal_id
        }

    return {
        "meta": {
            "schemaVersion": config["meta"]["schemaVersion"],
            "sourceText": config["meta"]["sourceText"],
            "ingestionMethodId": config["meta"]["ingestionMethodId"],
            "contactId": config["ingestion"]["contact_id"],
            "observedAt": _now_utc()
        },
        "options": config["options"],
        "platform": {
            "match": {
                "wigosId": wigos_id
            },
            "patch": patch
        },
        "sensorSetups": [],
        "contactContributions": contact_contributions,
        "agencyContributions": agency_contributions
    }


# -------------------------------------------------------------------
# Apply config updates
# -------------------------------------------------------------------
def apply_config_updates(passport, config):

    meta = passport.setdefault("meta", {})
    meta["schemaVersion"] = config["meta"]["schemaVersion"]
    meta["sourceText"] = config["meta"]["sourceText"]
    meta["ingestionMethodId"] = config["meta"]["ingestionMethodId"]
    meta["contactId"] = config["ingestion"]["contact_id"]

    passport["options"] = config["options"]

    # NEW: update contributions
    contact_contributions, agency_contributions = build_contributions(config)

    passport["contactContributions"] = contact_contributions
    passport["agencyContributions"] = agency_contributions

    return passport


def build_contributions(config):
    contact_contributions = []
    agency_contributions = []

    # Contacts
    for key, contact in config.get("contacts", {}).items():
        contact_contributions.append({
            "contactId": contact["id"],
            "roles": contact["roles"]
        })

    # Agency
    agency = config.get("agency")
    if agency:

        agency_contributions.append({
            "agencyId": agency["id"],
            "roles": agency["roles"]
            })

    return contact_contributions, agency_contributions