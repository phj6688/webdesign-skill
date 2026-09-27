#!/usr/bin/env bash
# Capture one URL at several viewports with the Playwright CLI.
#
# Written for a headless Linux host with no system Chrome, so the browser is
# always pinned to the bundled chromium build and the session never runs headed.
# Every PNG is size-checked and signature-checked afterwards, because a clean
# exit code from a browser says nothing about whether the page actually painted.
#
# Exit 3 stays apart from exit 1 on purpose. Exit 1 means the page or the URL
# needs a fix. Exit 3 means this host cannot fetch or start the browser at all,
# and no page fix or other browser changes that, so the caller must stop.
set -euo pipefail

SCRIPT_NAME="${0##*/}"
DEFAULT_VIEWPORTS="375x812,768x1024,1280x800"
# Pinned, because this script parses the CLI's free-text output. An unpinned
# upgrade that rewords a line would break the checks below without an error.
PINNED_CLI="@playwright/cli@0.1.21"

URL=""
OUT_DIR="./shots"
VIEWPORT_ARG="$DEFAULT_VIEWPORTS"
LABEL=""
WANT_CONSOLE=0
FULL_PAGE=1
SCHEME_ARG=""
REDUCED_MOTION=0

RUNNER=()
RUNNER_LABEL=""
SESSION=""
SESSION_OPEN=0
WORKDIR=""
START_CWD="$PWD"
HTTP_STATUS=""

usage() {
  cat <<'USAGE'
shoot.sh - screenshot one URL at several viewports, then prove the files are real.

Usage:
  shoot.sh <url> [options]

Options:
  --out DIR            directory for the PNG files. Default: ./shots
  --viewports LIST     comma separated WxH list. Default: 375x812,768x1024,1280x800
  --label NAME         file name prefix. Default: a slug of the URL host and path
  --console            also write browser console output per viewport
  --full-page          capture the whole scrollable page. This is the default
  --no-full-page       capture only the visible viewport
  --scheme MODE        emulate prefers-color-scheme: light, dark, or both.
                       Default: no emulation, the browser default
  --reduced-motion     emulate prefers-reduced-motion: reduce for every shot
  -h, --help           print this help and exit 0

Output:
  <out>/<label>[-<scheme>][-reduced]-<w>x<h>.png
  <out>/<label>[-<scheme>][-reduced]-<w>x<h>.console.txt   (only with --console)

Exit status:
  0  every shot is a real PNG
  1  a shot failed: fix the page or the URL, then run it again
  2  bad command line
  3  this environment cannot take screenshots: stop, and report the page as
     not screenshotted. No other browser or workaround will help here

Notes:
  The URL must carry a scheme, for example http://127.0.0.1:8080/ or file:///tmp/a.html.
  Console errors never fail the run. A missing or tiny PNG, or an HTTP status of
  400 or above, always fails the run.
  The project's own node_modules/.bin/playwright runs the capture only when it can
  do everything the run needs. Otherwise the pinned standalone CLI runs through
  npx, and one line says why.
  Exit 3 means the pinned CLI or its chromium cannot be downloaded or started
  on this host, for example with no npm registry access, no npx, or missing
  system libraries.
USAGE
}

die_usage() {
  printf '%s: %s\n\n' "$SCRIPT_NAME" "$1" >&2
  usage >&2
  exit 2
}

die() {
  printf '%s: %s\n' "$SCRIPT_NAME" "$1" >&2
  exit 1
}

# Exit 3 tells the caller to stop and report, because nothing it changes in the
# page, and no other browser, can capture on a host that cannot run this one.
cannot_capture() {
  printf '%s: CANNOT CAPTURE IN THIS ENVIRONMENT: %s\n' "$SCRIPT_NAME" "$1" >&2
  printf '%s: no screenshot can be taken here. Do not try another browser or a workaround.\n' \
    "$SCRIPT_NAME" >&2
  printf '%s: report that the page was not screenshotted, and list what the shots would have checked.\n' \
    "$SCRIPT_NAME" >&2
  exit 3
}

# Closes the browser session and drops the scratch directory. Runs twice on a
# signal, so every step tolerates being repeated.
cleanup() {
  if [ "$SESSION_OPEN" = "1" ] && [ "${#RUNNER[@]}" -gt 0 ]; then
    SESSION_OPEN=0
    "${RUNNER[@]}" -s="$SESSION" close >/dev/null 2>&1 || true
  fi
  if [ -n "$WORKDIR" ] && [ -d "$WORKDIR" ]; then
    rm -rf "$WORKDIR" || true
  fi
}

