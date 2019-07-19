from materials_io.utils import ParseResult
from typing import Iterable, List
from operator import itemgetter
from itertools import groupby
import os


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


def groupby_directory(parse_data: Iterable[ParseResult]) -> Iterable[List[ParseResult]]:
    """Group parsing results by directory
    
    Args:
        parse_data ([ParseResult])): Iterable of data coming from the parser
    Yields:
        ([ParseResult]) after grouping based on directory, sorted by directory name
    """

    # Sort by the directory name, so that `groupby` see consecutive keys of the
    # TODO (wardlt): Potentially memory intensive for larger filesystems. Consider memmap/spark
    sorted_data = sorted(zip(map(_get_directory, parse_data), parse_data), key=itemgetter(0))
    for gid, group in groupby(sorted_data, key=itemgetter(0)):
        yield [x[1] for x in group]  # Remove directory name
