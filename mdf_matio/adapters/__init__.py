"""Module for all adapters that turn MaterialsIO data into the MDF format"""
from materials_io.adapters.base import BaseAdapter

noop_parsers = ['image', 'em']
"""List of parsers that already produce information in the MDF formta"""


class FileAdapter(BaseAdapter):
    """Turns the file information into a list, wraps it inside of a dictionary"""

    def transform(self, metadata: dict) -> dict:
        # If data type is unknown, say so (MDF requires this field)
        if 'data_type' not in metadata:
            metadata['data_type'] = 'Unknown'

        # Wrap and return
        return {'files': [metadata]}

    def version(self):
        return '0.0.1'

