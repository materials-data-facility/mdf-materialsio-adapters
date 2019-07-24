"""Interfaces to the MaterialsIO parsers for use by the MDF"""

from materials_io.utils.interface import get_available_adapters, ParseResult, run_all_parsers
from mdf_matio.validation import validate_against_mdf_schemas
from mdf_matio.adapters import noop_parsers
from mdf_matio.grouping import groupby_file
from mdf_toolbox import dict_merge
from jsonschema.exceptions import SchemaError
from functools import reduce
from typing import Iterable
import logging

logger = logging.getLogger(__name__)


def _merge_files(parse_results: Iterable[ParseResult]) -> Iterable[ParseResult]:
    """Merge metadata of records associated with the same file(s)

    Args:
        parse_results (ParseResult): Generator of ParseResults
    Yields:
        (ParseResult): ParserResults merged for each file
    """

    for group in groupby_file(parse_results):
        # Get the list of files associated with this group
        group_files = list(set(sum([tuple(x.group) for x in group], ())))
        group_metadata = reduce(dict_merge, [x.metadata for x in group])
        yield ParseResult(group_files, 'merged', group_metadata)


# TODO (wardlt): Accept context for files (e.g., mapping for JSON files)
def generate_search_index(directory: str) -> Iterable[dict]:
    """Generate a search index from a directory of data

    Args:
        directory (str): Path to a directory to be parsed
    Yields:
        (dict): Metadata records ready for ingestion in MDF search index
    """

    # Get the list of parsers that have adapters defined in this package
    target_parsers = noop_parsers + [name for name, info in get_available_adapters().items()
                                     if info['class'].startswith('mdf_matio')]
    logging.info(f'Detected {len(target_parsers)} parsers: {target_parsers}')

    # Run the target parsers with their matching adapters on the directory
    parse_results = run_all_parsers(directory, include_parsers=target_parsers,
                                    adapter_map='match')

    # TODO (wardlt): Gather the directories with extra parse information

    # Merge records associated with the same file
    for group in _merge_files(parse_results):
        try:
            validate_against_mdf_schemas(group.metadata)
            yield group.metadata
        except SchemaError:
            logger.warning(f'{group.group} failed validation.')
