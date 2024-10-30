python_sources(name="lib")

python_distribution(
    name="dist",
    dependencies=[":lib"],
    wheel=True,
    sdist=True,
    provides=python_artifact(
        name="nacc-form-validator",
        version="0.3.1",
        description="The NACC form validator package",
        author="NACC",
        author_email="nacchelp@uw.edu",
        url="https://github.com/naccdata/nacc-form-validator"),
)
