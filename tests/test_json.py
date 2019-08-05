from materials_io.utils.interface import execute_parser
import os

json_dir = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'example-files', 'json')


def test_simple():
    # Run the parser without the adapter
    my_file = os.path.join(json_dir, 'simple.json')
    assert execute_parser('json', [my_file]) == {'line-delimited': False,
                                                 'content': {'composition': 'CuZr'}}

    # Make sure parser requires a mapping
    assert execute_parser('json', [my_file], adapter='json') is None
    assert execute_parser('json', [my_file], adapter='json', context={}) is None

    # Test out the mapping
    results = execute_parser('json', [my_file], adapter='json',
                             context={'mapping': {'material.composition': 'composition'}})
    assert results == [{'material': {'composition': 'CuZr'}}]


def test_list():
    # Run the parser without the adapter
    my_file = os.path.join(json_dir, 'list.json')
    assert not execute_parser('json', [my_file])['line-delimited']

    # Test out the mapping
    results = execute_parser('json', [my_file], adapter='json',
                             context={'mapping': {'material.composition': 'composition'}})
    assert results == [{'material': {'composition': 'CuZr'}}, {'material': {'composition': 'Fe'}}]

    # Add na-values to the mapping
    results = execute_parser('json', [my_file], adapter='json',
                             context={'mapping': {'material.composition': 'composition',
                                                  'value': 'oqmd.delta_e'},
                                      'na_values': 'N/A'})
    assert results == [{'material': {'composition': 'CuZr'}},
                       {'material': {'composition': 'Fe'}, 'value': 0}]


def test_ldjson():
    # Run the parser without the adapter
    my_file = os.path.join(json_dir, 'line-delimited.json')
    assert execute_parser('json', [my_file])['line-delimited']

    # Test out the mapping
    results = execute_parser('json', [my_file], adapter='json',
                             context={'mapping': {'material.composition': 'composition'}})
    assert results == [{'material': {'composition': 'NaCl'}},
                       {'material': {'composition': 'LiFePO4'}}]
