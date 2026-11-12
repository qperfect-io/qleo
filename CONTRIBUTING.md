# Contributing

Thanks for your interest in contributing!

This repository contains the **public Python interface** for the package qleo. 
The underlying simulation engine (Rust) is proprietary and not open for external contributions.

## What you can contribute

You are welcome to contribute to:

- Python API improvements
- Bug fixes in the Python wrapper
- Documentation improvements
- Examples and tutorials
- Test coverage for the Python interface
- Build, packaging, and CI improvements

## What is out of scope

The following are **not** open for contribution:

- The simulation engine implementation
- Backend build system or internal APIs
- Requests for access to private repositories

Issues or pull requests touching these areas will be closed.

## Changelog

Every user-visible change goes in [CHANGELOG.md](CHANGELOG.md) — including
the ones that come from bumping the `mimiq-exaqt` engine. A version bump of
the engine is a user-visible change to Qleo: name the new engine version and
summarise what it brings under an `### Engine` heading.

## Releasing

Cutting a release is a maintainer task and needs the private CI; the steps,
the CI behaviour and the one-time project settings are in
[RELEASING.md](RELEASING.md).

## Reporting issues

Please use GitHub Issues to report:

- Installation problems
- Runtime errors
- Incorrect behavior of the Python API
- Documentation issues

When reporting bugs, include:
- Python version
- Operating system
- Full error messages or tracebacks
- Minimal reproduction code if possible

## Pull requests

Pull requests should:
- Target the `main` branch
- Include tests where applicable
- Follow existing code style
- Keep changes focused and minimal


## Licensing

By contributing, you agree that your contributions will be licensed under
the same license as this repository.

---

If you have questions or are unsure whether a contribution fits,
feel free to open an issue for discussion first.