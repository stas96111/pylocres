import nox

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def get_version():
    with open("pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["version"]


@nox.session(venv_backend="venv")
def tests(session):
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.install("pytest")
    session.run("pytest", "tests")
    session.log("Tests passed.")


@nox.session(venv_backend="venv", requires=["tests"])
def release(session):
    session.run(
        "python",
        "-c",
        "import shutil; shutil.rmtree('dist', ignore_errors=True)",
    )

    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.install("build", "twine")

    session.run("python", "-m", "build")

    session.run("twine", "upload", "dist/*")

    version = get_version()
    session.run("git", "tag", f"v{version}", external=True)
    session.run("git", "push", external=True)
    session.run("git", "push", "--tags", external=True)

    session.log(f"Released v{version}")
