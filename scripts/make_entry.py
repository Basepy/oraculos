#!/usr/bin/env python3
"""Turn a signed registration event into the entry to add to oracles.json.

Usage:
    python scripts/make_entry.py proof.json --name "Your Name"
    cat proof.json | python scripts/make_entry.py - --link https://example.com/you

The event is the one signed by your Nostr key (see CONTRIBUTING.md). It names
your GitHub user, so nothing else has to be typed. The script checks the
signature before printing, so a mistake shows up here and not in the pull
request. It never asks for or reads a private key.
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify  # noqa: E402


def build_entry(proof, name=None, links=None, today=None):
    """Return (entry, problems) for a signed registration event."""
    github = next((tag[1] for tag in proof.get("tags", []) if tag[:1] == ["github"] and len(tag) > 1), None)
    entry = {
        "npub": verify.hex_to_npub(proof["pubkey"]),
        "github": github,
        "added": (today or datetime.date.today()).isoformat(),
        "proof": proof,
    }
    if name:
        entry["name"] = name
    if links:
        entry["links"] = list(links)
    problems, _ = verify._check_entry(entry, 0)
    return entry, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("event", help="file with the signed event as JSON, or - for standard input")
    parser.add_argument("--name", help="name shown in the list (optional)")
    parser.add_argument("--link", action="append", help="https link about you (optional, repeatable)")
    args = parser.parse_args(argv)
    try:
        source = sys.stdin if args.event == "-" else open(args.event, encoding="utf-8")
        with source:
            proof = json.load(source)
        if not isinstance(proof, dict) or not isinstance(proof.get("pubkey"), str):
            raise ValueError("not a signed Nostr event")
    except (OSError, ValueError) as error:
        print(f"ERROR: could not read the event: {error}", file=sys.stderr)
        return 1
    entry, problems = build_entry(proof, args.name, args.link)
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(json.dumps(entry, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
