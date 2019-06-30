from setuptools import setup

from media_management_scripts import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='media_management_scripts',
      version=version,
      description='Scripts for managing media',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/raydouglass/media_management_scripts',
      author='Ray Douglass',
      author_email='ray@raydouglass.com',
      license='Apache',
      packages=[
          'media_management_scripts',
          'media_management_scripts.commands',
          'media_management_scripts.silver_tube',
          'media_management_scripts.support'
      ],
      zip_safe=False,
      scripts=[
          'bin/manage-media',
          'bin/convert-dvds',
          'bin/silver-tube',
          'bin/tvdb-api'
      ],
      install_requires=[
          'requests',
          'pyOpenSSL',
          'texttable',
          'tmdbsimple',
          'argcomplete',
          'tempita',
          'SQLAlchemy',
          'pysrt',
          'paramiko',
          'scp',
          'pythondialog',
          'pyyaml',
          'pyparsing',
          'pycaption',
          'python-magic'
      ])
