from setuptools import setup, find_packages

setup (
    name = "tcp-api-testing",
    version = "0.0.1",
    install_requires = [
        "slumber",
        "requests",
    ],
    packages = find_packages(),
    include_package_data = True,
    scripts = ["test.sh"],
)
