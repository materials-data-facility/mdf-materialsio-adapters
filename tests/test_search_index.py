"""Tests for the key 'make search index' function"""

from mdf_matio import generate_search_index
from tarfile import TarFile
import pytest
import os


file_dir = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'example-files')

# Unpack the VASP calculation
with TarFile.open(os.path.join(file_dir, 'calc', 'AlNi_static_LDA.tar.gz')) as t:
    t.extractall(os.path.join(file_dir, 'calc'))


@pytest.mark.xfail
def test_parse():
    records = list(generate_search_index(file_dir, False))
    assert len(records) == 5


@pytest.mark.xfail
def test_parse_with_mapping():
    index_options = {'csv': {'mapping': {'material.composition': 'composition'}},
                     'json': {'mapping': {'material.composition': 'composition'}}}
    records = list(generate_search_index(file_dir, False, index_options=index_options))
    assert len(records) == 12
    assert all(isinstance(x, dict) for x in records)

    # Find the record for the csv directory
    my_dir = os.path.join('group-by-dir', 'csv')
    csv_merged = [x for x in records if any(my_dir in y['path'] for y in x['files'])][0]
    assert 'material' in csv_merged
    assert 'image' in csv_merged

    # Find the record for the csv directory
    my_dir = 'json' + os.path.sep
    json_files = [x for x in records if any(my_dir in y['path'] for y in x['files'])]
    assert len(json_files) == 5
