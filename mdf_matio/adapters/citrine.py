"""Adapters that pull metadata from parsers that produce PIF-format data"""

from materials_io.adapters.base import BaseAdapter
from pypif_sdk.interop.mdf import _to_user_defined as pif_to_feedstock
from typing import Dict, Tuple, Type
from mdf_toolbox import dict_merge
from pypif.pif import loado


class CitrineAdapter(BaseAdapter):
    """Base class for Citrine adapters

    Requires users to define the translation table"""

    def get_translations(self) -> Dict[str, Dict[str, Tuple[str, Type]]]:
        """The translation table from PIF field to MDF field

        The dictionary contains multiple levels. The first level is the
        "block" in the corresponding MDF output. The second level is the
        name of the field in a flattened PIF and the value of that key is the name
        of the field in the MDF block and a function that translates
        the PIF datatype to the MDF datatype

        Returns:
            (dict): Translation dict for this field
        """

        return {
            'material': {'elemental_proportion': ('elemental_proportions', dict)},
        }

    def transform(self, pif: dict, context=None) -> dict:
        # Flatten the pif into smaller records
        pif = pif_to_feedstock(loado(pif))

        # Map the records to an MDF field
        record = {}
        for block, mapping in self.get_translations().items():
            new_block = {}
            for pif_field, mdf_field_info in mapping.items():
                mdf_field = mdf_field_info[0]
                translator = mdf_field_info[1]
                if pif_field in pif:
                    new_block[mdf_field] = translator(pif[pif_field])
            if new_block:
                record[block] = new_block
        return record


class PIFDFTAdapter(CitrineAdapter):
    """Adapter for the PIF DFT parser"""

    def get_translations(self):
        return dict_merge(super().get_translations(), {
            "dft": {
                "Converged": ("converged", bool),
                "XC_Functional": ("exchange_correlation_functional", str),
                "Cutoff_Energy_eV": ("cutoff_energy", float)
            },
            "crystal_structure": {
                "Space_group_number": ("space_group_number", int),
                "Number_of_atoms_in_unit_cell": ("number_of_atoms", float),
                "Unit_cell_volume_AA_3": ("volume", float)
            },
        })

    def transform(self, pif: dict, context=None) -> dict:
        output = super().transform(pif)

        # Add in the method types
        software = pif['properties'][0]['methods'][0]['software'][0]
        output['origin'] = {'type': 'computation', 'name': software['name']}
        if 'version' in software:
            output['origin']['version'] = software['version']

        return output

    def version(self):
        return '0.0.1'
