#! coding: utf-8
from setuptools import find_packages
from setuptools import setup


setup(
    name = 'manozodynas',
    version = '0.1',
    url = 'http://manoŽodynas.lt',
    license = 'MIT',
    description = 'Evolving Lithuanian language dictionary used to create and '
                  'verify Lithuanian language terms',
    maintainer = 'Hack4LT',
    maintainer_email = 'info@hack4.lt',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[]
)
