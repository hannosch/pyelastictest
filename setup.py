import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()

tests_require = [
    'coverage',
    'nose',
    'Sphinx',
]

__version__ = '0.2'

setup(
    name='pyelastictest',
    version=__version__,
    description='Integration test harness for ElasticSearch',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    keywords='elasticsearch test',
    author="Hanno Schlichting",
    author_email="hanno@hannosch.eu",
    url="https://pyelastictest.readthedocs.org",
    license="Apache 2.0",
    packages=find_packages(),
    test_suite="pyelastictest.tests",
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'pyelasticsearch',
    ],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
    },
)
