from setuptools import setup

setup(name='media_management_scripts',
      version='0.0.4',
      description='Scripts for managing media',
      url='',
      author='Ray Douglass',
      author_email='ray@raydouglass.com',
      license='MIT',
      packages=[
          'media_management_scripts',
          'media_management_scripts.support'
      ],
      zip_safe=False,
      scripts=[
          'bin/manage-media',
          'bin/convert-dvds'
      ],
      install_requires=[
          'requests',
          'texttable',
          'tmdbsimple',
          'argcomplete',
          'tempita'
      ])
