from setuptools import setup, find_packages
from os import path
import re
import io

module_name = "tcp"
package_name = "tcp-sdk"

deps = [
    'slumber',
    'requests',
    'requests_oauthlib'
    ]

extra_deps = {
    'tests': [
        'coverage'
        'mock',
        'pylint'
        ],
    'develop': [
        'setuptools',
        'wheel'
        ]
    }

def read_file (*relative_path_elements):
    file_path = path.join (path.dirname(__file__), *relative_path_elements)
    return io.open(file_path, encoding='utf8').read().strip()

_version = None
def version ():
    global _version
    if _version:
        return _version
    init_file = read_file(module_name, '__init__.py')
    matches = re.search (r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', init_file, re.M)
    if not matches:
        raise RuntimeError ("Unable to find version string in __init__.py .")
    _version = matches.group(1)
    return _version

setup (
    name = package_name,

    version = version(),
    description = "Python SDK to query The Cross Product API.",
#    long_description_content_type = "text/x-rst",
#    long_description = read_file('README.rst'),
    long_description_content_type="text/x-rst",
    long_description=io.open(path.join(path.dirname(__file__), "README.rst"), "r").read(),

    install_requires = deps,
    tests_require = deps + extra_deps["tests"],
    extra_require = extra_deps,

    dependency_links = [],

    packages = find_packages(),
)
