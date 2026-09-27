#!/usr/bin/env python3
"""Fixture harness for slop_lint.

Every rule in the registry needs at least one bad fixture that triggers it and one
good fixture that does not, so the registry cannot grow a rule that nothing tests.
More cases for a rule go in bad_<rule>--<variant>.<ext> and
good_<rule>--<variant>.<ext>. A good fixture is also held to a stricter bar: it
must produce no finding at error severity from any rule.

A fixture can pin exact numbers with a comment such as
'fixture-expect pure-black-white count=1 severity=advisory'. A count of 0 says a
rule other than the fixture's own must stay quiet. A comment such as
'fixture-expect-text em-dash "plain hyphen"' requires one finding of that rule
to carry the quoted text in its message or its fix.

After the fixtures, the command-line checks run the linter in a subprocess: the
exit code under --max-findings, the report of skipped files, and time and memory
ceilings on inputs that once took seconds and gigabytes.
"""

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
LINTER = os.path.join(SKILL, "scripts", "slop_lint.py")
FIXTURES = os.path.join(HERE, "fixtures")
KINDS = ("bad", "good")
NAME_RE = re.compile(
    r"^(bad|good)_([a-z0-9]+(?:-[a-z0-9]+)*)(?:--([a-z0-9]+(?:-[a-z0-9]+)*))?$"
)
EXPECT_RE = re.compile(r"fixture-expect\s+([a-z0-9-]+)((?:\s+[a-z]+=[a-z0-9]+)+)")
EXPECT_TEXT_RE = re.compile(r'fixture-expect-text\s+([a-z0-9-]+)\s+"([^"]+)"')
NAME_WIDTH = 50
PERF_WALL_S = 3.0
PERF_RSS_KB = 300 * 1024
CLI_TIMEOUT_S = 60
# A regression back to exponential growth must fail here, not exhaust the host.
CHILD_ADDRESS_SPACE = 1024 * 1024 * 1024
EM_DASH = chr(0x2014)


def load_linter():
    spec = importlib.util.spec_from_file_location("slop_lint", LINTER)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load " + LINTER)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations through sys.modules, so register first.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_name(name):
    stem, ext = os.path.splitext(name)
    m = NAME_RE.match(stem)
    if not m:
        return None
    return m.group(1), m.group(2), ext.lower()


def check_registry(lint, failures):
    rule_ids = [rule.rule_id for rule in lint.RULES]
    no_check = sorted(set(rule_ids) - set(lint.CHECKS))
    no_rule = sorted(set(lint.CHECKS) - set(rule_ids))
    if no_check:
        failures.append("registry rules with no check: " + ", ".join(no_check))
    if no_rule:
        failures.append("checks with no registry entry: " + ", ".join(no_rule))
    return rule_ids


