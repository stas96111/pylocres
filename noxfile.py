import nox

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def get_version():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


@nox.session(venv_backend="venv")
def tests(session):
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.install("pytest")
    session.run("pytest", "tests")
    print("Good!")


@nox.session(venv_backend="none")
def install(session):
    session.install("-e", ".")


@nox.session(venv_backend="venv")
def twine(session):
    session.run(
        "python", "-c", "import shutil; shutil.rmtree('dist', ignore_errors=True)"
    )
    session.install("twine")
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.run("twine", "upload", "dist/*")


@nox.session(venv_backend="venv")
def release(session):
    session.install("twine")
    session.install("pytest")
    session.install("-r", "requirements.txt")
    session.install("-e", ".")

    session.run("pytest", "tests")
    session.run(
        "python", "-c", "import shutil; shutil.rmtree('dist', ignore_errors=True)"
    )
    session.run("python", "-m", "build")
    session.run("twine", "upload", "dist/*")

    session.run("git", "tag", f"v{get_version()}")
    session.run("git", "push", "--tags")

    twine(session)
