# Superstore: dbt (metadata-only) + Omni views + PII bridge

Use dbt only for column metadata; keep modeling in Omni.

## Includes
- dbt/: `sources.yml` for all Superstore tables (no joins/models). CUSTOMER is tagged PII.
- omni/: `.view` files for CUSTOMERS, ORDERS, PEOPLE, PRODUCTS, RETURNS, SALES and a model with `access_grants`.
- scripts/: `manifest_to_omni.py` to add `required_access_grants` into Omni views from dbt meta.

## Steps
1) In dbt Cloud, connect the dbt/ folder repo. Set creds (Database SUPERSTORE_DATA; role with SELECT on SUPERSTORE).
2) Run **Compile** or **Build** once. Download `target/manifest.json`.
3) In your Omni model repo, add omni/ files. Create a user attribute `can_see_pii` and set it to "true" for yourself.
4) Copy `manifest.json` into the repo at `./target/manifest.json`. Run:
   `python scripts/manifest_to_omni.py`
5) Open Omni Explore and confirm the `customer` field is hidden for users without the grant.
