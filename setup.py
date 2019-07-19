from setuptools import setup, find_packages
import os

# single source of truth for package version
version_ns = {}
with open(os.path.join("mdf_matio", "version.py")) as f:
    exec(f.read(), version_ns)
version = version_ns['__version__']

setup(
    name="mdf_matio",
    version=version,
    packages=find_packages(),
    install_requires=['mdf_toolbox>=0.4.2', 'stevedore>=1.28.0'],
    include_package_data=True,
)
