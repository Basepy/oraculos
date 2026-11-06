#!/usr/bin/env python3
"""Validate oracles.json and the proof of key ownership of every oracle.

Usage:
    python scripts/verify.py oracles.json
    python scripts/verify.py oracles.json --base base.json --author github-user

With --base and --author (used for pull requests), every entry that was added
or changed compared to the base file must belong to the pull request author.

Only the Python standard library is used. Each entry carries a proof: a Nostr
event signed by the oracle key (BIP-340) that names the GitHub user and this
repository, so nobody can register a key they do not control.
"""

import argparse
import datetime
import hashlib
import json
import re
import sys

REPO = "Basepy/oraculos"
PROOF_KIND = 30078  # NIP-78: application-specific data
PROOF_D_TAG = "satslottu-oracle-registration"
REQUIRED_KEYS = {"npub", "github", "added", "proof"}
OPTIONAL_KEYS = {"name", "links"}
GITHUB_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
HEX = frozenset("0123456789abcdef")
MAX_NAME = 60
MAX_LINKS = 5

# secp256k1 domain parameters.
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (
    55066263022277343669578718895168534326250603453777594175500187360389116729240,
    32670510020758816978083085130507043184471273380659243275938904335757337482424,
)


# ---------------------------------------------------------------- BIP-340
def _add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    (x1, y1), (x2, y2) = a, b
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if a == b:
        slope = 3 * x1 * x1 * pow(2 * y1, P - 2, P) % P
    else:
        slope = (y2 - y1) * pow(x2 - x1, P - 2, P) % P
    x3 = (slope * slope - x1 - x2) % P
    return x3, (slope * (x1 - x3) - y1) % P


def point_mul(scalar, point=G):
    result, addend = None, point
    while scalar:
        if scalar & 1:
            result = _add(result, addend)
        addend = _add(addend, addend)
        scalar >>= 1
    return result


def _lift_x(x):
    if x >= P:
        return None
    y_squared = (pow(x, 3, P) + 7) % P
    y = pow(y_squared, (P + 1) // 4, P)
    if pow(y, 2, P) != y_squared:
        return None
    return x, y if y % 2 == 0 else P - y


def tagged_hash(tag, message):
    digest = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(digest + digest + message).digest()


def schnorr_verify(message, public_key, signature):
    """Verify a BIP-340 signature (32-byte message, x-only public key)."""
    if len(message) != 32 or len(public_key) != 32 or len(signature) != 64:
        return False
    point = _lift_x(int.from_bytes(public_key, "big"))
    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    if point is None or r >= P or s >= N:
        return False
    challenge = tagged_hash("BIP0340/challenge", signature[:32] + public_key + message)
    e = int.from_bytes(challenge, "big") % N
    result = _add(point_mul(s), point_mul(N - e, point))
    return result is not None and result[1] % 2 == 0 and result[0] == r


# ----------------------------------------------------------------- bech32
_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_GENERATOR = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)


