from OceanOpsClient import OceanOpsClient

client = OceanOpsClient.from_env()


program = "vliz-arms-mbon"
start_date = "2026-06-15T12:00:00"
longitude = 4.6
latitude = 51.2
model = "Benthic Tripod Custom"

print(client.settings)

test = client.post_get_id(program=program,
                          start_date=start_date,
                          longitude=longitude,
                          latitude=latitude,
                          model=model)
print(test)

