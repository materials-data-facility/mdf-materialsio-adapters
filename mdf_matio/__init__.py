"""Interfaces to the MaterialsIO parsers for use by the MDF"""

from materials_io.utils.interface import (get_available_adapters, ParseResult,
                                          run_all_parsers, get_available_parsers)
from mdf_matio.grouping import groupby_file, groupby_directory
from mdf_matio.validation import validate_against_mdf_schemas
from mdf_matio.adapters import noop_parsers
from mdf_toolbox import dict_merge
from jsonschema.exceptions import SchemaError
from typing import Iterable, Set, List
from functools import reduce, partial
from glob import glob
import logging
import json
import os

logger = logging.getLogger(__name__)


_merge_func = partial(dict_merge, append_lists=True)
"""Function used to merge records"""


def get_mdf_parsers() -> Set[str]:
    """Get the list of parsers defined for the MDF

    Returns:
        ([str]): Names of parsers that are compatible with the MDF
    """
    return set(noop_parsers + [name for name, info in get_available_adapters().items()
                               if info['class'].startswith('mdf_matio')])


def _merge_records(group: List[ParseResult]):
    """Merge a group of records

    Args:
        group ([ParseResult]): List of parse results to group
        """
    group_files = list(set(sum([tuple(x.group) for x in group], ())))
    group_metadata = reduce(_merge_func, [x.metadata for x in group])
    group_parsers = '-'.join(sorted(set(sum([[x.parser] for x in group], []))))
    return ParseResult(group_files, group_parsers, group_metadata)


def _merge_files(parse_results: Iterable[ParseResult]) -> Iterable[ParseResult]:
    """Merge metadata of records associated with the same file(s)

    Args:
        parse_results (ParseResult): Generator of ParseResults
    Yields:
        (ParseResult): ParserResults merged for each file.
    """
    return map(_merge_records, groupby_file(parse_results))


def _merge_directories(parse_results: Iterable[ParseResult], dirs_to_group: List[str]) -> Iterable[ParseResult]:
    """Merge records from user-specified directories

    Args:
        parse_results (ParseResult): Generator of ParseResults
    Yields:
        (ParseResult): ParserResults merged for each record
    """

    # Add a path separator to the end of each directory
    #  Used to simplify checking whether each file is a subdirectory of the matched groups
    dirs_to_group = [d + os.pathsep for d in dirs_to_group]

    def is_in_directory(f):
        """Check whether a file is in one fo the directories to group"""
        f = os.path.dirname(f) + os.pathsep
        return any(f.startswith(d) for d in dirs_to_group)

    # Gather records that are in directories to group or any of their subdirectories
    flagged_records = []
    for record in parse_results:
        if any(is_in_directory(f) for f in record.group):
            flagged_records.append(record)
        else:
            yield record

    # Once all of the parse results are through, group by directory
    for group in groupby_directory(flagged_records):
        yield _merge_records(group)


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

    # Find directories with extra parse information
    parse_config = glob(os.path.join(directory, '**', 'mdf.json'), recursive=True)
    logging.info(f'Found {len(parse_config)} directories with extra parsing information')

    # Run the target parsers with their matching adapters on the directory
    parse_results = run_all_parsers(directory, include_parsers=target_parsers,
                                    adapter_map='match')

    # Merge by directory in the user-specified directories
    grouped_dirs = []
    for p in parse_config:
        with open(p) as fp:
            cfg = json.load(fp)
        if cfg.get('parse_by_directory', False):
            grouped_dirs.append(os.path.abspath(os.path.dirname(p)))
    logging.info(f'Grouping {len(grouped_dirs)} directories')
    parse_results = _merge_directories(parse_results, grouped_dirs)

    # Merge records associated with the same file
    for group in _merge_files(parse_results):

        # Skip records that include only generic metadata
        if group.parser == 'generic':
            continue

        # Validate records, but do not halt execution if they fail
        try:
            if validate_records:
                validate_against_mdf_schemas(group.metadata)
            yield group.metadata
        except SchemaError:
            logger.warning(f'{group.group} failed validation. Parsers: {group.parser}')
