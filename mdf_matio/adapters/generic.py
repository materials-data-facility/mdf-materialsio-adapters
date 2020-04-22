import os

import jsonschema
import mdf_toolbox

from materials_io.adapters.base import BaseAdapter


class GenericMDFAdapter(BaseAdapter):
    """Generic adapter for MDF extractors. Adapts metadata with MDF-format fields present.

    This class's transformation performs two tasks:
        - Removing all fields that are not in the MDF schema
        - Removing all fields for which the value is empty (empty list, empty dict, or None)

    Extractors that output MDF-format metadata, such as the MDF-contributed extractors,
    need very little or no transformation. As MatIO extractors are intended to always
    be backwards-compatible, with the only changes being additional metadata returned,
    this base adapter class grants all MDF adapters (subclasses of this adapter)
    forwards-compatibility by filtering out any additional metadata. This significantly
    reduces the maintenance burden for MDF adapters.

    All MDF adapters should subclass this adapter, and should call this adapter's transform()
    to gain forwards-compatibility.
    """

    def __init__(self, schema_branch="master", schema_uri=None):
        """Create a GenericMDFAdapter object, using a specified MDF schema.

        Arguments:
            schema_branch (str): The branch of the MDF data-schemas Github repository to
                    download and validate against. Default "master".
            schema_uri (str): The uri to the MDF schema location. Local and nonlocal locations
                    are supported. Default None, to use the Github branch instead.

        Note:
            schema_uri supercedes schema_branch - if schema_uri is specified,
            schema_branch is ignored.
        """
        if schema_uri:
            schema_branch = None

        # Generate URI from Github if branch supplied
        if schema_branch:
            schema_uri = ("https://raw.githubusercontent.com/materials-data-facility/"
                          "data-schemas/{}/schemas/".format(schema_branch))
        # If URI is bare file path, make into URI
        elif os.path.exists(schema_uri):
            schema_uri = "{}{}{}".format(
                                    "file://" if not schema_uri.startswith("file://") else "",
                                    os.path.abspath(schema_uri),
                                    "/" if schema_uri.endswith("/") else "")
        # Fetch record schema with resolver
        resolver = jsonschema.RefResolver(schema_uri, None)
        base_schema = resolver.resolve("record.json")[1]
        # Expand JSONSchema (can provider premade resolver)
        full_schema = mdf_toolbox.expand_jsonschema(base_schema, resolver=resolver)

        # Turn full MDF schema into self-mapping/automap (mdf.field:mdf.field)
        # Condense into mdf_field: type, then replace type value with field name
        self.automap = {}
        for field in mdf_toolbox.condense_jsonschema(full_schema, include_containers=False,
                                                     list_items=False).keys():
            self.automap[field] = field

    def transform(self, metadata, context=None):
        """Transform the metadata by filtering non-MDF fields away.

        Arguments:
            metadata (dict): The metadata to transform.
            context (dict): Additional context for the adapter. Default None.
                    No fields are used/read in this adapter.

        Returns:
            dict: The transformed metadata.
        """
        if context is None:
            context = {}
        # Use automapping to pull out MDF-format fields in metadata
        # Discard empty values
        filtered_metadata = mdf_toolbox.translate_json(metadata, self.automap,
                                                       na_values=[[], {}, None])
        return filtered_metadata
