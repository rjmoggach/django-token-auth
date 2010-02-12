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

SRC_DIR = abspath(join(dirname(__file__), "src/"))
sys.path.insert(0, SRC_DIR)

ROOT_DIR = abspath(dirname(__file__))
# root_dir = os.path.dirname(__file__)
if ROOT_DIR != '':
    os.chdir(join(ROOT_DIR,''))


version = __import__('token_auth').get_version()

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-token_auth',
    version = version,
    url = 'http://bitbucket.org/mogga/django-token_auth/',
    license = 'BSD',
    description = "app that provides limited authentication via hash-type URL.",
    long_description = read('README'),

    author = 'Oyvind Saltvik, Robert Moggach',
    author_email = 'oyvind.saltvik@gmail.com',

    packages = find_packages('src'),
    package_dir = {'': 'src'},
    data_files = data_files,

    install_requires = ['setuptools'],

    classifiers = [
        'Development Status :: 4 - Beta'
        'Programming Language :: Python',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        'Topic :: Internet :: WWW/HTTP',
    ],

    keywords = 'python django hash authentication'

)
