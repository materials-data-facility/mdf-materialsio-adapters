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
    install_requires=['pypif_sdk', 'jsonschema>3', 'mdf_toolbox>=0.5.3'],
    include_package_data=True,
    entry_points={
        'materialsio.adapter': [
            'dft = mdf_matio.adapters.citrine:PIFDFTAdapter',
            # 'generic = mdf_matio.adapters.file:FileAdapter',
            'csv = mdf_matio.adapters.mappable:CSVAdapter',
            'crystal_structure = mdf_matio.adapters.basic_adapters:CrystalStructureAdapter',
            'electron_microscopy = mdf_matio.adapters.basic_adapters:ElectronMicroscopyAdapter',
            'generic = mdf_matio.adapters.basic_adapters:GenericFileAdapter',
            'filename = mdf_matio.adapters.basic_adapters:FilenameAdapter',
            'image = mdf_matio.adapters.basic_adapters:ImageAdapter',
            'json = mdf_matio.adapters.basic_adapters:JSONAdapter',
            'tdb = mdf_matio.adapters.basic_adapters:TDBAdapter',
            'xml = mdf_matio.adapters.basic_adapters:XMLAdapter',
            'yaml = mdf_matio.adapters.basic_adapters:YAMLAdapter'
        ]
    }
)
