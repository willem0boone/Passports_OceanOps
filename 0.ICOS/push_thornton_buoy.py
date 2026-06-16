from pprint import pprint
from OceanOpsClient import OceanOpsClient

client = OceanOpsClient.from_env()

# passport = "passport_thornton_buoy_operational.json"
# passport = "passport_thornthon_buoy_comment.json"
passport = "passport_thornton_buoy_extid.json"


status = client.validate_passport_json(passport)
pprint(status)


m = client.post_passport(passport, dry_run=False)
pprint(m)
