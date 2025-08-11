# Metadata-only dbt + Omni starter (no joins)

Goal: Keep **all modeling in Omni**, use dbt **only** to store column metadata (`meta.contains_pii: true`)
for your **existing Snowflake tables**. We'll read dbt's `manifest.json` and update Omni views automatically.

## What this does
- Declares the existing table `SUPERSTORE_DATA.SUPERSTORE.CUSTOMERS` as a **dbt source**
- Flags the `CUSTOMER` column with `meta.contains_pii: true`
- No models, no new tables — your analytics still query the original table
- A small bridge script reads dbt's manifest (source nodes) and adds
  `required_access_grants: [can_see_pii]` to `customers.view` in Omni

## Steps

### 1) In dbt Cloud
1. Create a project connected to this Git repo (after you upload it).
2. Set Snowflake creds (Database: SUPERSTORE_DATA; Schema can be any build schema, but we won't create objects).
3. Open the IDE and run **Compile** or **Build** once — this generates `target/manifest.json` with source column metadata.

### 2) In Omni model repo
1. Add `omni/model.yml` (contains `access_grants`)
2. Add `omni/views/customers.view` (points at your existing table)
3. Run the bridge script:
   ```bash
   python scripts/manifest_to_omni.py
   ```
   It finds source columns with `meta.contains_pii: true` and injects
   `required_access_grants: [can_see_pii]` under matching dimensions in `customers.view`.

### 3) Test
- In Omni, set a user attribute `can_see_pii=true` for yourself.
- Open a chart with the `customer` dimension. Toggle the user attribute off/on to see the field hide/show.
- (Optional) Add Snowflake masking policy if you also want DB-layer masking.

