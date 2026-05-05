import os
from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read_project_file(filename):
    with open(os.path.join(here, filename), encoding="utf-8") as f:
        return f.read()


version = {}
with open(os.path.join(here, 'customerio', '__version__.py'), encoding="utf-8") as f:
    exec(f.read(), version)

long_description = "\n\n".join([
    read_project_file("README.md"),
    read_project_file("CHANGELOG.md"),
])

setup(
    name="customerio",
    version=version['__version__'],
    author="Peaberry Software Inc.",
    author_email="support@customerio.com",
    license="BSD",
    description="Customer.io Python bindings.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/customerio/customerio-python",
    packages=find_packages(),
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires=['requests>=2.20.0'],
    test_suite="tests",
)
