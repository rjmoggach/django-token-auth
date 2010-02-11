from glob import glob
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup

for scheme in INSTALL_SCHEMES.values():
    scheme["data"] = scheme["purelib"]

data_files = [
    ["token_auth/templates/base_templates", glob("token_auth/templates/base_templates/*.html")]
]

VERSION = (0, 1, 0, 'alpha', 1)

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    else:
        if VERSION[3] != 'final':
            version = '%s %s %s' % (version, VERSION[3], VERSION[4])
    return version

setup(
    name='django-token_auth',
    version = get_version(),
    url = 'http://bitbucket.org/mogga/django-token_auth/',
    license = 'BSD',
    description = "app that provides limited authentication via hash-type URL.",
    author = 'Oyvind Saltvik',
    author_email = 'oyvind.saltvik@gmail.com',
    packages = ["token_auth"], 
    package_dir = {"token_auth": "token_auth"},
    data_files = data_files,
    install_requires = ["setuptools"],
    classifiers = [
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords = 'python django hash auth'
)