def read_expectations(path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    out = []
    for m in EXPECT_RE.finditer(text):
        fields = dict(pair.split("=", 1) for pair in m.group(2).split())
        out.append((m.group(1), fields))
    for m in EXPECT_TEXT_RE.finditer(text):
        out.append((m.group(1), {"text": m.group(2)}))
    return out


def check_expectations(lint, path, findings):
    problems = []
    for rule_id, fields in read_expectations(path):
        if rule_id not in lint.RULES_BY_ID:
            problems.append("fixture-expect names unknown rule " + rule_id)
            continue
        got = [f for f in findings if f.rule == rule_id]
        if "count" in fields and len(got) != int(fields["count"]):
            problems.append("expected %s %s finding(s), got %d"
                            % (fields["count"], rule_id, len(got)))
        want = fields.get("severity")
        if want:
            other = sorted({f.severity for f in got if f.severity != want})
            if other or not got:
                problems.append("expected %s at %s, got %s"
                                % (rule_id, want, ", ".join(other) or "nothing"))
        text = fields.get("text")
        if text and not any(text in f.message or text in f.fix for f in got):
            problems.append("no %s finding says %r" % (rule_id, text))
    return problems


def grade(lint, path, kind, rule_id, rule_ids):
    findings = lint.lint_file(path, rule_ids)
    if findings is None:
        return [], ["the scanner skipped this fixture"]
    hit = sorted({f.rule for f in findings})
    errors = sorted({f.rule for f in findings if f.severity == "error"})
    problems = []
    if kind == "bad" and rule_id not in hit:
        problems.append("expected " + rule_id + ", got " + (", ".join(hit) or "nothing"))
    if kind == "good":
        if rule_id in hit:
            problems.append(rule_id + " fired on a clean fixture")
        if errors:
            problems.append("error severity on a clean fixture: " + ", ".join(errors))
    problems.extend(check_expectations(lint, path, findings))
    return hit, problems


def run_fixtures(lint, rule_ids, failures, report):
    seen = {}
    passes = 0
    for name in sorted(os.listdir(FIXTURES)):
        path = os.path.join(FIXTURES, name)
        if not os.path.isfile(path):
            continue
        parsed = parse_name(name)
        if parsed is None:
            failures.append(name + ": name must be bad_<rule>[--<variant>].<ext> "
                            "or good_<rule>[--<variant>].<ext>")
            continue
        kind, rule_id, ext = parsed
        if rule_id not in lint.RULES_BY_ID:
            failures.append(name + ": unknown rule id " + rule_id)
            continue
        seen.setdefault(rule_id, set()).add(kind)
        if ext not in lint.RULES_BY_ID[rule_id].exts:
            failures.append(name + ": extension " + ext + " is out of scope for " + rule_id)
            continue
        hit, problems = grade(lint, path, kind, rule_id, rule_ids)
        if problems:
            failures.append(name + ": " + "; ".join(problems))
            report.append("FAIL  " + name.ljust(NAME_WIDTH) + "; ".join(problems))
            continue
        passes += 1
        state = "triggered" if kind == "bad" else "clean"
        report.append("PASS  " + name.ljust(NAME_WIDTH) + rule_id + " " + state
                      + "  [" + (", ".join(hit) or "no findings") + "]")
    for rule_id in rule_ids:
        for kind in KINDS:
            if kind not in seen.get(rule_id, set()):
                failures.append("rule " + rule_id + " has no " + kind + " fixture")
    return passes


def children_peak_kb():
    """Peak RSS of the largest finished child so far, in KB, or None off Unix."""
    try:
        import resource
    except ImportError:
        return None
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return peak // 1024 if sys.platform == "darwin" else peak


def cap_child_memory():
    try:
        import resource
    except ImportError:
        return None

    def limit():
        # Some kernels, macOS among them, refuse an address-space limit; the
        # time and RSS ceilings still apply there.
        try:
            resource.setrlimit(resource.RLIMIT_AS, (CHILD_ADDRESS_SPACE, CHILD_ADDRESS_SPACE))
        except (ValueError, OSError):
            pass

    return limit


def run_linter(args):
    start = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, LINTER] + args,
            capture_output=True, text=True, timeout=CLI_TIMEOUT_S,
            preexec_fn=cap_child_memory(),
        )
    except subprocess.TimeoutExpired:
        return None, CLI_TIMEOUT_S
    return proc, time.monotonic() - start


def write(folder, name, text):
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def as_json(proc):
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return None


def cli_checks(tmp):
    """(label, problems) for command-line behaviour a fixture file cannot hold."""
    results = []

    advisory = write(tmp, "advisory.html", '<a class="text-white" href="/">Home</a>\n')
    error = write(tmp, "error.html", "<p>One " + EM_DASH + " two</p>\n")
    proc, _ = run_linter(["--json", "--max-findings", "1", advisory, error])
    problems = []
    data = as_json(proc) if proc else None
    if proc is None or data is None:
        problems.append("no JSON output")
    else:
        if proc.returncode != 2:
            problems.append("exit %d, want 2" % proc.returncode)
        summary = data["summary"]
        hidden = summary.get("error") != 1 or not summary.get("truncated")
        if hidden or len(data["findings"]) != 1:
            problems.append("summary %r" % summary)
    results.append(("--max-findings prints 1 and still exits 2 on a hidden error",
                    problems))

    bundle = write(tmp, "bundle.min.js", "window.a=1;\n")
    proc, _ = run_linter([bundle])
    problems = []
    if proc is None or proc.returncode != 1 or "minified" not in proc.stderr:
        problems.append("exit %s, stderr %r" % (proc and proc.returncode, proc and proc.stderr))
    results.append(("a named minified file exits 1", problems))

    tree = os.path.join(tmp, "tree")
    os.makedirs(tree)
    packed = write(tree, "vendor.js", ("x" * 800 + "\n") * 5)
    write(tree, "page.html", "<p>Plain copy.</p>\n")
    proc, _ = run_linter([tree])
    problems = []
    if proc is None or proc.returncode != 0:
        problems.append("exit %s, want 0" % (proc and proc.returncode))
    elif "skipped (minified): " + packed not in proc.stdout:
        problems.append("the skipped file is not named: %r" % proc.stdout)
    proc, _ = run_linter(["--json", tree])
    data = as_json(proc) if proc else None
    want = [{"file": packed, "reason": "minified"}]
    if data is None or data["summary"].get("skipped_files") != want:
        problems.append("skipped_files %r" % (data and data["summary"].get("skipped_files")))
    results.append(("a walked directory names its skipped files", problems))

    proc, _ = run_linter(["--list-rules", "--json"])
    data = as_json(proc) if proc else None
    problems = []
    listed = [rule["rule"] for rule in data["rules"]] if data else []
    if "undersized-ui-text" not in listed:
        problems.append("undersized-ui-text missing from --list-rules --json")
    results.append(("--list-rules --json lists undersized-ui-text", problems))
    return results


