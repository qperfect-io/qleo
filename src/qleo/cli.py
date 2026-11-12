# Copyright (c) 2025-2026 QPerfect. All Rights Reserved.
# Proprietary and confidential.

"""Command-line entry point for the ``qleo`` console script.

Installed as ``qleo`` via ``[project.scripts]``. Exposes:

- ``docs`` — open the documentation bundled inside the wheel in a browser.
- ``cudaq install`` / ``uninstall`` / ``status`` — enable Qleo as a CUDA-Q
  target by copying the bundled NVQIR backend into the CUDA-Q installation.
  See :mod:`qleo.cudaq`.
"""

import argparse
import sys
import webbrowser

from qleo import __version__, docs_dir

ONLINE_DOCS = "https://docs.qperfect.io/qleo/"


def _cmd_docs(args: argparse.Namespace) -> int:
    """Open the bundled documentation in a web browser."""
    index = docs_dir() / "index.html"
    if not index.is_file():
        print(
            "Bundled documentation was not found.\n"
            f"Expected it at: {index}\n"
            "This usually means the package was built without the docs "
            f"site. The online docs are at {ONLINE_DOCS}",
            file=sys.stderr,
        )
        return 1

    if args.print_path:
        print(index)
        return 0

    uri = index.as_uri()
    print(f"Opening {uri}")
    if not webbrowser.open(uri):
        print(
            f"Could not launch a web browser. Open the file manually:\n  {index}",
            file=sys.stderr,
        )
        return 1
    return 0


def _cmd_cudaq(args: argparse.Namespace) -> int:
    """Install, remove or report the CUDA-Q backend."""
    # Imported here rather than at module scope so `qleo docs` keeps working
    # in an environment with no CUDA-Q, and in the pure-Python wheel that
    # carries no backend at all.
    from qleo.cudaq import (
        InstallError,
        cudaq_install_dir,
        install,
        status,
        uninstall,
    )

    try:
        target = cudaq_install_dir()
        if args.cudaq_command == "install":
            for path in install(target):
                print(f"installed {path}")
            print('Ready: cudaq.set_target("qleo")')
        elif args.cudaq_command == "uninstall":
            removed = uninstall(target)
            for path in removed:
                print(f"removed {path}")
            if not removed:
                print(f"nothing to remove in {target}")
        else:
            print(f"CUDA-Q installation: {target}")
            for name, present in status(target).items():
                print(f"  {'present' if present else 'missing'}  {name}")
    except InstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the requested subcommand."""
    argv = sys.argv[1:] if argv is None else list(argv)

    parser = argparse.ArgumentParser(
        prog="qleo", description="Qleo command-line utilities."
    )
    parser.add_argument("--version", action="version", version=f"qleo {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    docs = sub.add_parser("docs", help="Open the bundled documentation.")
    docs.add_argument(
        "--print-path",
        action="store_true",
        help="Print the path to the bundled docs instead of opening a browser.",
    )
    docs.set_defaults(func=_cmd_docs)

    cudaq = sub.add_parser(
        "cudaq",
        help="Enable Qleo as a CUDA-Q target.",
        description=(
            "CUDA-Q discovers simulators inside its own installation and "
            "offers no plugin search path, so the backend has to be copied "
            "there. Run `install` once per environment."
        ),
    )
    cudaq_sub = cudaq.add_subparsers(dest="cudaq_command", required=True)
    for name, help_text in (
        ("install", "Copy the backend into the CUDA-Q installation."),
        ("uninstall", "Remove it again."),
        ("status", "Report whether it is installed."),
    ):
        cudaq_sub.add_parser(name, help=help_text)
    cudaq.set_defaults(func=_cmd_cudaq)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
