from os import path
from setuptools import setup, find_packages

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="cbpi4-DependentDelayActor",
    version="0.0.3",
    description="CraftBeerPi4 actor plugin with dependency actors, auto switching, delay and dashboard notifications",
    author="gerrywin",
    url="https://github.com/gerrywin/cbpi4-DependentDelayActor",
    packages=find_packages(),
    include_package_data=True,
    package_data={"cbpi4_DependentDelayActor": ["*.yaml"]},
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPLv3",
    python_requires=">=3.9",
)
