import logging
import json
import pathlib
import pprint
from copy import deepcopy

logger = logging.getLogger(__name__)

def plog(content):
    """
        Format json content for pretty printing to the logger.

        If `content` is not json, try to identify what it is and then try
        to format it appropriately.

        :param content: assumed to be json
        :return formatted_content:

        The typical usage will look like this:
        >>> from heofon.framework import utils
        >>> my_json = res.json()
        >>> logger.info(utils.plog.my_json)
    """
    # set a default pass-through value of an empty string in order
    # to catch None, because if a calling method tries to write()
    # the output of plog() will error out in the attempt.
    formatted_content = ''
    try:
        formatted_content = json.dumps(content, indent=4, sort_keys=True)
    except (ValueError, TypeError):
        # oops, this wasn't actually json

        # try pretty-printing based on the guessed content type
        from requests.structures import CaseInsensitiveDict
        import deepdiff

        if isinstance(content, dict):
            formatted_content = pprint.pformat(content, indent=1, width=100)
        elif isinstance(content, list):
            formatted_content = pprint.pformat(content, indent=1, width=100)
        elif isinstance(content, CaseInsensitiveDict):
            formatted_content = pprint.pformat(dict(content), indent=1, width=100)
        elif isinstance(content, deepdiff.diff.DeepDiff):
            formatted_content = pprint.pformat(content, indent=1, width=160, depth=4)
        elif isinstance(content, bytes):
            # is this XML?
            if content[:5] == b'<?xml':
                import xml.dom.minidom
                xml = xml.dom.minidom.parseString(content)
                formatted_content = str(xml.toprettyxml())
            else:
                # no, this is some other kind of byte string
                msg = f"Unable to pretty print the content that starts with {content[:20]}"
                logger.warning(msg)
                pass

    return formatted_content