def perf_inputs():
    """(name, source, expected em-dash count or None) for the ceiling checks.

    Each input keeps short lines, so the median rule does not skip it and the
    scanner really reads it.
    """
    rows = "".join("<tr><td>Row %d</td><td>%d units</td></tr>\n" % (n, n)
                   for n in range(300))
    nested_html = ('<div class="wrap">' * 60 + "\n<table>\n" + rows + "</table>\n"
                   + "</div>" * 60 + "\n")
    nested_tsx = ("export function Deep() {\n  return (\n"
                  + '<div className="wrap">\n' * 60 + "<p>Deep text</p>\n"
                  + "</div>\n" * 60 + "  );\n}\n")
    stray = ("<a " * 100 + "\n") * 200
    data_uri = "data:image/png;base64," + "QUJD" * 75000
    long_line = ("<p>First " + EM_DASH + " second</p>\n"
                 + '<img alt="Collage" src="' + data_uri + '">\n'
                 + "<p>Third " + EM_DASH + " fourth</p>\n")
    return [
        ("nested-wrappers.html", nested_html, None),
        ("nested-wrappers.tsx", nested_tsx, None),
        ("stray-open-tags.html", stray, None),
        ("data-uri-line.html", long_line, 2),
    ]


def perf_checks(tmp):
    results = []
    for name, source, dashes in perf_inputs():
        path = write(tmp, name, source)
        proc, wall = run_linter(["--json", path])
        peak = children_peak_kb()
        problems = []
        data = as_json(proc) if proc else None
        if proc is None:
            problems.append("timed out after %ds" % CLI_TIMEOUT_S)
        elif data is None:
            problems.append("no JSON output, exit %d" % proc.returncode)
        elif data["summary"].get("files_scanned") != 1:
            problems.append("not scanned: %r" % data["summary"].get("skipped_files"))
        if wall >= PERF_WALL_S:
            problems.append("wall %.2fs, ceiling %.1fs" % (wall, PERF_WALL_S))
        if peak is not None and peak >= PERF_RSS_KB:
            problems.append("peak RSS %d MB, ceiling %d MB" % (peak // 1024, PERF_RSS_KB // 1024))
        if data is not None and dashes is not None:
            got = sum(1 for f in data["findings"] if f["rule"] == "em-dash")
            if got != dashes:
                problems.append("em-dash %d, want %d" % (got, dashes))
        size = "%d KB" % (len(source.encode("utf-8")) // 1024)
        rss = "?" if peak is None else "%d MB" % (peak // 1024)
        results.append(("%s (%s) %.2fs, peak RSS so far %s" % (name, size, wall, rss),
                        problems))
    return results


def main():
    if not os.path.isdir(FIXTURES):
        sys.stderr.write("run_fixtures: no fixtures directory at " + FIXTURES + "\n")
        return 1
    lint = load_linter()
    failures = []
    report = []
    rule_ids = check_registry(lint, failures)
    passes = run_fixtures(lint, rule_ids, failures, report)
    for line in report:
        print(line)
    print("")
    print("fixtures %d, pass %d, fail %d, rules %d"
          % (len(report), passes, len(report) - passes, len(rule_ids)))

    print("")
    with tempfile.TemporaryDirectory() as tmp:
        cases = [("cli", cli_checks(tmp)), ("perf", perf_checks(tmp))]
    for group, results in cases:
        for label, problems in results:
            state = "FAIL" if problems else "PASS"
            print("%s  %s: %s" % (state, group, label))
            for problem in problems:
                failures.append(group + ": " + label + ": " + problem)

    if failures:
        print("")
        print("failures:")
        for item in failures:
            print("  " + item)
        return 1
    print("")
    print("every rule has a bad and a good fixture, and the command-line checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
