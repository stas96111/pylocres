import nox


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


def twine(session):
    session.run(
        "python", "-c", "import shutil; shutil.rmtree('dist', ignore_errors=True)"
    )
    session.install("twine")
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.run("twine", "upload", "dist/*")


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

    session.run("twine", "check", "dist/*")

    twine(session)
