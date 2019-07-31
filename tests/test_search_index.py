"""Tests for the key 'make search index' function"""

from mdf_matio import generate_search_index
import os


file_dir = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'example-files')


def test_parse():
    records = list(generate_search_index(file_dir, False))
    assert len(records) == 5


def test_parse_with_mapping():
    records = list(generate_search_index(file_dir, False,
                                         index_options={'csv': {'mapping': {'material.composition': 'composition'}}}))
    assert len(records) == 7
    assert all(isinstance(x, dict) for x in records)

    # Find the record for the csv directory
    my_dir = os.path.join('group-by-dir', 'csv')
    csv_merged = [x for x in records if any(my_dir in y['path'] for y in x['files'])][0]
    assert 'material' in csv_merged
    assert 'image' in csv_merged
