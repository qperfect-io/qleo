#!/usr/bin/env python3
# Copyright (c) 2025-2026 QPerfect. All Rights Reserved.
# Proprietary and confidential.

"""Validate a CUDA-Q backend payload and derive the wheel's platform tag.

Usage:
    python scripts/inspect_payload.py DIR [--policy-tag manylinux_2_28_x86_64]
                                          [--write-tag DIR/PLAT_TAG]

`DIR` holds the six files a cudaq-integration build produces: CPU
(`libnvqir-qleo.so`, `libexaqt.so`, `qleo.yml`) and GPU
(`libnvqir-qleo_gpu.so`, `libexaqt_gpu.so`, `qleo_gpu.yml`).

Two jobs it does, both of which used to be inline shell in `.gitlab-ci.yml`:

**Validation.** The libraries must be real ELF x86-64 objects and each YAML
must actually declare its NVQIR backend. Without this a failed download
ships a 200-byte JSON error as a shared library — the API returns those
with a 200 status when the token lacks access.

**Tag derivation.** A `manylinux_2_NN` tag is a *minimum*: it promises the
wheel needs glibc `2.NN` or newer. Claiming a lower floor than the truth is
the dangerous direction, because pip then installs the wheel somewhere the
library cannot load. So the floor is measured from all four binaries in the
payload rather than declared, and never goes below `--policy-tag` (the
oldest base we mean to support, which nobody has tested below).

Reported **per file**, deliberately. The four libraries are different
languages with different dependencies: `libexaqt.so`/`libexaqt_gpu.so` are
Rust and link no libstdc++ at all, so their floor is pure glibc, while
`libnvqir-qleo.so`/`libnvqir-qleo_gpu.so` are the C++ objects. A single
merged maximum reads as though one artifact demanded both, which is
actively misleading — it is what once made a libstdc++ problem look like a
glibc one.

Note that GLIBCXX/CXXABI are reported but cannot enter the tag: no wheel
tag encodes the C++ runtime. They still have to be satisfied by the target
host's libstdc++, so they are printed for a human to weigh.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

LIBS = ("libnvqir-qleo.so", "libexaqt.so", "libnvqir-qleo_gpu.so", "libexaqt_gpu.so")
# Each target config must declare its own `nvqir-simulation-backend`, in
# cudaq-integration's qleo.yml / qleo_gpu.yml respectively.
TARGET_CONFIG_MARKERS = {
    "qleo.yml": "nvqir-simulation-backend: qleo",
    "qleo_gpu.yml": "nvqir-simulation-backend: qleo_gpu",
}
SYMBOL_PREFIXES = ("GLIBC", "GLIBCXX", "CXXABI")


def die(msg: str) -> None:
    sys.exit(f"error: {msg}")


def version_key(version: str) -> tuple[int, ...]:
    """`3.4.9` sorts below `3.4.29` — numerically, not lexically."""
    return tuple(int(p) for p in version.split(".") if p.isdigit())


def max_symbol_version(path: Path, prefix: str) -> str | None:
    """Highest `<prefix>_x.y.z` version the object requires, or None."""
    out = subprocess.run(
        ["objdump", "-T", str(path)], capture_output=True, text=True, check=True
    ).stdout
    # `GLIBC_` must not match `GLIBCXX_`, hence the explicit underscore.
    found = re.findall(rf"\b{prefix}_(\d[\d.]*)", out)
    if not found:
        return None
    return max(found, key=version_key)


def check_files(payload: Path) -> None:
    missing = [
        n for n in (*LIBS, *TARGET_CONFIG_MARKERS) if not (payload / n).is_file()
    ]
    if missing:
        die(f"{payload}/ is missing {', '.join(missing)}")

    for name in LIBS:
        path = payload / name
        with path.open("rb") as fh:
            head = fh.read(20)
        # ELF magic, 64-bit, little-endian, e_machine == EM_X86_64 (0x3e).
        if head[:4] != b"\x7fELF":
            die(f"{name} is not an ELF object (starts {head[:8]!r}) — a failed download?")
        if head[4] != 2 or head[5] != 1:
            die(f"{name} is not 64-bit little-endian ELF")
        if int.from_bytes(head[18:20], "little") != 0x3E:
            die(f"{name} is not x86-64")
        print(f"    {name}: ELF 64-bit x86-64, {path.stat().st_size} bytes")

    for name, marker in TARGET_CONFIG_MARKERS.items():
        cfg = (payload / name).read_text()
        if marker not in cfg:
            die(f"{name} does not declare {marker!r}")
        print(f"    {name}: declares its NVQIR backend")


def report_abi(payload: Path) -> dict[str, dict[str, str | None]]:
    table: dict[str, dict[str, str | None]] = {}
    for name in LIBS:
        table[name] = {}
        print(f"    --- {name}")
        for prefix in SYMBOL_PREFIXES:
            value = max_symbol_version(payload / name, prefix)
            table[name][prefix] = value
            print(f"        max {prefix}: {value or 'none'}")
    return table


def derive_tag(table: dict[str, dict[str, str | None]], policy_tag: str) -> str:
    m = re.fullmatch(r"manylinux_2_(\d+)_(\w+)", policy_tag)
    if not m:
        die(f"--policy-tag {policy_tag!r} is not a manylinux_2_NN_<arch> tag")
    policy_minor, arch = int(m.group(1)), m.group(2)

    # The wheel's floor is the highest glibc any file in it demands.
    minors = []
    for name, syms in table.items():
        glibc = syms["GLIBC"]
        if glibc:
            parts = version_key(glibc)
            if len(parts) >= 2 and parts[0] == 2:
                minors.append(parts[1])
    measured = max(minors) if minors else policy_minor

    if measured < policy_minor:
        print(
            f"    measured glibc floor 2.{measured} is below the policy floor "
            f"2.{policy_minor}; keeping the policy floor, which is the oldest "
            "base anyone has tested"
        )
        measured = policy_minor
    elif measured > policy_minor:
        print(
            f"    NOTE: glibc 2.{measured} is above the intended floor "
            f"2.{policy_minor}. The tag below is honest, so older distros will "
            "install the pure py3-none-any wheel and simply have no CUDA-Q "
            "backend."
        )

    tag = f"manylinux_2_{measured}_{arch}"

    worst_cxx = max(
        (s["GLIBCXX"] for s in table.values() if s["GLIBCXX"]),
        key=version_key,
        default=None,
    )
    if worst_cxx:
        print(
            f"    reminder: manylinux tags encode glibc only. The payload also "
            f"needs GLIBCXX_{worst_cxx}, which the target host's libstdc++ must "
            "provide and no wheel tag can express."
        )
    return tag


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="inspect_payload.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("payload", type=Path)
    parser.add_argument("--policy-tag", default="manylinux_2_28_x86_64")
    parser.add_argument(
        "--write-tag", type=Path, default=None,
        help="File to write the derived tag to (default: <payload>/PLAT_TAG).",
    )
    args = parser.parse_args()

    if shutil.which("objdump") is None:
        die("objdump not found (install binutils)")
    if not args.payload.is_dir():
        die(f"{args.payload} is not a directory")

    print(f"[1/3] validating {args.payload}/")
    check_files(args.payload)
    print("[2/3] measuring the runtime floor, per file")
    table = report_abi(args.payload)
    print("[3/3] deriving the wheel platform tag")
    tag = derive_tag(table, args.policy_tag)

    out = args.write_tag or (args.payload / "PLAT_TAG")
    out.write_text(tag + "\n")
    print(f"    derived platform tag: {tag}  (written to {out})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
