import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verify", ROOT / "scripts" / "verify.py")
verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify)

# Official BIP-340 vectors (bitcoin/bips, bip-0340/test-vectors.csv) with a
# 32-byte message, like a Nostr event id: (index, public key, message, signature, valid).
BIP340_VECTORS = [
    (0, "F9308A019258C31049344F85F89D5229B531C845836F99B08601F113BCE036F9",
     "0000000000000000000000000000000000000000000000000000000000000000",
     "E907831F80848D1069A5371B402410364BDF1C5F8307B0084C55F1CE2DCA8215"
     "25F66A4A85EA8B71E482A74F382D2CE5EBEEE8FDB2172F477DF4900D310536C0",
     True),
    (1, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "6896BD60EEAE296DB48A229FF71DFE071BDE413E6D43F917DC8DCF8C78DE3341"
     "8906D11AC976ABCCB20B091292BFF4EA897EFCB639EA871CFA95F6DE339E4B0A",
     True),
    (2, "DD308AFEC5777E13121FA72B9CC1B7CC0139715309B086C960E18FD969774EB8",
     "7E2D58D8B3BCDF1ABADEC7829054F90DDA9805AAB56C77333024B9D0A508B75C",
     "5831AAEED7B44BB74E5EAB94BA9D4294C49BCF2A60728D8B4C200F50DD313C1B"
     "AB745879A5AD954A72C45A91C3A51D3C7ADEA98D82F8481E0E1E03674A6F3FB7",
     True),
    (3, "25D1DFF95105F5253C4022F628A996AD3A0D95FBF21D468A1B33F8C160D8F517",
     "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
     "7EB0509757E246F19449885651611CB965ECC1A187DD51B64FDA1EDC9637D5EC"
     "97582B9CB13DB3933705B32BA982AF5AF25FD78881EBB32771FC5922EFC66EA3",
     True),
    (4, "D69C3509BB99E412E68B0FE8544E72837DFA30746D8BE2AA65975F29D22DC7B9",
     "4DF3C3F68FCC83B27E9D42C90431A72499F17875C81A599B566C9889B9696703",
     "00000000000000000000003B78CE563F89A0ED9414F5AA28AD0D96D6795F9C63"
     "76AFB1548AF603B3EB45C9F8207DEE1060CB71C04E80F593060B07D28308D7F4",
     True),
    (5, "EEFDEA4CDB677750A420FEE807EACF21EB9898AE79B9768766E4FAA04A2D4A34",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "6CFF5C3BA86C69EA4B7376F31A9BCB4F74C1976089B2D9963DA2E5543E177769"
     "69E89B4C5564D00349106B8497785DD7D1D713A8AE82B32FA79D5F7FC407D39B",
     False),
    (6, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "FFF97BD5755EEEA420453A14355235D382F6472F8568A18B2F057A1460297556"
     "3CC27944640AC607CD107AE10923D9EF7A73C643E166BE5EBEAFA34B1AC553E2",
     False),
    (7, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "1FA62E331EDBC21C394792D2AB1100A7B432B013DF3F6FF4F99FCB33E0E1515F"
     "28890B3EDB6E7189B630448B515CE4F8622A954CFE545735AAEA5134FCCDB2BD",
     False),
    (8, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "6CFF5C3BA86C69EA4B7376F31A9BCB4F74C1976089B2D9963DA2E5543E177769"
     "961764B3AA9B2FFCB6EF947B6887A226E8D7C93E00C5ED0C1834FF0D0C2E6DA6",
     False),
    (9, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "0000000000000000000000000000000000000000000000000000000000000000"
     "123DDA8328AF9C23A94C1FEECFD123BA4FB73476F0D594DCB65C6425BD186051",
     False),
    (10, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "0000000000000000000000000000000000000000000000000000000000000001"
     "7615FBAF5AE28864013C099742DEADB4DBA87F11AC6754F93780D5A1837CF197",
     False),
    (11, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "4A298DACAE57395A15D0795DDBFD1DCB564DA82B0F269BC70A74F8220429BA1D"
     "69E89B4C5564D00349106B8497785DD7D1D713A8AE82B32FA79D5F7FC407D39B",
     False),
    (12, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F"
     "69E89B4C5564D00349106B8497785DD7D1D713A8AE82B32FA79D5F7FC407D39B",
     False),
    (13, "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "6CFF5C3BA86C69EA4B7376F31A9BCB4F74C1976089B2D9963DA2E5543E177769"
     "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141",
     False),
    (14, "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC30",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "6CFF5C3BA86C69EA4B7376F31A9BCB4F74C1976089B2D9963DA2E5543E177769"
     "69E89B4C5564D00349106B8497785DD7D1D713A8AE82B32FA79D5F7FC407D39B",
     False),
]

SECRET_A = 0xB7E151628AED2A6ABF7158809CF4F3C762E7160F38B4DA56A784D9045190CFEF
SECRET_B = 0x0B432B2677937381AEF05BB02A66ECD012773062CF3FA2549E44F58ED2401710

