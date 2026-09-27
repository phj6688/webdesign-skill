#!/usr/bin/env bash
# Fetch one reference design system from VoltAgent/awesome-design-md at a pinned
# commit. Pinned, because an unpinned fetch makes the same prompt produce a different
# page next month. Allowlisted, because the slug becomes part of a URL and a path.
set -euo pipefail

PIN="f6961238d5cddcf8042a74a70fc400ec67181abb"
REPO="VoltAgent/awesome-design-md"
OUT=".design-ref"

SLUGS=(
  airbnb airtable apple binance bmw bmw-m bugatti cal claude clay clickhouse cohere
  coinbase composio cursor dell-1996 elevenlabs expo ferrari figma framer hashicorp
  hp ibm intercom kraken lamborghini linear.app lovable mastercard meta minimax
  mintlify miro mistral.ai mongodb nike nintendo-2001 notion nvidia ollama
  opencode.ai pinterest playstation posthog raycast renault replicate resend
  revolut runwayml sanity sentry shopify slack spacex spotify starbucks stripe
  supabase superhuman tesla theverge together.ai uber vercel vodafone voltagent
  warp webflow wired wise x.ai zapier
)

usage() {
  cat <<'EOF'
Usage: fetch_system.sh <slug> [--out DIR] [--sha COMMIT]
       fetch_system.sh --list

Downloads design-md/<slug>/DESIGN.md from VoltAgent/awesome-design-md into
<out>/<slug>.DESIGN.md. The default output directory is .design-ref/.

Each file describes the publicly visible styling of a real brand's site. Read it
for technique: the shape of the type ramp, the elevation ladder, the component
structure. Do not ship a page that a visitor could mistake for that brand.
Proprietary typefaces named in the file are not licensed by it. Use the
substitute the file names in its font section.
EOF
}

is_slug() {
  local want="$1" s
  for s in "${SLUGS[@]}"; do
    [ "$s" = "$want" ] && return 0
  done
  return 1
}

slug=""
sha="$PIN"
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --list) printf '%s\n' "${SLUGS[@]}"; exit 0 ;;
    --out) OUT="${2:?--out needs a directory}"; shift 2 ;;
    --sha) sha="${2:?--sha needs a commit}"; shift 2 ;;
    -*) echo "fetch_system: unknown flag: $1" >&2; usage >&2; exit 1 ;;
    *) slug="$1"; shift ;;
  esac
done

if [ -z "$slug" ]; then
  usage >&2
  exit 1
fi
if ! is_slug "$slug"; then
  echo "fetch_system: '$slug' is not a known system. Run with --list." >&2
  exit 1
fi
# Test the whole value at once. grep matches line by line, so a value with an
# embedded newline passed when any single line looked like a commit id.
if ! [[ $sha =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "fetch_system: --sha must be a hex commit id" >&2
  exit 1
fi

mkdir -p "$OUT"
dest="$OUT/$slug.DESIGN.md"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

url="https://raw.githubusercontent.com/$REPO/$sha/design-md/$slug/DESIGN.md"
if ! curl -fsSL --max-time 30 "$url" -o "$tmp"; then
  echo "fetch_system: download failed: $url" >&2
  exit 1
fi

# A 404 page or an empty body must not land as if it were a design system.
bytes="$(wc -c < "$tmp" | tr -d ' ')"
if [ "$bytes" -lt 2000 ] || ! grep -q '^#' "$tmp"; then
  echo "fetch_system: response for '$slug' does not look like a DESIGN.md ($bytes bytes)" >&2
  exit 1
fi

mv "$tmp" "$dest"
chmod 644 "$dest"
trap - EXIT
echo "fetched $slug -> $dest ($bytes bytes, $REPO@${sha:0:12})"
echo "note: reference for technique only. Rename the tokens and swap proprietary fonts."
