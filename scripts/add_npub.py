#!/usr/bin/env python3
"""Add trusted npubs to oracles.json (for maintainers).

Usage:
    python scripts/add_npub.py npub1... --name "Name"
    python scripts/add_npub.py npub1... npub1...

No proof and no GitHub account are needed: the list is curated by the
maintainers, and the pull request that adds the npubs must come from one of them
(see "maintainers" in oracles.json). The file is checked before it is saved.
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify  # noqa: E402

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "oracles.json")


def add_npubs(roster, npubs, name=None, links=None, today=None):
    """Return the problems found; on success the entries were appended to roster."""
    if len(npubs) > 1 and name:
        return ["--name only works with a single npub"]
    problems, entries = [], []
    known = {verify.npub_to_hex(e.get("npub")) for e in roster["oracles"] if isinstance(e, dict)}
    for value in npubs:
        public_key = verify.npub_to_hex(value)
        if public_key is None and len(value) == 64 and all(c in verify.HEX for c in value.lower()):
            public_key = value.lower()
        if public_key is None:
            problems.append(f"{value[:20]}...: not a valid npub1... key or 64 hex characters")
        elif public_key in known:
            problems.append(f"{verify.hex_to_npub(public_key)}: already in the list")
        else:
            known.add(public_key)
            entry = {"npub": verify.hex_to_npub(public_key), "added": (today or datetime.date.today()).isoformat()}
            if name:
                entry["name"] = name
            if links:
                entry["links"] = list(links)
            entries.append(entry)
    if problems:
        return problems
    problems = verify.validate(dict(roster, oracles=roster["oracles"] + entries))
    if not problems:
        roster["oracles"].extend(entries)
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("npub", nargs="+", help="npub1... (or 64 hex characters)")
    parser.add_argument("--name", help="name shown in the list (single npub only)")
    parser.add_argument("--link", action="append", help="https link about the person (repeatable)")
    parser.add_argument("--file", default=DEFAULT_FILE, help="roster file (default: oracles.json)")
    args = parser.parse_args(argv)
    try:
        with open(args.file, encoding="utf-8") as handle:
            roster = json.load(handle)
    except (OSError, ValueError) as error:
        print(f"ERROR: could not read the roster: {error}", file=sys.stderr)
        return 1
    problems = verify.validate(roster)
    if not problems:
        problems = add_npubs(roster, args.npub, args.name, args.link)
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    if problems:
        return 1
    with open(args.file, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"OK: {len(args.npub)} npub(s) added; now {len(roster['oracles'])} in the list")
    return 0


if __name__ == "__main__":
    sys.exit(main())
