"""Test the functions that group files into chunks"""

from mdf_matio.grouping import groupby_directory, groupby_file
import pytest
import os


@pytest.fixture
def example_files():
    return [
        (('a.in',), 'fake', {}),
        ((os.path.join('d', 'a.in'), 'a.in',), 'fake', {}),
        ((os.path.join('d', 'a.in'),), 'fake', {}),
        ((os.path.join('d', 'b.in'),), 'fake', {}),
        ((os.path.join('e', 'a.in'),), 'fake', {})
    ]


def test_groupby_direectory(example_files):
    groups = list(groupby_directory(example_files))

    # Should make 3 groups:
    #  1: ("a.in") and ("d/a.in", "a.in") <- directory of >1 file is the greatest common path
    #  2: ("d/a.in") and ("d/b.in") <- Files in the same directory
    #  3: ("e/a.in") <- File in the same directory
    # They are sorted in this order, which is alphabetical by directory name
    assert len(groups) == 3
    assert isinstance(groups[0], list)

    # Check the contents of group #1
    assert len(groups[0]) == 2
    files = set(x[0] for x in groups[0])
    assert ('a.in',) in files
    assert (os.path.join('d', 'a.in'), 'a.in') in files
    assert isinstance(groups[0][0], tuple)

    # Check the contents of group #2
    assert len(groups[1]) == 2
    files = set(x[0] for x in groups[1])
    assert os.path.join('d', 'a.in') not in files
    assert (os.path.join('d', 'a.in'),) in files
    assert (os.path.join('d', 'b.in'),) in files

    # Check the contents of group #3
    assert len(groups[2]) == 1
    assert groups[2] == [((os.path.join('e', 'a.in'),), 'fake', {})]


def test_groupby_file(example_files):
    groups = list(groupby_file(example_files))

    # Allowing grouping to complete
    #  Should produce three groups:
    #   0 and 1, and 1 + 2 share files. So 0, 1, 2 will be grouped
    #   3 and 4 are their own groups
    assert len(groups) == 3
    assert sorted(map(len, groups)) == [1, 1, 3]
    assert isinstance(groups[0], list)
    assert isinstance(groups[0][0], tuple)
