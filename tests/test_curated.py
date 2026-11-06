"""Entradas curadas (só a npub, sem prova nem GitHub) e o script add_npub.py."""
import contextlib
import datetime
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

from test_verify import (ROOT, SECRET_A, SECRET_B, make_entry, npub_from_hex, roster, verify,
                         x_only)

NPUB_A = npub_from_hex(x_only(SECRET_A).hex())
NPUB_B = npub_from_hex(x_only(SECRET_B).hex())


def curated(npub=NPUB_A, **fields):
    entry = {"npub": npub, "added": "2026-11-06"}
    entry.update(fields)
    return entry


def with_maintainers(data, *names):
    return dict(data, maintainers=list(names))


class CuratedEntryTest(unittest.TestCase):
    def test_a_bare_npub_is_a_valid_entry(self):
        self.assertEqual(verify.validate(roster(curated())), [])
        self.assertEqual(verify.validate(roster(curated(name="Base", links=["https://example.com"]))), [])

    def test_curated_and_self_registered_entries_can_live_together(self):
        self.assertEqual(verify.validate(roster(curated(), make_entry(SECRET_B, "bob"))), [])

    def test_github_and_proof_go_together(self):
        only_github = curated(github="alice")
        only_proof = {k: v for k, v in make_entry().items() if k != "github"}
        for name, entry in {"only github": only_github, "only proof": only_proof}.items():
            with self.subTest(case=name):
                self.assertTrue(verify.validate(roster(entry)), name)

    def test_a_curated_entry_still_needs_a_valid_npub_and_date(self):
        self.assertTrue(verify.validate(roster(curated(npub="npub1abc"))))
        self.assertTrue(verify.validate(roster(curated(added="ontem"))))
        self.assertTrue(verify.validate(roster(curated(), curated())))

    def test_maintainers_field_is_validated(self):
        self.assertEqual(verify.validate(with_maintainers(roster(), "Basepy")), [])
        for bad in ("Basepy", ["-bad"], [5]):
            with self.subTest(value=bad):
                self.assertTrue(verify.validate(dict(roster(), maintainers=bad)))


class CuratedPullRequestTest(unittest.TestCase):
    def setUp(self):
        self.base = with_maintainers(roster(), "Basepy")

    def test_a_maintainer_can_add_curated_entries(self):
        new = with_maintainers(roster(curated(), curated(NPUB_B)), "Basepy")
        self.assertEqual(verify.validate(new, self.base, "Basepy"), [])
        self.assertEqual(verify.validate(new, self.base, "basepy"), [])

    def test_a_stranger_cannot_add_a_curated_entry(self):
        new = with_maintainers(roster(curated()), "Basepy")
        problems = verify.validate(new, self.base, "mallory")
        self.assertTrue(any("only a maintainer" in p for p in problems))

    def test_a_stranger_cannot_make_themselves_maintainer(self):
        new = with_maintainers(roster(curated()), "Basepy", "mallory")
        problems = verify.validate(new, self.base, "mallory")
        self.assertTrue(any("maintainers list" in p for p in problems))
        # a lista que vale é a da base, não a da própria pull request
        self.assertTrue(any("only a maintainer" in p for p in problems))

    def test_first_pull_request_may_create_the_maintainers_field(self):
        legacy_base = roster()  # a main antiga, sem o campo
        new = with_maintainers(roster(), "Basepy")
        self.assertEqual(verify.validate(new, legacy_base, "Basepy"), [])
        # mas, mesmo assim, não dá para entrar sem prova numa base que ainda não tem mantenedores
        with_entry = with_maintainers(roster(curated()), "Basepy")
        self.assertTrue(verify.validate(with_entry, legacy_base, "Basepy"))

    def test_a_stranger_cannot_edit_a_curated_entry(self):
        base = with_maintainers(roster(curated()), "Basepy")
        changed = with_maintainers(roster(curated(name="Renamed")), "Basepy")
        self.assertTrue(verify.validate(changed, base, "mallory"))
        self.assertEqual(verify.validate(changed, base, "Basepy"), [])

    def test_a_stranger_can_still_register_with_a_proof(self):
        new = with_maintainers(roster(make_entry(SECRET_B, "bob")), "Basepy")
        self.assertEqual(verify.validate(new, self.base, "bob"), [])
        self.assertTrue(verify.validate(new, self.base, "mallory"))

    def test_a_maintainer_can_add_a_proof_entry_for_someone_else(self):
        new = with_maintainers(roster(make_entry(SECRET_B, "bob")), "Basepy")
        self.assertEqual(verify.validate(new, self.base, "Basepy"), [])

    def test_unchanged_entries_are_not_checked(self):
        base = with_maintainers(roster(curated()), "Basepy")
        self.assertEqual(verify.validate(base, base, "carol"), [])


class AddNpubTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("add_npub", ROOT / "scripts" / "add_npub.py")
        self.add = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.add)
        self.today = datetime.date(2026, 11, 6)

    def test_adds_a_valid_npub_with_the_date(self):
        data = with_maintainers(roster(), "Basepy")
        self.assertEqual(self.add.add_npubs(data, [NPUB_A], name="Base", today=self.today), [])
        self.assertEqual(data["oracles"], [{"npub": NPUB_A, "added": "2026-11-06", "name": "Base"}])
        self.assertEqual(data["maintainers"], ["Basepy"])

    def test_accepts_hex_and_converts_to_npub(self):
        data = roster()
        self.assertEqual(self.add.add_npubs(data, [x_only(SECRET_B).hex().upper()], today=self.today), [])
        self.assertEqual(data["oracles"][0]["npub"], NPUB_B)

    def test_rejects_invalid_and_repeated_npubs_and_changes_nothing(self):
        data = roster(curated())
        broken = NPUB_B[:-1] + ("q" if NPUB_B[-1] != "q" else "p")
        for value in ([NPUB_A], ["npub1abc"], [broken], [NPUB_B, NPUB_B], [NPUB_B, "lixo"]):
            with self.subTest(value=value):
                self.assertTrue(self.add.add_npubs(data, value))
                self.assertEqual(len(data["oracles"]), 1)

    def test_name_needs_a_single_npub(self):
        self.assertTrue(self.add.add_npubs(roster(), [NPUB_A, NPUB_B], name="X"))

    def test_command_line_writes_a_file_that_verifies(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "oracles.json"
            path.write_text(json.dumps(with_maintainers(roster(), "Basepy")), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.add.main([NPUB_A, "--name", "Base", "--file", str(path)]), 0)
                self.assertEqual(self.add.main([NPUB_B, "--file", str(path)]), 0)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(self.add.main([NPUB_B, "--file", str(path)]), 1)
                self.assertEqual(self.add.main([NPUB_A, "--file", str(Path(folder) / "nao-existe.json")]), 1)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual([e["npub"] for e in saved["oracles"]], [NPUB_A, NPUB_B])
            self.assertEqual(verify.validate(saved), [])
            self.assertTrue(path.read_text(encoding="utf-8").endswith("}\n"))


if __name__ == "__main__":
    unittest.main()
