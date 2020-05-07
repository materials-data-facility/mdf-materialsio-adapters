from mdf_matio.adapters.generic import GenericMDFAdapter


# Adapters that require no extra processing and can just use the GenericMDFAdapter

class CrystalStructureAdapter(GenericMDFAdapter):
    """Adapt the CrystalStructureExtractor"""
    # No extra processing required
    pass


class ElectronMicroscopyAdapter(GenericMDFAdapter):
    """Adapt the ElectronMicroscopyExtractor"""
    # No extra processing required
    pass


class GenericFileAdapter(GenericMDFAdapter):
    """Adapt the GenericFileExtractor"""

    def transform(self, metadata, context=None):
        """Transform MatIO's GenericFileParser to MDF format.
        Changes:
            - Add 'globus' (Globus EP/path link)
            - Add 'url' (HTTP link, or None for no HTTP access)
            - Remove 'path' (done by GenericMDFAdapter)

        Arguments:
            metadata (dict): The metadata from GenericFileParser to adapt.
            context (dict): Additional adapting requirements. Default None.
                globus_uri (str): The UUID and path of the Globus-accessible location
                        this file is accessible at. Default None, to add no URI.
                http_link (str): The HTTP link this file is accessible at.
                        Default None, to indicate this file is not HTTP accessible.

        Returns:
            dict: The transformed metadata.
        """
        if context is None:
            context = {}
        if context.get("globus_uri"):
            metadata["globus"] = context["globus_uri"]
        metadata["url"] = context.get("http_link")
        metadata = {
            "files": [metadata]
        }
        filtered_metadata = super().transform(metadata, context)
        # The `files` block differs from nearly every other MDF-schema block,
        # because multiple files can be listed. The GenericMDFAdapter flattens the structure,
        # which removes the list, so it must be added back in.
        # Only one file is extracted at a time, so this works.
        return {
            "files": [filtered_metadata["files"]]
        }


class FilenameAdapter(GenericMDFAdapter):
    """Adapt the FilenameExtractor"""
    # No extra processing required
    pass


class ImageAdapter(GenericMDFAdapter):
    """Adapt the ImageExtractor"""
    # No extra processing required
    pass


class JSONAdapter(GenericMDFAdapter):
    """Adapt the JSONExtractor"""
    # Extra processing doesn't really make sense;
    # If output not in MDF format, JSON mapping was incorrect
    pass


class TDBAdapter(GenericMDFAdapter):
    """Adapt the TDBExtractor"""
    # No extra processing required
    pass


class XMLAdapter(GenericMDFAdapter):
    """Adapt the XMLExtractor"""
    # Extra processing doesn't really make sense;
    # If output not in MDF format, XML mapping was incorrect
    pass


class YAMLAdapter(GenericMDFAdapter):
    """Adapt the YAMLExtractor"""
    # Extra processing doesn't really make sense;
    # If output not in MDF format, YAML mapping was incorrect
    pass
