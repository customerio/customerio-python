from setuptools import find_packages, setup

from customerio import get_version


setup(
    name="customerio",
    version=get_version(),
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
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=['requests>=2.5'],
    test_suite="tests",
)
