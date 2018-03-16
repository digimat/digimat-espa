from setuptools import setup, find_packages

from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='digimat.espa',
    version='0.1.11',
    description='Digimat ESPA 4.4.4',
    long_description=long_description,
    namespace_packages=['digimat'],
    author='Frederic Hess',
    author_email='fhess@st-sa.ch',
    url='https://github.com/digimat/digimat-espa',
    license='PSF',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'pyserial',
        'setuptools'
    ],
    dependency_links=[
        ''
    ],
    zip_safe=False)
