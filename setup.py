from setuptools import setup
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
setup(name='cbpi4-DependentDelayActor',
      version='0.0.1',
      description='CraftBeerPi4 Actor Plugin to switch an actor after another actor has a required state and an optional delay',
      author='ChatGPT',
      author_email='',
      url='',
      include_package_data=True,
      license='GPLv3',
      package_data={
          '': ['*.txt', '*.rst', '*.yaml'],
          'cbpi4-DependentDelayActor': ['*','*.txt', '*.rst', '*.yaml']},
      packages=['cbpi4-DependentDelayActor'],
      long_description=long_description,
      long_description_content_type='text/markdown')
