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
    # No extra processing required
    pass


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