trap cleanup EXIT
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --out) [ "$#" -ge 2 ] || die_usage "--out needs a directory"; OUT_DIR="$2"; shift 2 ;;
    --out=*) OUT_DIR="${1#*=}"; shift ;;
    --viewports) [ "$#" -ge 2 ] || die_usage "--viewports needs a list"; VIEWPORT_ARG="$2"; shift 2 ;;
    --viewports=*) VIEWPORT_ARG="${1#*=}"; shift ;;
    --label) [ "$#" -ge 2 ] || die_usage "--label needs a name"; LABEL="$2"; shift 2 ;;
    --label=*) LABEL="${1#*=}"; shift ;;
    --console) WANT_CONSOLE=1; shift ;;
    --full-page) FULL_PAGE=1; shift ;;
    --no-full-page) FULL_PAGE=0; shift ;;
    --scheme) [ "$#" -ge 2 ] || die_usage "--scheme needs light, dark or both"; SCHEME_ARG="$2"; shift 2 ;;
    --scheme=*) SCHEME_ARG="${1#*=}"; shift ;;
    --reduced-motion) REDUCED_MOTION=1; shift ;;
    --) shift; [ "$#" -eq 0 ] || { [ -z "$URL" ] || die_usage "only one url is supported"; URL="$1"; shift; } ;;
    -*) die_usage "unknown option: $1" ;;
    *) [ -z "$URL" ] || die_usage "only one url is supported"; URL="$1"; shift ;;
  esac
done

[ -n "$URL" ] || die_usage "a url is required"
case "$URL" in
  http://*|https://*) ;;
  # The CLI blocks the file: protocol unless this is set. Only a file:// run
  # sets it, so an http run keeps the default block on local file access.
  file://*) export PLAYWRIGHT_MCP_ALLOW_UNRESTRICTED_FILE_ACCESS=1 ;;
  *) die_usage "the url must start with http://, https:// or file://" ;;
esac

# The CLI accepts only light or dark for the scheme, so "both" expands here
# rather than being passed through.
case "$SCHEME_ARG" in
  "") SCHEMES=("") ;;
  light|dark) SCHEMES=("$SCHEME_ARG") ;;
  both) SCHEMES=(light dark) ;;
  *) die_usage "bad --scheme '$SCHEME_ARG', expected light, dark or both" ;;
esac

IFS=',' read -r -a VIEWPORTS <<< "$VIEWPORT_ARG"
[ "${#VIEWPORTS[@]}" -gt 0 ] || die_usage "--viewports produced no entries"
for vp in "${VIEWPORTS[@]}"; do
  [[ "$vp" =~ ^[0-9]+x[0-9]+$ ]] || die_usage "bad viewport '$vp', expected WxH like 1280x800"
done

# Keeps a label safe as a file name component, whether it came from the URL or
# from --label. The optional second argument caps the length. Edge hyphens go
# last, after that cut, because a cut that ends on a hyphen would leave one to
# double up against the -WxH suffix.
sanitize() {
  local s
  s="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9._-' '-' | tr -s '-')"
  if [ -n "${2:-}" ]; then
    s="${s:0:$2}"
  fi
  s="${s#-}"
  printf '%s' "${s%-}"
}

slug_from_url() {
  local u="$1"
  u="${u#*://}"
  u="${u%%\?*}"
  u="${u%%#*}"
  u="${u%/}"
  sanitize "$u" 60
}

if [ -n "$LABEL" ]; then
  LABEL="$(sanitize "$LABEL")"
else
  LABEL="$(slug_from_url "$URL")"
fi
[ -n "$LABEL" ] || LABEL="page"
MOTION_TAG=""
[ "$REDUCED_MOTION" = "1" ] && MOTION_TAG="-reduced"

mkdir -p "$OUT_DIR" || die "cannot create the output directory '$OUT_DIR'"
OUT_ABS="$(cd "$OUT_DIR" && pwd)"

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/shoot-XXXXXX")"

# Every CLI command this run calls. A runner that lacks one prints its help
# halfway through the run and fails there.
REQUIRED_COMMANDS=(open resize reload screenshot console close)
if [ -n "$SCHEME_ARG" ]; then
  REQUIRED_COMMANDS+=(set-color-scheme)
