import os
import sys
from os.path import abspath, dirname, join
from glob import glob
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup, find_packages


for scheme in INSTALL_SCHEMES.values():
    scheme["data"] = scheme["purelib"]


data_files = [
    ["src/token_auth/templates/base_templates", 
    glob("src/token_auth/templates/base_templates/*.html")]
]

root_dir = abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(root_dir, "src"))

version = __import__('token_auth').get_version()

def read(fname):
    return open(os.path.join(abspath(os.path.dirname(__file__)), fname)).read()

setup(
    name='django-token-auth',
    version = version,
    url = 'http://github.com/mogga/django-token-auth/',
    license = 'BSD',
    description = "app that provides limited authentication via hash-type URL.",
    long_description = '',

    author = 'Oyvind Saltvik, Robert Moggach',
    author_email = 'oyvind.saltvik@gmail.com, rob@moggach.com',

    packages = find_packages('src'),
    package_dir = {'': 'src'},
    data_files = data_files,

    install_requires = ['setuptools'],

    classifiers = [
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        'Topic :: Internet :: WWW/HTTP',
    ],

    keywords = 'python django hash authentication'

)
