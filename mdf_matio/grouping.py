from materials_io.utils.interface import ParseResult
from typing import Iterable, List
from operator import itemgetter
from itertools import groupby
import os


# TODO (wardlt): Grouping requires entire parsed data, memory intensive for larger filesystems
#  Potential Plan: Write to a temporary database with SQLite and sqlalchemy
#    Pros: No external database to manage, can handle temporary file with context manager
#    Cons: Disk access slow (avoidable?), would recreate database on each step


def _get_directory(group: ParseResult) -> str:
    """Get the directory for a group of files

    Args:
        group (ParseResult): Result of parsing
    Returns:
        (str) Output string
    """
    files = group[0]
    if len(files) == 1:
        return os.path.dirname(files[0])
    else:
        return os.path.commonpath(files)


def groupby_directory(records: Iterable[ParseResult]) -> Iterable[List[ParseResult]]:
    """Group parsing results by directory

    Args:
        records ([ParseResult])): Iterable of data coming from the parser
    Yields:
        ([ParseResult]) after grouping based on directory, sorted by directory name
    """

    # Sort by the directory name, so that `groupby` see consecutive keys of the
    sorted_data = sorted(zip(map(_get_directory, records), records), key=itemgetter(0))
    for gid, group in groupby(sorted_data, key=itemgetter(0)):
        yield [x[1] for x in group]  # Remove directory name


def groupby_file(records: Iterable[ParseResult], max_passes=-1) -> Iterable[List[ParseResult]]:
    """Group together parsing results that reference the same files

    Files are grouped in an iterative procedure, which can be costly.
    The number of grouping iterations can be truncated for speed.

    Args:
        records (ParseResult): Results of parsing
        max_passes (int): Maximum number of grouping passes
        # TODO: Consider a timeout-based solution
    Yields:
        ([ParseResult]) Lists of parsed records that contain the same files
    """

    # Initialize each file into its own group
    current_groups = [(set(x[0]), [x]) for x in records]

    # Perform grouping passes
    grouping_pass = 0
    while True:
        grouping_pass += 1
        matched_groups = []  # Groups that are matched and may have to be grouped again

        while len(current_groups) > 0:
            # Pick a record to attempt to match other records
            to_match = current_groups.pop()
            matched_ids = set()

            # See if it matches any already-matched group
            my_files = to_match[0]
            matched = False
            for files, records in matched_groups:
                if not my_files.isdisjoint(files):
                    matched = True
                    files.update(my_files)
                    records.extend(to_match[1])
                    break
            if matched:
                continue

            # Loop over all other records, find those that have similar
            for i, record in enumerate(current_groups):
                if not record[0].isdisjoint(my_files):
                    matched_ids.add(i)

            if len(matched_ids) == 0:
                # Take it out of circulation as there will be no matches on later passes
                yield to_match[1]  # Return the group
            else:
                # Get the matched entries, and delete them from current groups
                my_matched_groups = [e for i, e in enumerate(current_groups) if i in matched_ids]
                current_groups = [e for i, e in enumerate(current_groups) if i not in matched_ids]

                # Merge the matched groups
                my_records = to_match[1]
                for group in my_matched_groups:
                    my_files.update(group[0])
                    my_records.extend(group[1])

                # Add new groups to the "must be grouped again list"
                matched_groups.append((my_files, my_records))

        # Check if we are done
        if grouping_pass == max_passes:
            # Return the current matched groups
            for group in matched_groups:
                yield group[1]
        elif len(matched_groups) == 0:
            return  # Nothing left to group
        else:
            # Prepare to group again
            current_groups = matched_groups