_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _polymod(values):
    generator = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    check = 1
    for value in values:
        top = check >> 25
        check = (check & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            check ^= generator[i] if (top >> i) & 1 else 0
    return check


def npub_from_hex(public_key_hex, hrp="npub"):
    """Encode a 32-byte key as bech32 (test helper)."""
    accumulator, bits, data = 0, 0, []
    for byte in bytes.fromhex(public_key_hex):
        accumulator = (accumulator << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            data.append((accumulator >> bits) & 31)
    if bits:
        data.append((accumulator << (5 - bits)) & 31)
    expanded = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    polymod = _polymod(expanded + data + [0] * 6) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(_CHARSET[d] for d in data + checksum)


def x_only(secret):
    return verify.point_mul(secret)[0].to_bytes(32, "big")


def sign(secret, message):
    """BIP-340 signing with a deterministic nonce (tests only)."""
    point = verify.point_mul(secret)
    d = secret if point[1] % 2 == 0 else verify.N - secret
    public_key = point[0].to_bytes(32, "big")
    k = int.from_bytes(
        verify.tagged_hash("BIP0340/nonce", d.to_bytes(32, "big") + public_key + message), "big"
    ) % verify.N
    r_point = verify.point_mul(k)
    if r_point[1] % 2:
        k = verify.N - k
    r = r_point[0].to_bytes(32, "big")
    e = int.from_bytes(verify.tagged_hash("BIP0340/challenge", r + public_key + message), "big")
    return r + ((k + e * d) % verify.N).to_bytes(32, "big")


def make_proof(secret, github="alice", **overrides):
    event = {
        "pubkey": x_only(secret).hex(),
        "created_at": 1_767_268_800,
        "kind": verify.PROOF_KIND,
        "tags": [["d", verify.PROOF_D_TAG], ["repo", verify.REPO], ["github", github]],
        "content": "I want to be a Sats Lottu oracle",
    }
    event.update(overrides)
    event["id"] = verify.event_id(event)
    event["sig"] = sign(secret, bytes.fromhex(event["id"])).hex()
    return event


def make_entry(secret=SECRET_A, github="alice", **fields):
    entry = {
        "npub": npub_from_hex(x_only(secret).hex()),
        "github": github,
        "added": "2026-11-06",
        "proof": make_proof(secret, github),
    }
    entry.update(fields)
    return entry


def roster(*entries):
    return {"version": 1, "oracles": list(entries)}


class Bip340Test(unittest.TestCase):
    def test_official_vectors(self):
        for index, public_key, message, signature, expected in BIP340_VECTORS:
            with self.subTest(vector=index):
                result = verify.schnorr_verify(
                    bytes.fromhex(message), bytes.fromhex(public_key), bytes.fromhex(signature)
                )
                self.assertIs(result, expected)

    def test_test_signer_matches_the_verifier(self):
        message = hashlib.sha256(b"oracle").digest()
        signature = sign(SECRET_A, message)
        self.assertTrue(verify.schnorr_verify(message, x_only(SECRET_A), signature))
        self.assertFalse(verify.schnorr_verify(bytes(32), x_only(SECRET_A), signature))

    def test_wrong_lengths_are_rejected(self):
        signature = sign(SECRET_A, bytes(32))
        self.assertFalse(verify.schnorr_verify(bytes(31), x_only(SECRET_A), signature))
        self.assertFalse(verify.schnorr_verify(bytes(32), bytes(31), signature))
        self.assertFalse(verify.schnorr_verify(bytes(32), x_only(SECRET_A), signature[:63]))


class NpubTest(unittest.TestCase):
    def test_round_trip(self):
        public_key = x_only(SECRET_A).hex()
        self.assertEqual(verify.npub_to_hex(npub_from_hex(public_key)), public_key)

    def test_rejects_bad_checksum_case_prefix_and_garbage(self):
        good = npub_from_hex(x_only(SECRET_A).hex())
        broken = good[:-1] + ("q" if good[-1] != "q" else "p")
        for value in (broken, good.upper(), npub_from_hex(x_only(SECRET_A).hex(), "nsec"), "npub1", "", None, 5):
            with self.subTest(value=value):
                self.assertIsNone(verify.npub_to_hex(value))


class RosterTest(unittest.TestCase):
    def test_empty_and_valid_rosters(self):
        self.assertEqual(verify.validate(roster()), [])
        entry = make_entry(name="Alice", links=["https://example.com/alice"])
        self.assertEqual(verify.validate(roster(entry, make_entry(SECRET_B, "bob"))), [])

    def test_file_shape(self):
        for value in ([], {"version": 2, "oracles": []}, {"version": 1}, {"version": 1, "oracles": {}}):
            with self.subTest(value=value):
                self.assertTrue(verify.validate(value))

    def test_fields(self):
        cases = {
            "unknown field": make_entry(extra="x"),
            "missing github": {k: v for k, v in make_entry().items() if k != "github"},
            "bad npub": make_entry(npub="npub1abc"),
            "bad github": make_entry(github="-alice"),
            "bad date": make_entry(added="06/11/2026"),
            "date without zeros": make_entry(added="2026-1-6"),
            "long name": make_entry(name="x" * 61),
            "empty name": make_entry(name=""),
            "http link": make_entry(links=["http://example.com"]),
            "too many links": make_entry(links=["https://example.com"] * 6),
            "not an object": "alice",
        }
        for name, entry in cases.items():
            with self.subTest(case=name):
                self.assertTrue(verify.validate(roster(entry)), name)

    def test_duplicates(self):
        self.assertTrue(verify.validate(roster(make_entry(), make_entry())))
        same_user = make_entry(SECRET_B, "ALICE")
        same_user["proof"] = make_proof(SECRET_B, "ALICE")
        self.assertTrue(verify.validate(roster(make_entry(), same_user)))

    def test_proof_problems(self):
        entry = make_entry()
        other = make_entry(SECRET_B)
        tampered = dict(entry["proof"], content="changed")
        bad_sig = dict(entry["proof"], sig="0" * 128)
        cases = {
            "signed by another key": dict(entry, proof=other["proof"]),
            "other github user": dict(entry, github="mallory"),
            "other repo": dict(entry, proof=make_proof(SECRET_A, tags=[
                ["d", verify.PROOF_D_TAG], ["repo", "someone/else"], ["github", "alice"]])),
            "missing d tag": dict(entry, proof=make_proof(SECRET_A, tags=[
                ["repo", verify.REPO], ["github", "alice"]])),
            "wrong kind": dict(entry, proof=make_proof(SECRET_A, kind=1)),
            "tampered content": dict(entry, proof=tampered),
            "invalid signature": dict(entry, proof=bad_sig),
            "malformed proof": dict(entry, proof={"id": "x"}),
            "no proof": {k: v for k, v in entry.items() if k != "proof"},
        }
        for name, bad in cases.items():
            with self.subTest(case=name):
                self.assertTrue(verify.validate(roster(bad)), name)


class PullRequestTest(unittest.TestCase):
    def test_author_can_add_own_entry(self):
        base = roster(make_entry())
        new = roster(make_entry(), make_entry(SECRET_B, "bob"))
        self.assertEqual(verify.validate(new, base, "bob"), [])

    def test_author_cannot_add_someone_elses_entry(self):
        base = roster()
        new = roster(make_entry(SECRET_B, "bob"))
        problems = verify.validate(new, base, "mallory")
        self.assertTrue(any("belongs to" in p for p in problems))

    def test_unchanged_entries_are_not_checked_against_the_author(self):
        base = roster(make_entry(), make_entry(SECRET_B, "bob"))
        self.assertEqual(verify.validate(base, base, "carol"), [])

    def test_author_cannot_change_someone_elses_entry(self):
        base = roster(make_entry())
        changed = roster(make_entry(name="Renamed"))
        self.assertTrue(verify.validate(changed, base, "mallory"))
        self.assertEqual(verify.validate(changed, base, "alice"), [])

    def test_case_of_the_author_does_not_matter(self):
        self.assertEqual(verify.validate(roster(make_entry(SECRET_B, "bob")), roster(), "BOB"), [])

    def test_removal_is_left_to_the_maintainers(self):
        self.assertEqual(verify.validate(roster(), roster(make_entry()), "mallory"), [])


class CommandLineTest(unittest.TestCase):
    def _run(self, data, *extra):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "oracles.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return verify.main([str(path), *extra])

    def test_exit_codes(self):
        self.assertEqual(self._run(roster(make_entry())), 0)
        self.assertEqual(self._run(roster(make_entry(github="-bad"))), 1)

    def test_missing_file_fails(self):
        self.assertEqual(verify.main(["does-not-exist.json"]), 1)

    def test_committed_roster_is_valid(self):
        self.assertEqual(verify.main([str(ROOT / "oracles.json")]), 0)


class MakeEntryTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("make_entry", ROOT / "scripts" / "make_entry.py")
        self.make_entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.make_entry)

    def test_encoder_matches_the_independent_test_helper(self):
        for secret in (SECRET_A, SECRET_B):
            public_key = x_only(secret).hex()
            self.assertEqual(verify.hex_to_npub(public_key), npub_from_hex(public_key))

    def test_builds_a_valid_entry_from_a_signed_event(self):
        entry, problems = self.make_entry.build_entry(
            make_proof(SECRET_A, "alice"), name="Alice", links=["https://example.com"]
        )
        self.assertEqual(problems, [])
        self.assertEqual(entry["github"], "alice")
        self.assertEqual(entry["npub"], npub_from_hex(x_only(SECRET_A).hex()))
        self.assertEqual(verify.validate(roster(entry)), [])

    def test_reports_a_bad_signature(self):
        proof = dict(make_proof(SECRET_A, "alice"), sig="0" * 128)
        _, problems = self.make_entry.build_entry(proof)
        self.assertTrue(problems)

    def test_command_line_prints_the_entry(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "proof.json"
            path.write_text(json.dumps(make_proof(SECRET_A, "alice")), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = self.make_entry.main([str(path), "--name", "Alice"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out.getvalue())["name"], "Alice")
            self.assertEqual(self.make_entry.main([str(Path(folder) / "missing.json")]), 1)


if __name__ == "__main__":
    unittest.main()
