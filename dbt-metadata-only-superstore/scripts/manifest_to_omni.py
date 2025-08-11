#!/usr/bin/env python3
"""
Read dbt manifest.json, find columns with meta.contains_pii == true from **sources** and **models**,
and add `required_access_grants: [can_see_pii]` to matching fields in Omni .view files.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS_DIR = os.path.join(ROOT, "omni", "views")
MANIFEST_PATH = os.path.join(ROOT, "target", "manifest.json")  # dbt output

def collect_pii(manifest):
    pii = {}  # name_lower -> set(upper_colnames)
    for section in ("sources", "nodes"):
        for _, node in manifest.get(section, {}).items():
            rtype = node.get("resource_type")
            if rtype not in ("source", "model"):
                continue
            name = node.get("name", "")
            if not name:
                continue
            cols = node.get("columns", {}) or {}
            for colname, cdef in cols.items():
                meta = (cdef.get("meta") or {})
                if meta.get("contains_pii") is True:
                    pii.setdefault(name.lower(), set()).add(colname.upper())
    return pii

def inject(view_path, pii_cols):
    with open(view_path, "r") as f:
        content = f.read()
    changed = False
    def repl(m):
        nonlocal changed
        sql_line = m.group(0)
        col = m.group(2).upper()
        if col in pii_cols and "required_access_grants" not in sql_line:
            changed = True
            return m.group(1) + m.group(2) + m.group(3) + "\n    required_access_grants: [can_see_pii]\n"
        return sql_line
    pattern = re.compile(r'(\s+sql:\s*\")([^\"]+)(\")')
    new = pattern.sub(repl, content)
    if changed:
        with open(view_path, "w") as f:
            f.write(new)
    return changed

def main():
    if not os.path.exists(MANIFEST_PATH):
        print(f"Manifest not found at {MANIFEST_PATH}. Run dbt compile/build first.")
        sys.exit(1)
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    pii_map = collect_pii(manifest)
    if not pii_map:
        print("No PII columns found.")
        return
    total = 0
    for name_lower, cols in pii_map.items():
        view_file = os.path.join(VIEWS_DIR, f"{name_lower}.view")
        if not os.path.exists(view_file):
            print(f"[skip] No Omni view for {name_lower}: {view_file}")
            continue
        if inject(view_file, cols):
            print(f"[ok] Updated {view_file} -> PII: {sorted(cols)}")
            total += 1
        else:
            print(f"[noop] {view_file} unchanged")
    print(f"Done. Files changed: {total}")

if __name__ == "__main__":
    main()