fi
if [ "$REDUCED_MOTION" = "1" ]; then
  REQUIRED_COMMANDS+=(set-reduced-motion)
fi

# A project that ships its own Playwright wins, so the capture matches the
# version the project tests with, but only when it can do the whole run.
# Playwright 1.60 has the cli without the emulation commands, and no release
# before 1.62 prints the HTTP status line that the per-shot status check
# reads. Otherwise the run uses the pinned standalone CLI, never an unpinned
# download, and one line says why.
resolve_runner() {
  local local_pw="$START_CWD/node_modules/.bin/playwright"
  local version="" help="" cmd why gaps=() missing=()
  if [ -x "$local_pw" ]; then
    # Both probes run in scratch space, so nothing lands in the user's repo.
    version="$(cd "$WORKDIR" && "$local_pw" --version 2>/dev/null)" || version=""
    version="${version#Version }"
    if [[ $version =~ ^([0-9]+)\.([0-9]+) ]]; then
      if (( BASH_REMATCH[1] < 1 || (BASH_REMATCH[1] == 1 && BASH_REMATCH[2] < 62) )); then
        gaps+=("$version prints no HTTP status line, 1.62 is the first that does")
      fi
    else
      gaps+=("its version is unreadable")
    fi
    help="$(cd "$WORKDIR" && "$local_pw" cli --help 2>/dev/null)" || help=""
    for cmd in "${REQUIRED_COMMANDS[@]}"; do
      grep -Eq "^  $cmd( |\$)" <<< "$help" || missing+=("$cmd")
    done
    if [ "${#missing[@]}" -gt 0 ]; then
      gaps+=("its cli lacks ${missing[*]}")
    fi
    if [ "${#gaps[@]}" -eq 0 ]; then
      RUNNER=("$local_pw" cli)
      RUNNER_LABEL="project-local node_modules/.bin/playwright cli $version"
      return 0
    fi
    why="$(printf '%s; ' "${gaps[@]}")"
    printf '%s: skipping the project-local playwright (%s), using the pinned %s\n' \
      "$SCRIPT_NAME" "${why%; }" "$PINNED_CLI" >&2
  fi
  # Without npx, or the node that runs it, the pinned CLI cannot start at all.
  command -v npx >/dev/null 2>&1 || cannot_capture "npx is not installed or not on PATH"
  command -v node >/dev/null 2>&1 \
    || cannot_capture "node is not installed or not on PATH, and npx needs it"
  RUNNER=(npx --yes "$PINNED_CLI")
  RUNNER_LABEL="npx $PINNED_CLI (standalone)"
}

resolve_runner

pw() {
  "${RUNNER[@]}" -s="$SESSION" "$@"
}

# Runs one CLI command quietly and replays the output only when it fails, so a
# broken step is readable without burying the summary in browser chatter.
pw_quiet() {
  local log="$WORKDIR/pw-last.log"
  if pw "$@" >"$log" 2>&1; then
    return 0
  fi
  printf '%s: playwright step failed: %s\n' "$SCRIPT_NAME" "$*" >&2
  sed 's/^/  | /' "$log" >&2
  return 1
}

console_errors_from_log() {
  local log="$1" n
  n="$(sed -n 's/.*Console: \([0-9][0-9]*\) errors.*/\1/p' "$log" | head -n1)"
  [ -n "$n" ] || n=0
  printf '%s' "$n"
}

# The CLI prints "- HTTP status: <code> <text>" in its Page section when the
# main document answered outside 2xx, and no such line on success. A reply
# without a Page section reports no change, so the last status stands.
note_http_status() {
  grep -q '^### Page' "$1" || return 0
  HTTP_STATUS="$(sed -n 's/^- HTTP status: \([0-9][0-9]*\).*/\1/p' "$1" | head -n1)"
}

png_bytes() {
  wc -c < "$1" | tr -d ' '
}

# Guards against the blank or truncated file a browser leaves behind when the
# render never completed.
png_is_real() {
  local f="$1" sig
  [ -f "$f" ] || return 1
  [ "$(png_bytes "$f")" -gt 1000 ] || return 1
  sig="$(od -An -N4 -tx1 < "$f" | tr -d ' \n')"
  [ "$sig" = "89504e47" ]
}

