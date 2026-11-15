"""AMD's FSR 4 libraries for the players' build (scripts/fsr_sdk.py, nx2/make_game.py --fsr).

Without the network: a stand-in for AMD's repository hands out this test's own files, and the script's table is pointed
at them.
- both files are fetched into the folder; a second fetch downloads nothing; a damaged one alone is fetched again;
- a file of another size or SHA-256 stops the fetch and is not left in the folder;
- the game folder gets the two libraries and AMD's license text beside the exe, and loses exactly those again;
- make_game.py fetches with --fsr, places them at the end, and Setup asks for --fsr.

python -I -B tests/test_fsr_sdk.py
"""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fsr_sdk", ROOT / "scripts" / "fsr_sdk.py")
fsr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fsr)


def content(name):
    return (("AMD's %s\n" % name) * 300).encode()


class FsrSdkTest(unittest.TestCase):
    def setUp(self):
        self.saved = fsr.RUNTIME
        fsr.RUNTIME = [(name, len(content(name)), hashlib.sha256(content(name)).hexdigest()) for name, _, _ in self.saved]
        self.tmp = tempfile.TemporaryDirectory(prefix="fsr-sdk-")
        self.dir = Path(self.tmp.name)
        self.asked = []
        self.said = []

    def tearDown(self):
        fsr.RUNTIME = self.saved
        self.tmp.cleanup()

    def get(self, url):
        self.asked.append(url)
        return content(url.rsplit("/", 1)[1])

    def test_fetch(self):
        folder = self.dir / "sdk"
        fsr.fetch(str(folder), say=self.said.append, get=self.get)
        self.assertTrue(fsr.complete(str(folder)))
        self.assertEqual(len(self.asked), 2)
        self.assertTrue(all(url.startswith(fsr.BASE) for url in self.asked))
        fsr.fetch(str(folder), say=self.said.append, get=self.get)
        self.assertEqual(len(self.asked), 2)   # (nothing asked for again)
        self.assertIn("already", self.said[-1])
        (folder / "amd_fidelityfx_loader_vk.dll").write_bytes(b"damaged")
        self.assertEqual(fsr.missing(str(folder)), ["amd_fidelityfx_loader_vk.dll"])
        fsr.fetch(str(folder), say=self.said.append, get=self.get)
        self.assertEqual(len(self.asked), 3)
        self.assertTrue(fsr.complete(str(folder)))

    def test_another_file_refused(self):
        folder = self.dir / "sdk"
        with self.assertRaises(ValueError):
            fsr.fetch(str(folder), say=self.said.append, get=lambda url: content(url) + b"x")
        self.assertEqual(sorted(p.name for p in folder.iterdir()), [])
        self.assertFalse(fsr.complete(str(folder)))

    def test_game_folder(self):
        folder, game = self.dir / "sdk", self.dir / "game"
        fsr.fetch(str(folder), say=self.said.append, get=self.get)
        game.mkdir()
        (game / "Triforce.exe").write_bytes(b"the game")
        placed = fsr.install_runtime(str(folder), str(game))
        self.assertEqual(sorted(Path(p).name for p in placed), ["amd_fidelityfx_loader_vk.dll", "amd_fidelityfx_upscaler_vk.dll"])
        self.assertTrue((game / fsr.LICENSE_NAME).is_file())
        self.assertIn("Advanced Micro Devices", (game / fsr.LICENSE_NAME).read_text(encoding="utf-8", errors="replace"))
        self.assertTrue(fsr.remove_runtime(str(game)))
        self.assertEqual([p.name for p in game.iterdir()], ["Triforce.exe"])
        self.assertFalse(fsr.remove_runtime(str(game)))

    def test_real_table(self):
        self.assertEqual([name for name, _, _ in self.saved], ["amd_fidelityfx_loader_vk.dll", "amd_fidelityfx_upscaler_vk.dll"])
        for name, size, digest in self.saved:
            self.assertGreater(size, 30000, name)
            self.assertRegex(digest, r"^[0-9a-f]{64}$", name)
        self.assertTrue(Path(fsr.LICENSE_SOURCE).is_file())

    def test_wired(self):
        src = (ROOT / "nx2" / "make_game.py").read_text(encoding="utf-8")
        for needle in ("fetch_fsr_runtime(work)", 'place_fsr_runtime(out, work, os.environ.get("HOOKSHOT_FSR") == "1")',
                       "fsr.remove_runtime(out)"):
            self.assertIn(needle, src)
        shell = (ROOT / "setup" / "Shell.cs").read_text(encoding="utf-8")
        self.assertIn('args.Add("--fsr")', shell)


if __name__ == "__main__":
    raise SystemExit(unittest.main(verbosity=1))
