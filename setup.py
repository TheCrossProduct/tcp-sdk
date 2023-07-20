from setuptools import setup, find_packages

setup (
    name = "tcpSDK",
    version = "0.0.1",
    install_requires = [
        "slumber",
        "requests",
        "requests_oauthlib",
    ],
    packages = find_packages(),
    include_package_data = True,
)