def _polymod(values):
    check = 1
    for value in values:
        top = check >> 25
        check = (check & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            check ^= _GENERATOR[i] if (top >> i) & 1 else 0
    return check


def npub_to_hex(npub):
    """Return the 64-character hex public key of an npub1... string, or None."""
    if not isinstance(npub, str) or npub != npub.lower() or len(npub) > 90:
        return None
    position = npub.rfind("1")
    if position < 1 or position + 7 > len(npub) or npub[:position] != "npub":
        return None
    data = [_CHARSET.find(char) for char in npub[position + 1:]]
    if -1 in data:
        return None
    expanded = [ord(c) >> 5 for c in "npub"] + [0] + [ord(c) & 31 for c in "npub"]
    if _polymod(expanded + data) != 1:
        return None
    accumulator, bits, output = 0, 0, []
    for value in data[:-6]:
        accumulator = (accumulator << 5) | value
        bits += 5
        while bits >= 8:
            bits -= 8
            output.append((accumulator >> bits) & 0xFF)
    if bits >= 5 or (accumulator << (8 - bits)) & 0xFF or len(output) != 32:
        return None
    return bytes(output).hex()


def hex_to_npub(public_key_hex):
    """Encode a 64-character hex public key as an npub1... string."""
    accumulator, bits, data = 0, 0, []
    for byte in bytes.fromhex(public_key_hex):
        accumulator = (accumulator << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            data.append((accumulator >> bits) & 31)
    if bits:
        data.append((accumulator << (5 - bits)) & 31)
    expanded = [ord(c) >> 5 for c in "npub"] + [0] + [ord(c) & 31 for c in "npub"]
    polymod = _polymod(expanded + data + [0] * 6) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return "npub1" + "".join(_CHARSET[d] for d in data + checksum)


# ----------------------------------------------------------------- events
def _is_hex(value, length):
    return isinstance(value, str) and len(value) == length and set(value) <= HEX


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def event_id(event):
    serialized = json.dumps(
        [0, event["pubkey"], event["created_at"], event["kind"], event["tags"], event["content"]],
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(serialized.encode()).hexdigest()


def check_proof(entry, public_key_hex):
    """Return a list of problems with the registration proof of an entry."""
    proof = entry.get("proof")
    well_formed = (
        isinstance(proof, dict)
        and _is_hex(proof.get("id"), 64)
        and _is_hex(proof.get("pubkey"), 64)
        and _is_hex(proof.get("sig"), 128)
        and _is_int(proof.get("created_at"))
        and _is_int(proof.get("kind"))
        and isinstance(proof.get("content"), str)
        and isinstance(proof.get("tags"), list)
        and all(isinstance(t, list) and all(isinstance(i, str) for i in t) for t in proof["tags"])
    )
    if not well_formed:
        return ["proof is not a well-formed signed Nostr event"]
    problems = []
    if proof["kind"] != PROOF_KIND:
        problems.append(f"proof kind must be {PROOF_KIND}")
    for tag in (["d", PROOF_D_TAG], ["repo", REPO], ["github", entry.get("github")]):
        if tag not in proof["tags"]:
            problems.append(f"proof is missing the tag {tag}")
    if proof["pubkey"] != public_key_hex:
        problems.append("proof was signed by a different key than the npub")
    if event_id(proof) != proof["id"]:
        problems.append("proof id does not match its content")
    elif not schnorr_verify(
        bytes.fromhex(proof["id"]), bytes.fromhex(proof["pubkey"]), bytes.fromhex(proof["sig"])
    ):
        problems.append("proof signature is invalid")
    return problems


# ---------------------------------------------------------------- roster
def _check_entry(entry, index):
    where = f"oracles[{index}]"
    if not isinstance(entry, dict):
        return [f"{where}: must be an object"], None
    problems = []
    keys = set(entry)
    for key in sorted(REQUIRED_KEYS - keys):
        problems.append(f"{where}: missing '{key}'")
    for key in sorted(keys - REQUIRED_KEYS - OPTIONAL_KEYS):
        problems.append(f"{where}: unknown field '{key}'")
    public_key = npub_to_hex(entry.get("npub"))
    if "npub" in entry and public_key is None:
        problems.append(f"{where}: npub is not a valid npub1... key")
    github = entry.get("github")
    if "github" in entry and not (isinstance(github, str) and GITHUB_RE.match(github)):
        problems.append(f"{where}: github is not a valid user name")
    added = entry.get("added")
    if "added" in entry:
        try:
            datetime.date.fromisoformat(added)
            if not (isinstance(added, str) and len(added) == 10):
                raise ValueError
        except (TypeError, ValueError):
            problems.append(f"{where}: added must be a date like 2026-11-06")
    name = entry.get("name")
    if "name" in entry and not (isinstance(name, str) and 0 < len(name) <= MAX_NAME):
        problems.append(f"{where}: name must have 1 to {MAX_NAME} characters")
    links = entry.get("links")
    if "links" in entry and not (
        isinstance(links, list)
        and len(links) <= MAX_LINKS
        and all(isinstance(link, str) and link.startswith("https://") and len(link) <= 200 for link in links)
    ):
        problems.append(f"{where}: links must be at most {MAX_LINKS} https URLs")
    if not problems:
        problems += [f"{where}: {p}" for p in check_proof(entry, public_key)]
    return problems, public_key


def validate(roster, base=None, author=None):
    """Return a list of problems with the roster (empty when it is valid)."""
    if not (isinstance(roster, dict) and roster.get("version") == 1 and isinstance(roster.get("oracles"), list)):
        return ['the file must be {"version": 1, "oracles": [...]}']
    problems, seen_keys, seen_users = [], set(), set()
    for index, entry in enumerate(roster["oracles"]):
        entry_problems, public_key = _check_entry(entry, index)
        problems += entry_problems
        if public_key:
            if public_key in seen_keys:
                problems.append(f"oracles[{index}]: this npub is listed twice")
            seen_keys.add(public_key)
        user = str(entry.get("github", "")).lower() if isinstance(entry, dict) else ""
        if user:
            if user in seen_users:
                problems.append(f"oracles[{index}]: github user '{entry['github']}' is listed twice")
            seen_users.add(user)
    if base is not None and author:
        old = {e.get("npub"): e for e in base.get("oracles", []) if isinstance(e, dict)}
        for index, entry in enumerate(roster["oracles"]):
            if isinstance(entry, dict) and old.get(entry.get("npub")) != entry:
                if str(entry.get("github", "")).lower() != author.lower():
                    problems.append(
                        f"oracles[{index}]: added or changed by '{author}' but belongs to '{entry.get('github')}'"
                    )
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roster")
    parser.add_argument("--base", help="roster of the base branch (pull requests)")
    parser.add_argument("--author", help="GitHub user that opened the pull request")
    args = parser.parse_args(argv)
    try:
        with open(args.roster, encoding="utf-8") as handle:
            roster = json.load(handle)
        base = None
        if args.base:
            with open(args.base, encoding="utf-8") as handle:
                base = json.load(handle)
    except (OSError, ValueError) as error:
        print(f"ERROR: could not read the files: {error}")
        return 1
    problems = validate(roster, base, args.author)
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        return 1
    print(f"OK: {len(roster['oracles'])} oracle(s) verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
