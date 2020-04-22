"""Interfaces to the MaterialsIO parsers for use by the MDF"""

from mdf_matio.version import __version__  # noqa: F401
from materials_io.utils.interface import (get_available_adapters, ParseResult, get_adapter,
                                          run_all_parsers, get_available_parsers)
from mdf_matio.grouping import groupby_file, groupby_directory
from mdf_matio.validator import Validator
from mdf_matio.adapters import noop_parsers
from mdf_toolbox import dict_merge
from jsonschema.exceptions import SchemaError
from typing import Iterable, Set, List
from functools import reduce, partial
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


def _call_xtracthub(data_url: str, index_options: dict, target_parsers: Set[str]) -> Iterable[ParseResult]:
    """Call out to XtractHub to get the metadata and perform the adapting

    Args:
        data_url (str): Pointer to the location of the data (currently only globus:// supported)  # TODO: HTTPS
        index_options (dict): Arguments for the parsers. Dictionary of "parser name" mapped to a dictionary which
            is passed to the `context` option of the associated parser and adapter.
        target_parsers ([str[): List of the parsers to run
    Yields:
        (ParseResult) Individual parsing records
    """

    # Call to XH
    # TODO: Make API call with the Globus path, tokens, and desired parsers? [Configuration TBD]

    # Get the list of adapters
    adapters = get_available_adapters()
    adapter_map = dict((x, x) for x in target_parsers if x in adapters)

    # Wait for XH or Globus transfer to finish, whatever Tyler thinks is best for working with XH
    # TODO: Hold until metadata file is on disk

    # Read metadata file and apply adapters
    # TODO: Tyler is switching to a "individual parser" rather than "call matio" model needed for this loop
    with open('xtracthub.jsonld', 'r') as fp:  # TODO: Identify correct file name
        for line in fp:  # TODO: Make this loop parallel with Pool.imap_unordered
            # File is in JSON-LD format: {'group': [str], 'parser': str, 'metadata'': dict}
            record = json.loads(line)

            # Adapt the metadata, if needed
            parser = record['parser']
            metadata = record['metadata']
            if parser in adapter_map:
                # Get the adapter and any context needed for the transformation
                adapter = get_adapter(parser)
                context = index_options.get(parser, {})

                # Invoke the adapter
                try:
                    metadata = adapter.transform(metadata, context)
                except Exception:
                    logger.warning(f'Adapter for {parser} failed')
                    continue
                if metadata is None:
                    continue

            yield ParseResult(record['group'], record['parser'], metadata)


# TODO (WardLt): Where does this run? [FuncX? Automate? Next challenge, after running locally and figuring out Auth]
def generate_search_index(data_url: str, validate_records=True, parse_config=None,
                          exclude_parsers=None, index_options=None) -> Iterable[dict]:
    """Generate a search index from a directory of data

    Args:
        data_url (str): Location of dataset to be parsed
        validate_records (bool): Whether to validate records against MDF Schemas
        parse_config (dict): Dictionary of parsing options specific to certain files/directories.
            Keys must be the path of the file or directory.
            Values are dictionaries of options for that directory, supported options include:
                group_by_directory: (bool) Whether to group all subdirectories of this directory as single records
        exclude_parsers ([str]): Names of parsers to exclude
        index_options (dict): Indexing options used by MDF Connect
    Yields:
        (dict): Metadata records ready for ingestion in MDF search index
    """

    # Get the list of parsers that have adapters defined in this package
    target_parsers = get_mdf_parsers()
    logging.info(f'Detected {len(target_parsers)} parsers: {target_parsers}')
    missing_parsers = set(get_available_parsers().keys()).difference(
        target_parsers).difference(['noop'])
    if len(missing_parsers) > 0:
        logging.warning(f'{len(missing_parsers)} parsers are not used: {missing_parsers}')
    if exclude_parsers is not None:
        target_parsers.difference_update(exclude_parsers)
        logging.info(f'Excluded {len(exclude_parsers)} parsers: {len(exclude_parsers)}')

    # Add root directory to the target path
    index_options = index_options or {}
    index_options['generic'] = {'root_dir': data_url}  # TODO (wardlt): Figure out how this works with Globus URLs

    # Run the target parsers with their matching adapters on the directory
    parse_results = _call_xtracthub(data_url, index_options, target_parsers)

    # Merge by directory in the user-specified directories
    grouped_dirs = []
    for path, cfg in parse_config.items():
        if cfg.get('group_by_directory', False):
            grouped_dirs.append(path)
    logging.info(f'Grouping {len(grouped_dirs)} directories')
    parse_results = _merge_directories(parse_results, grouped_dirs)

    # Merge records associated with the same file
    for group in _merge_files(parse_results):
        # Skip records that include only generic metadata
        if group.parser == 'generic':
            continue

        # Loop over all produced records
        metadata = group.metadata if isinstance(group.metadata, list) else [group.metadata]
        # Validate metadata and tweak into final MDF feedstock format
        # Will fail if any entry fails validation - no invalid entries can be allowed
        # TODO list:
        #   - How should validation failures (which stop processing) be communicated?
        #   - How should the feedstock be output? (Currently yield-ed, could be written to file)
        #   - (Future) Should feedstock be sent to Search directly here?
        #   - import Validator (where should it live? Toolbox?)
        #   - schema_path: MDF schema location, also makes updates easy
        #   - dataset_metadata: Metadata for dataset entry, will be passed in, no changes needed
        #   - validation_params: Params for validation, will be passed in, no changes needed

        # Probably need source_id in later revision
        source_id = dataset_metadata.get("mdf", {}).get("source_id", "unknown")

        vald = Validator(schema_path=schema_path)
        # Dataset validation
        ds_res = vald.start_dataset(dataset_metadata, validation_params)
        if not ds_res["success"]:
            raise ValueError(ds_res["error"])
        # Record validation
        for record in metadata:
            rc_res = vald.add_record(record)
            if not rc_res["success"]:
                raise ValueError(rc_res["error"])
        # Output feedstock (currently yielding)
        yield from vald.get_finished_dataset()
        '''
        # Validate records, but do not halt execution if they fail
        for record in metadata:
            # TODO (jgaff): Add in the record tweaking
            try:
                if validate_records:
                    validate_against_mdf_schemas(record)
                yield record
            except SchemaError:
                logger.warning(f'{group.group} failed validation. Parsers: {group.parser}')
        '''
