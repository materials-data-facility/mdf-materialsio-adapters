"""Tests for the Citrine adapters"""

from mdf_matio.adapters.citrine import PIFDFTAdapter
from pytest import fixture
import json
import os

cwd = os.path.dirname(__file__)


@fixture()
def example_dft():
    with open(os.path.join(cwd, 'data', 'pifdft.json')) as fp:
        return json.load(fp)


def test_pif_dft(example_dft):
    expected = {'material': {'elemental_proportions': {'Al': 1}},
                'dft': {'converged': True, 'exchange_correlation_functional': 'PAW',
                        'cutoff_energy': 650.0},
                'origin': {'type': 'computation', 'name': 'VASP', 'version': '5.3.2'}}
    assert PIFDFTAdapter().transform(example_dft) == expected
