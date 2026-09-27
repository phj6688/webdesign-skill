#!/usr/bin/env bash
# Repo verify gate. The default tier needs no browser. --full adds a real
# capture against a local server, to prove the screenshot path still works.
# Exits non-zero on the first failure, naming the step. Mirrors CI.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FULL=0
[ "${1:-}" = "--full" ] && FULL=1
fail() { echo "verify: FAILED at: $1" >&2; exit 1; }

HTTP_PID=""
FULLDIR=""
full_cleanup() {
  if [ -n "$HTTP_PID" ]; then kill "$HTTP_PID" >/dev/null 2>&1 || true; HTTP_PID=""; fi
  if [ -n "$FULLDIR" ] && [ -d "$FULLDIR" ]; then rm -rf "$FULLDIR" || true; fi
}
trap full_cleanup EXIT

# Tracked files plus new files that .gitignore does not exclude. A gate that
# only sees committed files misses the change you are about to commit.
repo_files() {
  git -C "$ROOT" ls-files --cached --others --exclude-standard
}

# Outside a work tree git ls-files prints nothing, and every step built on it
# would pass having checked nothing. Stop before any of them runs.
command -v git >/dev/null 2>&1 \
  || fail "git check (git is not installed, and several steps list files through git ls-files)"
if [ "$(git -C "$ROOT" rev-parse --is-inside-work-tree 2>/dev/null)" != "true" ]; then
  fail "git check ($ROOT is not inside a git work tree, so the git ls-files steps would check nothing; run verify.sh from a git checkout)"
fi

echo "[1] py_compile"
python3 - "$ROOT" <<'PY' || fail "py_compile"
import os, py_compile, sys, tempfile
root = sys.argv[1]
base = os.path.join(root, "skills", "webdesign")
bad = count = 0
with tempfile.TemporaryDirectory() as td:
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", "node_modules", ".git"}]
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            count += 1
            try:
                py_compile.compile(path, cfile=os.path.join(td, name + "c"), doraise=True)
            except Exception as exc:
                print(f"  {os.path.relpath(path, root)}: {exc}")
                bad += 1
print(f"  compiled {count} python file(s)")
sys.exit(1 if bad else 0)
PY

echo "[2] linter fixture suite"
python3 "$ROOT/skills/webdesign/tests/run_fixtures.py" >/dev/null || fail "run_fixtures"
echo "  every rule fires on its bad fixture and stays quiet on its good one"

echo "[3] contrast suite"
python3 "$ROOT/skills/webdesign/tests/test_contrast.py" >/dev/null || fail "test_contrast"
echo "  WCAG reference values, archetype palettes and error paths all hold"

echo "[4] JSON manifests"
python3 - "$ROOT" <<'PY' || fail "manifests"
import json, os, subprocess, sys
root = sys.argv[1]
files = subprocess.run(["git", "-C", root, "ls-files", "--cached", "--others", "--exclude-standard"],
                       capture_output=True, text=True).stdout.split()
bad = 0
for rel in files:
    if not rel.endswith(".json"):
        continue
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        continue
    try:
        json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        print(f"  invalid JSON {rel}: {exc}")
        bad += 1
manifest = os.path.join(root, ".claude-plugin/plugin.json")
if not os.path.isfile(manifest):
    print("  .claude-plugin/plugin.json is missing")
    sys.exit(1)
data = json.load(open(manifest, encoding="utf-8"))
for key in ("name", "version", "skills"):
    if not data.get(key):
        print(f"  manifest missing '{key}'")
        bad += 1
skills = data.get("skills")
if skills and not os.path.exists(os.path.join(root, skills.lstrip("./"))):
    print(f"  manifest skills path '{skills}' does not exist")
    bad += 1
sys.exit(1 if bad else 0)
PY

echo "[5] SKILL.md frontmatter"
python3 - "$ROOT" <<'PY' || fail "frontmatter"
import os, sys
root = sys.argv[1]
try:
    import yaml
    def parse(text):
        return yaml.safe_load(text) or {}
except ImportError:
    # Minimal top level parser, so the gate never depends on a pip install.
    def parse(text):
        data = {}
        for line in text.splitlines():
            if not line or line[0] in " \t#" or ":" not in line:
                continue
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip("'\"")
        return data
found = bad = 0
for dirpath, dirnames, filenames in os.walk(os.path.join(root, "skills")):
    dirnames[:] = [d for d in dirnames if d not in {"__pycache__", "node_modules", ".git"}]
    if "SKILL.md" not in filenames:
        continue
    path = os.path.join(dirpath, "SKILL.md")
    rel = os.path.relpath(path, root)
    found += 1
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        print(f"  {rel}: missing YAML frontmatter")
        bad += 1
        continue
    parts = text.split("---", 2)
    if len(parts) < 3:
        print(f"  {rel}: frontmatter is not closed")
        bad += 1
        continue
    try:
        data = parse(parts[1])
    except Exception as exc:
        print(f"  {rel}: invalid frontmatter YAML: {exc}")
        bad += 1
        continue
    for key in ("name", "description"):
        if not data.get(key):
            print(f"  {rel}: frontmatter missing '{key}'")
            bad += 1
    print(f"  OK: {rel}")
if not found:
    print("  no SKILL.md found under skills/")
    sys.exit(1)
sys.exit(1 if bad else 0)
PY

echo "[6] dash ban (md, sh, py, json, yml, yaml)"
python3 - "$ROOT" <<'PY' || fail "dash ban (no em dash or en dash in md, sh, py, json, yml, yaml)"
import os, subprocess, sys
root = sys.argv[1]
files = subprocess.run(["git", "-C", root, "ls-files", "--cached", "--others", "--exclude-standard"],
                       capture_output=True, text=True).stdout.split("\n")
