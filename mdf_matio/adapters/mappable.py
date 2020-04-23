"""Adapters for structured files"""
from materials_io.adapters.base import BaseAdapter
from typing import List, Tuple, Union


def _add_value(record, key: Tuple[str], value):
    """Adds value to MDF record

    Args:
        record (dict): Record to be added to
        key ((str)): Location of new record as a listing of the
        value: Value to be stored
    """

    if len(key) == 1:
        record[key[0]] = value
    else:
        if key[0] not in record:
            record[key[0]] = {}
        _add_value(record[key[0]], key[1:], value)


class CSVAdapter(BaseAdapter):
    """Execute mapping operation on CSV adapters

    The CSV adapter requires a single context parameter: ``mapping``.
    Mapping defines the name of the MDF field (using '.'s to separate keys at different levels)
    to the name of the column.
    """

    def transform(self, metadata: dict,
                  context: Union[None, dict] = None) -> Union[None, List[dict]]:
        # We cannot handle CSV files if the user does not define a mapping
        if context is None:
            return None
        if 'mapping' not in context:
            return None

        # Parse the mapping
        col_to_mdf = dict((y, x.split('.')) for x, y in context['mapping'].items())

        # Generate entries
        sub_records = []
        for record in metadata['records']:
            new_record = {}
            for col, key in col_to_mdf.items():
                if col in record:
                    _add_value(new_record, key, record[col])
            if len(new_record) > 0:
                sub_records.append(new_record)
        return sub_records if len(sub_records) > 0 else None
