"""
Demo script for OceanOpsClient.post_get_id() method.

This demonstrates how to request a single platform identifier from OceanOPS
using deployment information.
"""

from OceanOpsClient import OceanOpsClient
from pprint import pprint
import json
from datetime import datetime
import os

# Load credentials from .env file manually
API_KEY_ID = "1382"
API_KEY_TOKEN = "_3EQGERnB2Nv9EJqNUzj2C0sHv0"

# Initialize client with credentials
client = OceanOpsClient.from_credentials(API_KEY_ID, API_KEY_TOKEN)

# Example 1: Request WIGOS ID for an ARMS deployment
print("=" * 70)
print("Example 1: Request WIGOS ID for ARMS deployment")
print("=" * 70)

result = client.post_get_id(
    program="VLIZ-ARMS-MBON",
    start_date="2024-07-18T09:11:00Z",
    model="VR2AR",
    batch_status="IN STOCK",
    longitude=2.9959,
    latitude=51.5806
)

print("\nResponse:")
pprint(result)

# Save result to file
with open("post_get_id_response.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4)
print("\nSaved to post_get_id_response.json")

# Example 2: Request WIGOS ID for another deployment
print("\n" + "=" * 70)
print("Example 2: Request WIGOS ID for TBR800 deployment")
print("=" * 70)

result2 = client.post_get_id(
    program="VLIZ-ARMS-MBON",
    start_date="2024-01-30T11:52:00Z",
    model="TBR800",
    batch_status="IN STOCK",
    longitude=2.9959,
    latitude=51.5806
)

print("\nResponse:")
pprint(result2)

# Example 3: With ISO format date
print("\n" + "=" * 70)
print("Example 3: Request with today's date")
print("=" * 70)

today_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
result3 = client.post_get_id(
    program="VLIZ-ARMS-MBON",
    start_date=today_iso,
    model="VR2AR",
    batch_status="IN STOCK",
    longitude=2.9955,
    latitude=51.5798
)

print(f"\nRequest date: {today_iso}")
print("Response:")
pprint(result3)