bad = 0
for rel in files:
    rel = rel.strip()
    if not rel.endswith((".md", ".sh", ".py", ".json", ".yml", ".yaml")):
        continue
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        continue
    with open(path, encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            for char, name in ((chr(0x2014), "em dash"), (chr(0x2013), "en dash")):
                if char in line:
                    print(f"  {rel}:{number}: {name}")
                    bad += 1
print(f"  {bad} offending line(s)")
sys.exit(1 if bad else 0)
PY

echo "[7] ruff"
if command -v ruff >/dev/null 2>&1; then
  (cd "$ROOT" && ruff check .) || fail "ruff"
else
  echo "  ruff absent, skipped"
fi

echo "[8] shellcheck"
if command -v shellcheck >/dev/null 2>&1; then
  mapfile -t sh < <(repo_files | grep '\.sh$' || true)
  if [ "${#sh[@]}" -gt 0 ]; then
    (cd "$ROOT" && shellcheck "${sh[@]}") || fail "shellcheck"
    echo "  ${#sh[@]} script(s) clean"
  else
    echo "  no shell scripts found"
  fi
else
  echo "  shellcheck absent, skipped"
fi

echo "[9] reference links"
python3 - "$ROOT" <<'PY' || fail "reference links"
import os, re, sys
root = sys.argv[1]
base = os.path.join(root, "skills", "webdesign")
link = re.compile(r"\]\(([^)]+)\)")
bad = checked = 0
for dirpath, dirnames, filenames in os.walk(base):
    dirnames[:] = [d for d in dirnames if d not in {"__pycache__", "node_modules", ".git"}]
    for name in sorted(filenames):
        if not name.endswith(".md"):
            continue
        path = os.path.join(dirpath, name)
        text = open(path, encoding="utf-8", errors="replace").read()
        for match in link.finditer(text):
            target = match.group(1).strip()
            if ' "' in target:
                target = target.split(' "', 1)[0].strip()
            target = target.strip("<>")
            # A site absolute path is not a repo path, so it is out of scope.
            if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            checked += 1
            resolved = os.path.normpath(os.path.join(dirpath, target))
            if not os.path.exists(resolved):
                line = text[: match.start()].count("\n") + 1
                print(f"  {os.path.relpath(path, root)}:{line}: dead link -> {target}")
                bad += 1
print(f"  {checked} local link(s) checked")
sys.exit(1 if bad else 0)
PY

if [ "$FULL" = "1" ]; then
  echo "[10] full tier: real capture, three widths, both schemes"
  SHOOT="$ROOT/skills/webdesign/scripts/shoot.sh"
  [ -x "$SHOOT" ] || fail "shoot.sh is missing or not executable"

  FULLDIR="$(mktemp -d "${TMPDIR:-/tmp}/webdesign-verify-XXXXXX")" || fail "mktemp"
  mkdir -p "$FULLDIR/site" "$FULLDIR/shots"
  cat > "$FULLDIR/site/index.html" <<'HTML'
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>verify target</title>
<style>
  body { margin:0; background:#f2efe6; color:#15120b; font-family:monospace; }
  @media (prefers-color-scheme: dark) { body { background:#15120b; color:#ece0c8; } }
  header { padding:3rem 1rem; background:#f0a82a; color:#15120b; font-size:2rem; }
  .card { border:1px solid #f0a82a; padding:1rem; margin:1rem; }
</style></head>
<body><header>verify target</header>
<div class="card">one</div><div class="card">two</div><div class="card">three</div>
</body></html>
HTML

  PORT="$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')" \
    || fail "cannot pick a free port"
  python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$FULLDIR/site" >/dev/null 2>&1 &
  HTTP_PID=$!

  python3 - "$PORT" <<'PY' || fail "the local test server never came up"
import socket, sys, time
port = int(sys.argv[1])
for _ in range(80):
    try:
        with socket.create_connection(("127.0.0.1", port), 0.25):
            sys.exit(0)
    except OSError:
        time.sleep(0.25)
sys.exit(1)
PY

  "$SHOOT" "http://127.0.0.1:$PORT/index.html" --out "$FULLDIR/shots" \
    --label verify --console || fail "shoot.sh capture"

  shots="$(find "$FULLDIR/shots" -name '*.png' -size +1000c | wc -l)"
  [ "$shots" -eq 3 ] || fail "full tier expected 3 real PNGs, found $shots"
  echo "  3 real PNGs captured and checked"

  mkdir -p "$FULLDIR/schemes"
  "$SHOOT" "http://127.0.0.1:$PORT/index.html" --out "$FULLDIR/schemes" \
    --label verify --scheme both || fail "shoot.sh --scheme both"
  shots="$(find "$FULLDIR/schemes" -name '*.png' -size +1000c | wc -l)"
  [ "$shots" -eq 6 ] || fail "--scheme both expected 6 real PNGs, found $shots"
  # Identical light and dark files would mean the emulation silently did nothing,
  # and every dark-mode check built on those shots would be checking light mode.
  if cmp -s "$FULLDIR/schemes/verify-light-1280x800.png" "$FULLDIR/schemes/verify-dark-1280x800.png"; then
    fail "light and dark shots are byte-identical, scheme emulation did not apply"
  fi
  echo "  6 real PNGs across both schemes, light and dark differ"
  full_cleanup
fi

echo "verify: OK"
