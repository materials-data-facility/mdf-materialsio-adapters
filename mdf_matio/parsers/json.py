from materials_io.base import BaseSingleFileParser
from typing import List
import json


# TODO (wardlt): Move this to MatIO
class JSONParser(BaseSingleFileParser):
    """Parses both JSON and line-delimited JSON files"""

    def _parse_file(self, path: str, context=None):
        try:
            with open(path) as fp:
                content = json.load(fp)
            return {'line-delimited': False, 'content': content}
        except json.decoder.JSONDecodeError as e:
            if not str(e).startswith('Extra data: line 2 column 1'):
                raise e

        # The file could be a line-delimited JSON file
        with open(path) as fp:
            content = [json.loads(line) for line in fp]
        return {'line-delimited': True, 'content': content}

    def implementors(self) -> List[str]:
        return ['Logan Ward']

    def version(self) -> str:
        return '0.0.1'
