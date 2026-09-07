import json
import requests

endpoint = "https://www.ocean-ops.org/api/data/passports/search"
program_id = "1006434"  # vliz-thornton-buoy


payload = {
    "ptfIds": [1305758],
    # "filters": {
    #     "programs": program_id
    # }
}

response = requests.post(endpoint, json=payload, timeout=30)
response.raise_for_status()

print(json.dumps(response.json(), indent=2))