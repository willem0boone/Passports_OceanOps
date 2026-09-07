from OceanOpsClient import OceanOpsClient
from pprint import pprint
import json

client = OceanOpsClient.from_env()


resp = client.get_platform(ptfWigosId="0-22000-0-6204817")
pprint(resp)

with open("return_thronton.json", "w", encoding='utf-8') as f:
    json.dump(resp, f,  indent=4)
