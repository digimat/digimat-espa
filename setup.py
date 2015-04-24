from setuptools import setup, find_packages

setup(
    name='digimat.espa',
    version='0.1.6',
    description='Digimat Espa 4.4.4',
    namespace_packages=['digimat'],
    author='Frederic Hess',
    author_email='fhess@splust.ch',
    license='PSF',
    packages=find_packages('src'),
    package_dir = {'':'src'},
    install_requires=[
        'pyserial',
        'setuptools'
    ],
    dependency_links=[
        ''
    ],
    zip_safe=False)
