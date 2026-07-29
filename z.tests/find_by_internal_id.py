import json
import requests

endpoint = "https://www.ocean-ops.org/api/data/passports/search"
program_id = "1006434"  # vliz-thornton-buoy
internal_id = "007"

payload = {
    "internalIds": [internal_id],
    "filters": {
        "programs": program_id
    }
}

response = requests.post(endpoint, json=payload, timeout=30)
response.raise_for_status()

print(json.dumps(response.json(), indent=2))