# Prints a one-line reason and succeeds when a failed open shows that this host
# cannot fetch or start the CLI or its browser at all. Prints nothing and fails
# when the page or the URL is at fault. Every signal matches in any case.
environment_blocker() {
  local log="$1" code=""
  # A navigation error means the browser started, so this host can capture.
  if grep -qi 'net::ERR_' "$log"; then
    return 1
  fi
  code="$(grep -m1 -Eio \
    'npm (error|err!) code (e403|enotfound|eai_again|econnrefused|etimedout|err_socket[a-z_]*)' \
    "$log")" || code=""
  if [ -n "$code" ]; then
    printf 'the npm registry is unreachable (npm %s)' "${code##* }"
    return 0
  fi
  if grep -Eqi 'npm (error|err!) network|403 forbidden - get https://registry\.npmjs\.org' "$log"; then
    printf 'the npm registry is unreachable (npm network error)'
    return 0
  fi
  code="$(grep -m1 -Eio 'err_socket[a-z_]*' "$log")" || code=""
  if [ -n "$code" ]; then
    printf 'the capture tool hit a socket error (%s)' "${code%%$'\n'*}"
    return 0
  fi
  if grep -Eqi 'host system is missing dependencies|error while loading shared libraries' "$log"; then
    printf 'chromium cannot start, the host is missing system libraries it needs'
    return 0
  fi
  if grep -qi 'missing x server' "$log"; then
    printf 'chromium asked for a display, and this host has none'
    return 0
  fi
  return 1
}

SESSION="shoot-$$-$RANDOM"

printf '%s: runner   %s\n' "$SCRIPT_NAME" "$RUNNER_LABEL"
printf '%s: url      %s\n' "$SCRIPT_NAME" "$URL"
printf '%s: out      %s\n' "$SCRIPT_NAME" "$OUT_ABS"
printf '%s: label    %s\n' "$SCRIPT_NAME" "$LABEL"
printf '%s: session  %s\n' "$SCRIPT_NAME" "$SESSION"

OPEN_ARGS=(open "$URL" --browser=chromium)
if [ -f "$START_CWD/.playwright/cli.config.json" ]; then
  OPEN_ARGS+=("--config=$START_CWD/.playwright/cli.config.json")
fi

# The CLI writes snapshots and console logs into .playwright-cli under the
# current directory, so run it from scratch space instead of the user's repo.
cd "$WORKDIR"

# Sorts a failed open into its exit status: 3 when this host cannot fetch or
# start the browser, 1 when the page or the URL is at fault.
open_failed() {
  local reason
  if reason="$(environment_blocker "$WORKDIR/pw-last.log")"; then
    # An npm error means the CLI never started, so no session exists, and a
    # close through npx would only repeat the failed download.
    if grep -Eqi '^npm (error|err!) ' "$WORKDIR/pw-last.log"; then
      SESSION_OPEN=0
    fi
    cannot_capture "$reason"
  fi
  die "cannot open $URL in headless chromium"
}

SESSION_OPEN=1
if ! pw_quiet "${OPEN_ARGS[@]}"; then
  # Only a missing browser build earns a retry. A host that cannot capture is
  # ruled out first, because its missing-library error suggests running
  # "playwright install-deps", which the retry pattern would match. A bad URL
  # or a dead host must fail now, instead of pulling 300 MiB before it fails
  # anyway. A route that answers with an error status opens cleanly, so the
  # per-shot status check below is what fails that one.
  if ! environment_blocker "$WORKDIR/pw-last.log" >/dev/null \
     && grep -qEi "executable doesn't exist|is not found at|playwright install|install-browser" \
          "$WORKDIR/pw-last.log"; then
    printf '%s: chromium build missing, installing it once, then retrying\n' "$SCRIPT_NAME" >&2
    "${RUNNER[@]}" install-browser chromium >&2 || cannot_capture "the chromium download failed"
    pw_quiet "${OPEN_ARGS[@]}" || open_failed
  else
    open_failed
  fi
fi
note_http_status "$WORKDIR/pw-last.log"

SHOT_NAMES=()
SHOT_FILES=()
SHOT_BYTES=()
SHOT_ERRORS=()
SHOT_STATUS=()
FAILED=0
TOTAL_ERRORS=0

# Emulation is set before the reload below, so the page paints under it. A
# failed emulation must fail the run: a "dark" shot that painted light would
# pass every size check and prove the opposite of what it claims.
if [ "$REDUCED_MOTION" = "1" ]; then
  pw_quiet set-reduced-motion reduce || die "cannot emulate prefers-reduced-motion"
fi

