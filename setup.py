from setuptools import setup, find_packages

setup(
    name='validator',
    version='0.2',
    url='https://github.com/naccdata/nacc-form-validator',
    author='NACC',
    author_email='nacchelp@uw.edu',
    packages=find_packages(),
    install_requires=['cerberus', 'python-dateutil'],
)
