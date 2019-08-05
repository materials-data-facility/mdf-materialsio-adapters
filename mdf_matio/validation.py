"""Tools for validating against MDF schema"""

from jsonschema import Draft7Validator, RefResolver


# Make the schema resolver: Using a module-level variable to leverage RefResolvers' cache
_schema_repo = "https://raw.githubusercontent.com/materials-data-facility/" \
               "data-schemas/master/schemas/"
_ref_resolver = RefResolver(_schema_repo, None)


def validate_against_mdf_schemas(document):
    """Validate a metadata record against the MDF record schema

    Note: Requires an internet connection to GitHub

    Args:
        document (dict): Document instance to be validated
    Raises:
        (jsonschema.SchemaError) If the schema fails to validate
    """

    # Get record schema
    _, schema = _ref_resolver.resolve("record.json")

    # Make the validator
    validator = Draft7Validator(schema, resolver=_ref_resolver)

    # Test the document
    validator.validate(document)
