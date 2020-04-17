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
    install_requires=['pypif_sdk', 'jmespath>=0.9.4', 'jsonschema>3', 'mdf_toolbox>=0.5.2'],
    include_package_data=True,
    entry_points={
        'materialsio.adapter': [
            'dft = mdf_matio.adapters.citrine:PIFDFTAdapter',
            'generic = mdf_matio.adapters:FileAdapter',
            'csv = mdf_matio.adapters.mappable:CSVAdapter',
            'json = mdf_matio.adapters.mappable:JSONAdapter',
        ],
        'materialsio.parser': [
            'json = mdf_matio.parsers.json:JSONParser'
        ]
    }
)
