"""Adapters for structured files"""
from materials_io.adapters.base import BaseAdapter
from typing import List, Tuple, Union
import jmespath


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


class JSONAdapter(BaseAdapter):
    """Converts JSON records into MDF format

    The JSON adapter requires a single context parameter: ``mapping``.
    Mapping defines the name of the MDF field (using '.'s to separate keys at different levels)
    to a JMESPath expression definine the location of the desired value(s).
    """

    def transform(self, metadata: dict,
                  context: Union[None, dict] = None) -> Union[None, List[dict]]:
        # We cannot handle JSON files if the user does not define a mapping
        if context is None:
            return None
        if 'mapping' not in context:
            return None

        # Get the "n/a" values
        na_values = context.get('na_values', [])
        if not isinstance(na_values, list):
            na_values = [na_values]

        # Compile the JMESPath expressions
        mdf_to_jmes = dict((tuple(x.split('.')), jmespath.compile(y))
                           for x, y in context['mapping'].items())

        # Get the list of records
        if metadata['line-delimited']:
            records = metadata['content']
        else:
            content = metadata['content']
            records = content if isinstance(content, list) else [content]

        # Generate entries
        sub_records = []
        for record in records:
            new_record = {}
            for key, expr in mdf_to_jmes.items():
                value = expr.search(record)
                if value is not None and value not in na_values:
                    _add_value(new_record, key, value)
            if len(new_record) > 0:
                sub_records.append(new_record)
        return sub_records if len(sub_records) > 0 else None
