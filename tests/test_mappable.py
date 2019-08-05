from materials_io.utils.interface import execute_parser
import os

csv_file = os.path.join(os.path.dirname(__file__), '..', 'notebooks',
                        'example-files', 'test.csv')


def test_csv():
    # Only works with mapping
    output = execute_parser('csv', [csv_file], adapter='csv',
                            context={'mapping': {'material.composition': 'composition'}})
    assert output == [{'material': {'composition': 'NaCl'}},
                      {'material': {'composition': 'LiFePO4'}}]

    # No effect
    assert execute_parser('csv', [csv_file], adapter='csv', context={}) is None
    assert execute_parser('csv', [csv_file], adapter='csv') is None
