from setuptools import setup, find_packages

module_name = "tcp"
package_name = "tcp-sdk"

setup (
    name = ,
    version = "0.0.1",
    install_requires = [
        "slumber",
        "requests",
        "requests_oauthlib",
    ],
    packages = find_packages(),
    include_package_data = True,
)
