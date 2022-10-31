"""Automation using nox."""
import glob
import os
from pathlib import Path

import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = "lint", "tests"


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "pypy3.8", "pypy3.9"])
def tests(session: nox.Session) -> None:
    session.install(".[dev]")

    env = {
        "COVERAGE_FILE": f".coverage.{session.python}",
        "COVERAGE_PROCESS_START": os.fspath(Path.cwd() / "pyproject.toml"),
    }
    # pytest loads plugin before the test is run, so we have to start coverage
    # before pytest loads.
    session.run("coverage", "run", "-m", "pytest", *session.posargs, env=env)
    session.run("coverage", "combine", env=env)
    session.run("coverage", "report", env=env)
    if os.getenv("COVERAGE_XML"):
        session.run("coverage", "xml", "-o", "coverage.xml", env=env)


@nox.session
def lint(session: nox.Session) -> None:
    session.install("pre-commit")
    session.install("-e", ".[dev]")

    args = *(session.posargs or ("--show-diff-on-failure",)), "--all-files"
    session.run("pre-commit", "run", *args)
    session.run("python", "-m", "mypy")
    session.run("python", "-m", "pylint", "src")


@nox.session
def safety(session: nox.Session) -> None:
    """Scan dependencies for insecure packages."""
    session.install(".[dev]")
    session.install("safety")
    session.run("safety", "check", "--full-report")


@nox.session
def build(session: nox.Session) -> None:
    session.install("build", "setuptools", "twine")
    session.run("python", "-m", "build")
    dists = glob.glob("dist/*")
    session.run("twine", "check", *dists, silent=True)


@nox.session
def dev(session: nox.Session) -> None:
    """Sets up a python development environment for the project."""
    args = session.posargs or ("venv",)
    venv_dir = os.fsdecode(os.path.abspath(args[0]))

    session.log(f"Setting up virtual environment in {venv_dir}")
    session.install("virtualenv")
    session.run("virtualenv", venv_dir, silent=True)

    python = os.path.join(venv_dir, "bin/python")
    session.run(
        python, "-m", "pip", "install", "-e", ".[all,dev]", external=True
    )
