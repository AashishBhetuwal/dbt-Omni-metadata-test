#!/usr/bin/env python3
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS_DIR = os.path.join(ROOT, "omni")
MANIFEST_PATH = os.path.join(ROOT, "target", "manifest.json")

def collect_pii(manifest):
    pii = {}
    for section in ("sources", "nodes"):
        for _, node in manifest.get(section, {}).items():
            if node.get("resource_type") not in ("source", "model"):
                continue
            name = node.get("name", "").lower()
            cols = (node.get("columns") or {})
            for cname, cdef in cols.items():
                meta = (cdef.get("meta") or {})
                if meta.get("contains_pii") is True:
                    pii.setdefault(name, set()).add(cname.upper())
    return pii

def inject(view_path, pii_cols):
    with open(view_path, "r") as f:
        content = f.read()
    changed = False
    def repl(m):
        nonlocal changed
        before, col, after = m.group(1), m.group(2), m.group(3)
        if col.upper() in pii_cols and "required_access_grants" not in content[m.start():m.end()+120]:
            changed = True
            return f'{before}{col}{after}\n  required_access_grants: [can_see_pii]\n'
        return m.group(0)
    pattern = re.compile(r'(\s+sql:\s*\")([^\"]+)(\")')
    new = pattern.sub(repl, content)
    if changed:
        with open(view_path, "w") as f:
            f.write(new)
    return changed

def main():
    if not os.path.exists(MANIFEST_PATH):
        print(f"Manifest not found at {MANIFEST_PATH}. Run dbt compile/build and copy it here.")
        sys.exit(1)
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    pii_map = collect_pii(manifest)
    if not pii_map:
        print("No PII columns found.")
        return
    changed = 0
    for root, _, files in os.walk(VIEWS_DIR):
        for fname in files:
            if not fname.endswith(".view"):
                continue
            key = fname[:-5].lower()
            cols = pii_map.get(key)
            if not cols:
                continue
            if inject(os.path.join(root, fname), cols):
                print(f"[ok] updated {fname} -> {sorted(list(cols))}")
                changed += 1
    print(f"Done. Files changed: {changed}")

if __name__ == "__main__":
    main()
