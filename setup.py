from setuptools import setup, find_packages

setup(
    name='validator',
    version='0.1',

    url='https://github.com/naccdata/nacc-form-validator',
    author='Chandima HewaNadungodage',
    author_email='chandhn@uw.edu',

    packages=find_packages(),

    install_requires=[
        'cerberus',
        'pyyaml',
    ],
)
