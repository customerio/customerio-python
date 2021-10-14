import os
from setuptools import find_packages, setup

version = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'customerio', '__version__.py')) as f:
        exec(f.read(), version)

setup(
    name="customerio",
    version=version['__version__'],
    author="Peaberry Software Inc.",
    author_email="support@customerio.com",
    license="BSD",
    description="Customer.io Python bindings.",
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
