import os
import sys
import re
from setuptools import setup, find_packages, Command

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except:
    README = CHANGES = ''

v = open(os.path.join(os.path.dirname(__file__), 'pyramid_crud', '__init__.py'))
VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)
v.close()

requires = [
    'pyramid',  # framework
    'Mako',  # templating
    'pyramid_mako',  # templating
    'SQLAlchemy>=0.8',  # database
    'wtforms',  # forms
    'wtforms_alchemy',  # forms
    'ordereddict>=1.1'  # ordereddict for Python < 2.7
    if sys.version_info[0] == 2 and sys.version_info[1] < 7 else '',
]


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)

setup(name='pyramid_crud',
      version=VERSION,
      description='CRUD interface for the Pyramid Framework',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Intended Audience :: Developers",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.3",
          "Framework :: Pylons",
          "License :: OSI Approved :: MIT License",
      ],
      keywords='web wsgi pylons pyramid crud admin',
      author='Florian Ruechel',
      author_email='pyramid_crud@googlegroups.com',
      url='https://github.com/Javex/pyramid_crud',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      cmdclass={'test': PyTest},
      )
