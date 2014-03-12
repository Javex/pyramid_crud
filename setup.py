import os
from setuptools import setup, find_packages, Command

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except:
    README = CHANGES = ''

docs_extras = [
    'Sphinx',
    'docutils',
    'sphinx_rtd_theme',
]


tests_require = [
    'pytest',
]

requires = [
    'pyramid',  # framework
    'Mako',  # templating
    'pyramid_mako',  # templating
    'SQLAlchemy>=0.8',  # database
    'WTForms',  # forms
    'wtforms_alchemy',  # forms
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
      version='0.1',
      description='CRUD interface for the Pyramid Framework',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Intended Audience :: Developers",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.2",
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
      tests_require=tests_require,
      cmdclass={'test': PyTest},
      )
