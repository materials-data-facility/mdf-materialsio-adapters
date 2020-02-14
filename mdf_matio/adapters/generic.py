import json
import os

import mdf_toolbox

from materials_io.adapters.base import BaseAdapter


class GenericMDFAdapter(BaseAdapter):
    """Generic adapter for MDF extractors. Adapts metadata with MDF-format fields present."""

    def __init__(self, schema_path=None):
        """Create a GenericMDFAdapter object.

        Arguments:
            schema_path (str): The path to the MDF schema directory or MDF record schema file.
                    Default None, to set later.
        """
        self.schema_path = schema_path

    def transform(self, metadata, context=None):
        """Transform the metadata by filtering non-MDF fields away.

        Arguments:
            metadata (dict): The metadata to transform.
            context (dict): Additional context for the adapter. Default None.
                    Fields used:
                        schema_path (str): The path to the MDF schema directory
                                or MDF record schema file.

        Returns:
            dict: The transformed metadata.
        """
        if context is None:
            context = {}
        schema_path = context.get("schema_path", self.schema_path)
        if not schema_path:
            raise ValueError("schema_path must be provided, in context or through __init__().")
        # Normalize schema_path to point at record.json file (base schema for MDF record)
        if os.path.isdir(schema_path):
            schema_path = os.path.join(schema_path, "record.json")
        if not os.path.exists(schema_path):
            raise FileNotFoundError("MDF schema file '{}' not found".format(schema_path))
        # Read and expand MDF schema
        with open(schema_path) as f:
            full_schema = mdf_toolbox.expand_jsonschema(json.load(f), os.path.dirname(schema_path))
        # Turn full MDF schema into self-mapping (mdf.field:mdf.field)
        # Condense into mdf_field: type, then replace type value with field name
        automap = {}
        for field in mdf_toolbox.condense_jsonschema(full_schema, include_containers=False,
                                                     list_items=False).keys():
            automap[field] = field
        # Now use automapping to pull out MDF-format fields in metadata
        # Discard empty values
        filtered_metadata = mdf_toolbox.translate_json(metadata, automap, na_values=[[], {}, None])

        return filtered_metadata
