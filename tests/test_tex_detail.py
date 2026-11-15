"""Compile and run the texture detail rule (gpu/vk/tex_detail.h; no game/GPU)."""
import argparse
import subprocess
import tempfile
from pathlib import Path

RUN_ALL_ARGS = ["--cxx", "g++"]

ROOT = Path(__file__).resolve().parents[1]


def check_source():
    """The texture setup still asks the rule, reads the switch and keeps the textures it must leave whole"""
    src = (ROOT / "gpu/vk/vk_texture.cpp").read_text(encoding="utf-8")
    for needle in ('#include "tex_detail.h"', "tex_detail::by_vram(", 'getenv("RX_VK_TEX_DETAIL")',
                   "tex_detail::skip(detail_level(), x.width, x.height, x.levels)",
                   "!as_target && astc && !x.sparse"):
        if needle not in src:
            raise SystemExit("vk_texture.cpp no longer has: " + needle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", default="g++")
    args = parser.parse_args()
    check_source()
    with tempfile.TemporaryDirectory(prefix="tex-detail-") as tmp:
        exe = Path(tmp) / "tex-detail"
        subprocess.run([args.cxx, "-std=c++20", "-Wall", "-Wextra", "-Werror",
                        str(ROOT / "tests/test_tex_detail.cpp"), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    main()
