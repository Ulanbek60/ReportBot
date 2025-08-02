import json

with open("google_credentials.json", "r") as f:
    data = json.load(f)

data["private_key"] = data["private_key"].replace("\n", "\\n")

with open("google_credentials.json", "w") as f:
    json.dump(data, f, indent=2)
