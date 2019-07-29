"""Tests for the key 'make search index' function"""

from mdf_matio import generate_search_index
import os


file_dir = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'example-files')


def test_parse():
    records = list(generate_search_index(file_dir, False))
    assert len(records) == 4
