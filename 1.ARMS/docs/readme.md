# ARMS ingestion

## Part 1: pull ARMS metadata from ETN

ARMS data is pulled from ETN with `1.extract_ETN_ARMS.py`.
- Credentials come from `.Renviron`.
- The filter parameters live in the ETN request payload.

The output is `etn_arms_export/deployments_ARMS.json` with the variable fields used downstream:
- deployment_id
- receiver_id
- station_name
- deploy_latitude
- deploy_longitude
- deploy_date_time
- recover_date_time

```mermaid
flowchart TB

A((Operators)) --> B[(ETN service)]
B --> C[1.extract_ETN_ARMS.py]
C --> D[deployments_ARMS.json]
```

## Part 2: create passports

The deployment export is merged with static config from `scripts/config/config_passports.json` in `2.form_passports.py`.
Before writing a file, the script queries OceanOPS by `receiver_id` and program to see whether a matching platform already exists.

- Match found: update the passport payload and write `ETN_*receverId*_WIGOS_*wigosID*.json`
- No match: write `ETN_*receverId*_WIGOS_NONE.json`

```mermaid
flowchart TB

D[deployments_ARMS.json]
E[config_passports.json]
F[2.form_passports.py]

D --> F
E --> F

G{OceanOPS match found?}
F --> G

G -- Yes --> H[Write ETN_*receverId*_WIGOS_*wigosID*.json]
G -- No --> I[Write ETN_*receverId*_WIGOS_NONE.json]

J[(passports/)]
H --> J
I --> J
```

## Part 3: assign WIGOS-ID if missing

`3.assign_missing_wigos.py` scans `passports/` for `WIGOS_NONE` files, asks for confirmation, then requests a real WIGOS ID from OceanOPS and renames the passport.

```mermaid
flowchart TB

J[(passports/)]
K[passport with WIGOS_NONE]
J --> K

L{WIGOS missing?}
K --> L

L -- Yes --> M[Confirm in CLI]
M --> N[Request WIGOS ID]
N --> O[Rename passport file]
O --> J

L -- No --> P[Skip]
```

## Part 4: push passports

`4.push_passports.py` sends each passport from `passports/` to OceanOPS.

```mermaid
flowchart TB

J[(passports/)]
Q[4.push_passports.py]
R[(OceanOPS)]

J --> Q
Q --> R
```