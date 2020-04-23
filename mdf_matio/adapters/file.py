from materials_io.adapters.base import BaseAdapter
import os


class FileAdapter(BaseAdapter):
    """Turns the file information into a list, wraps it inside of a dictionary"""

    def transform(self, metadata: dict, context=None) -> dict:
        # If data type is unknown, say so (MDF requires this field)
        if 'data_type' not in metadata:
            metadata['data_type'] = 'Unknown'

        # If a root directory is given, compute the relative path
        if context is not None and 'root_dir' in context:
            metadata['path'] = os.path.relpath(metadata['path'], context['root_dir'])

        # Wrap and return
        return {'files': [metadata]}

    def version(self):
        return '0.0.1'
