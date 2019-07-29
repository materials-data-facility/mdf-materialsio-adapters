"""Interfaces to the MaterialsIO parsers for use by the MDF"""

from materials_io.utils.interface import (get_available_adapters, ParseResult,
                                          run_all_parsers, get_available_parsers)
from mdf_matio.validation import validate_against_mdf_schemas
from mdf_matio.adapters import noop_parsers
from mdf_matio.grouping import groupby_file
from mdf_toolbox import dict_merge
from jsonschema.exceptions import SchemaError
from functools import reduce, partial
from typing import Iterable, Set
import logging

logger = logging.getLogger(__name__)


def get_mdf_parsers() -> Set[str]:
    """Get the list of parsers defined for the MDF

    Returns:
        ([str]): Names of parsers that are compatible with the MDF
    """
    return set(noop_parsers + [name for name, info in get_available_adapters().items()
                               if info['class'].startswith('mdf_matio')])


def _merge_files(parse_results: Iterable[ParseResult]) -> Iterable[ParseResult]:
    """Merge metadata of records associated with the same file(s)

    Args:
        parse_results (ParseResult): Generator of ParseResults
    Yields:
        (ParseResult): ParserResults merged for each file.
    """

    # Make sure to merge using the append lists option
    merge_func = partial(dict_merge, append_lists=True)

    for group in groupby_file(parse_results):
        # Get the list of files associated with this group
        group_files = list(set(sum([tuple(x.group) for x in group], ())))
        group_metadata = reduce(merge_func, [x.metadata for x in group])
        group_parsers = sorted(set(sum([[x.parser] for x in group], [])))
        yield ParseResult(group_files, group_parsers, group_metadata)


# TODO (wardlt): Accept context for files (e.g., mapping for JSON files)
def generate_search_index(directory: str, validate_records=True,
                          exclude_parsers=None) -> Iterable[dict]:
    """Generate a search index from a directory of data

    Args:
        directory (str): Path to a directory to be parsed
        validate_records (bool): Whether to validate records against MDF Schemas
        exclude_parsers ([str]): Names of parsers to exclude
    Yields:
        (dict): Metadata records ready for ingestion in MDF search index
    """

    # Get the list of parsers that have adapters defined in this package
    target_parsers = get_mdf_parsers()
    logging.info(f'Detected {len(target_parsers)} parsers: {target_parsers}')
    missing_parsers = set(get_available_parsers().keys()).difference(target_parsers)
    logging.warning(f'{len(missing_parsers)} parsers are not used: {missing_parsers}')
    if exclude_parsers is not None:
        target_parsers.difference_update(exclude_parsers)
        logging.info(f'Excluded {len(exclude_parsers)} parsers: {len(exclude_parsers)}')

    # Run the target parsers with their matching adapters on the directory
    parse_results = run_all_parsers(directory, include_parsers=target_parsers,
                                    adapter_map='match')

    # TODO (wardlt): Gather the directories with extra parse information

    # Merge records associated with the same file
    for group in _merge_files(parse_results):

        # Skip records that include only generic metadata
        if group.parser == ['generic']:
            continue

        # Validate records, but do not halt execution if they fail
        try:
            if validate_records:
                validate_against_mdf_schemas(group.metadata)
            yield group.metadata
        except SchemaError:
            logger.warning(f'{group.group} failed validation. Parsers: {group.parser}')