for scheme in "${SCHEMES[@]}"; do
  if [ -n "$scheme" ]; then
    pw_quiet set-color-scheme "$scheme" || die "cannot emulate prefers-color-scheme: $scheme"
  fi
  scheme_tag=""
  [ -n "$scheme" ] && scheme_tag="-$scheme"

  for vp in "${VIEWPORTS[@]}"; do
    w="${vp%%x*}"
    h="${vp##*x}"
    shot_name="${scheme:+$scheme }$vp"
    png="$OUT_ABS/$LABEL$scheme_tag$MOTION_TAG-${w}x${h}.png"
    rm -f "$png"

    status="ok"
    errors=0

    if pw_quiet resize "$w" "$h"; then
      pw_quiet console --clear >/dev/null 2>&1 || true
      # Reload at the target width so media queries and load-time layout scripts
      # run for this viewport instead of the one the page first opened at.
      if pw_quiet reload; then
        note_http_status "$WORKDIR/pw-last.log"
        errors="$(console_errors_from_log "$WORKDIR/pw-last.log")"
        shot_args=(screenshot "--filename=$png")
        [ "$FULL_PAGE" = "1" ] && shot_args+=(--full-page)
        pw_quiet "${shot_args[@]}" || status="screenshot-failed"
        # An error page paints a real PNG that passes every file check below,
        # so the status code is the only tell. The PNG stays, as a record of
        # what the server sent back.
        if [ "${HTTP_STATUS:-0}" -ge 400 ]; then
          status="http-$HTTP_STATUS"
        fi
      else
        status="reload-failed"
      fi
    else
      status="resize-failed"
    fi

    if [ "$WANT_CONSOLE" = "1" ]; then
      ctxt="${png%.png}.console.txt"
      if pw console >"$ctxt" 2>&1; then
        n="$(sed -n 's/.*Errors: \([0-9][0-9]*\).*/\1/p' "$ctxt" | head -n1)"
        [ -n "$n" ] && errors="$n"
      else
        printf '%s: could not read the console at %s\n' "$SCRIPT_NAME" "$vp" >&2
      fi
    fi

    if [ "$status" = "ok" ] && ! png_is_real "$png"; then
      status="blank-or-missing-png"
    fi

    bytes=0
    [ -f "$png" ] && bytes="$(png_bytes "$png")"

    if [ "$status" != "ok" ]; then
      FAILED=$((FAILED + 1))
      printf '%s: FAIL %s (%s)\n' "$SCRIPT_NAME" "$shot_name" "$status" >&2
    fi
    if [ "$errors" -gt 0 ]; then
      printf '%s: WARNING %s console errors at %s\n' "$SCRIPT_NAME" "$errors" "$shot_name" >&2
    fi
    TOTAL_ERRORS=$((TOTAL_ERRORS + errors))

    SHOT_NAMES+=("$shot_name")
    SHOT_FILES+=("$png")
    SHOT_BYTES+=("$bytes")
    SHOT_ERRORS+=("$errors")
    SHOT_STATUS+=("$status")
  done
done

cd "$START_CWD"
cleanup

printf '\n'
printf '%-16s %-48s %9s %8s %s\n' "SHOT" "FILE" "BYTES" "CON.ERR" "STATUS"
i=0
while [ "$i" -lt "${#SHOT_NAMES[@]}" ]; do
  printf '%-16s %-48s %9s %8s %s\n' \
    "${SHOT_NAMES[$i]}" "${SHOT_FILES[$i]##*/}" "${SHOT_BYTES[$i]}" "${SHOT_ERRORS[$i]}" \
    "${SHOT_STATUS[$i]}"
  i=$((i + 1))
done
printf 'files under %s\n\n' "$OUT_ABS"

CAPTURED=$(( ${#SHOT_NAMES[@]} - FAILED ))
printf '%s: %s/%s shots captured, %s console errors total\n' \
  "$SCRIPT_NAME" "$CAPTURED" "${#SHOT_NAMES[@]}" "$TOTAL_ERRORS"

if [ "$FAILED" -gt 0 ]; then
  printf '%s: FAILED, %s shot(s) failed, the STATUS column says why\n' "$SCRIPT_NAME" "$FAILED" >&2
  exit 1
fi

if [ "$WANT_CONSOLE" = "1" ] && [ "$TOTAL_ERRORS" -gt 0 ]; then
  printf '%s: read the .console.txt files before you call the page done\n' "$SCRIPT_NAME"
fi

printf '%s: OK\n' "$SCRIPT_NAME"
