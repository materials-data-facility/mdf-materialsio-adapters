"""Interfaces to the MaterialsIO parsers for use by the MDF"""

from mdf_matio.version import __version__  # noqa: F401
from materials_io.utils.interface import (get_available_adapters, ParseResult,
                                          get_available_parsers, run_all_parsers)
from mdf_matio.grouping import groupby_file, groupby_directory
from mdf_matio.validator import MDFValidator
from mdf_toolbox import dict_merge
from typing import Iterable, Set, List
from functools import reduce, partial
import logging
import os

logger = logging.getLogger(__name__)


_merge_func = partial(dict_merge, append_lists=True)
"""Function used to merge records"""


def get_mdf_parsers() -> Set[str]:
    """Get the list of parsers defined for the MDF

    Returns:
        ([str]): Names of parsers that are compatible with the MDF
    """
    return set([name for name, info in get_available_adapters().items()
                if info['class'].startswith('mdf_matio')])


def _merge_records(group: List[ParseResult]):
    """Merge a group of records

    Args:
        group ([ParseResult]): List of parse results to group
    """

    # Group the file list and parsers
    group_files = list(set(sum([tuple(x.group) for x in group], ())))
    group_parsers = '-'.join(sorted(set(sum([[x.parser] for x in group], []))))

    # Merge the metadata
    is_list = [isinstance(x.metadata, list) for x in group]
    if sum(is_list) > 1:
        raise NotImplementedError('We have not defined how to merge >1 list-type data')
    elif sum(is_list) == 1:
        list_data = group[is_list.index(True)].metadata
        if len(is_list) > 1:
            other_metadata = reduce(_merge_func,
                                    [x.metadata for x, t in zip(group, is_list) if not t])
            group_metadata = [_merge_func(x, other_metadata) for x in list_data]
        else:
            group_metadata = list_data
    else:
        group_metadata = reduce(_merge_func, [x.metadata for x in group])
    return ParseResult(group_files, group_parsers, group_metadata)


def _merge_files(parse_results: Iterable[ParseResult]) -> Iterable[ParseResult]:
    """Merge metadata of records associated with the same file(s)

    Args:
        parse_results (ParseResult): Generator of ParseResults
    Yields:
        (ParseResult): ParserResults merged for each file.
    """
    return map(_merge_records, groupby_file(parse_results))


def _merge_directories(parse_results: Iterable[ParseResult], dirs_to_group: List[str])\
        -> Iterable[ParseResult]:
    """Merge records from user-specified directories

    Args:
        parse_results (ParseResult): Generator of ParseResults
    Yields:
        (ParseResult): ParserResults merged for each record
    """

    # Add a path separator to the end of each directory
    #  Used to simplify checking whether each file is a subdirectory of the matched groups
    dirs_to_group = [d + os.path.sep for d in dirs_to_group]

    def is_in_directory(f):
        """Check whether a file is in one fo the directories to group"""
        f = os.path.dirname(f) + os.path.sep
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


def generate_search_index(data_url: str, validate_records=True, parse_config=None,
                          exclude_parsers=None, index_options=None) -> Iterable[dict]:
    """Generate a search index from a directory of data

    Args:
        data_url (str): Location of dataset to be parsed
        validate_records (bool): Whether to validate records against MDF Schemas
        parse_config (dict): Dictionary of parsing options specific to certain files/directories.
            Keys must be the path of the file or directory.
            Values are dictionaries of options for that directory, supported options include:
                group_by_directory: (bool) Whether to group all subdirectories of this
                        directory as single records
        exclude_parsers ([str]): Names of parsers to exclude
        index_options (dict): Indexing options used by MDF Connect
    Yields:
        (dict): Metadata records ready for ingestion in MDF search index
    """
    if parse_config is None:
        parse_config = {}
    # Get the list of parsers that have adapters defined in this package
    target_parsers = get_mdf_parsers()
    logging.info(f'Detected {len(target_parsers)} parsers: {target_parsers}')
    missing_parsers = set(get_available_parsers().keys()).difference(
        target_parsers)
    if len(missing_parsers) > 0:
        logging.warning(f'{len(missing_parsers)} parsers are not used: {missing_parsers}')
    if exclude_parsers is not None:
        target_parsers.difference_update(exclude_parsers)
        logging.info(f'Excluded {len(exclude_parsers)} parsers: {len(exclude_parsers)}')

    # Add root directory to the target path
    index_options = index_options or {}
    # TODO (wardlt): Figure out how this works with Globus URLs
    index_options['generic'] = {'root_dir': data_url}

    # Run the target parsers with their matching adapters on the directory
    parse_results = run_all_parsers(data_url, include_parsers=list(target_parsers),
                                    adapter_map='match', parser_context=index_options,
                                    adapter_context=index_options)
    # Merge by directory in the user-specified directories
    grouped_dirs = []
    for path, cfg in parse_config.items():
        if cfg.get('group_by_directory', False):
            grouped_dirs.append(path)
    logging.info(f'Grouping {len(grouped_dirs)} directories')
    parse_results = _merge_directories(parse_results, grouped_dirs)

    # TODO: Add these variables as arguments or fetch in other way
    dataset_metadata = None   # Provided by MDF directly
    validation_params = None  # Provided by MDF directly
    schema_branch = "master"  # Must be configurable, can be provided by MDF directly

    # Validate metadata and tweak into final MDF feedstock format
    # Will fail if any entry fails validation - no invalid entries can be allowed
    vald = MDFValidator(schema_branch=schema_branch)
    vald_gen = vald.validate_mdf_dataset(dataset_metadata, validation_params)
    # Yield validated dataset entry
    yield next(vald_gen)

    # Merge records associated with the same file
    for group in _merge_files(parse_results):
        # Skip records that include only generic metadata
        if group.parser == 'generic':
            continue

        # Loop over all produced records
        metadata = group.metadata if isinstance(group.metadata, list) else [group.metadata]

        # Record validation
        for record in metadata:
            yield vald_gen.send(record)

    vald_gen.send(None)
