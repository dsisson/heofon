import logging
import json
import pathlib
import pprint
from copy import deepcopy

logger = logging.getLogger(__name__)


def create_test_output_folder(timestamped_name):
    """
        Every pytest invocation triggers a bunch of logging actions. During
        the pytest start up routines, logging is enabled and configured,
        including the creation of timestamped folders for the output, which is
        managed below.

        :param timestamped_name:
        :return: tuple, heofon_root_path & testrun_path
    """
    # Get the absolute path to the current local directory.
    # This Path object will look like
    # PosixPath('/Users/<<name>>/devc/heofon/heofon')
    base_path = pathlib.Path.cwd()

    # Get the path parts up to and including the first instance of `heofon`.
    # We can't be certain that we are in the correct directory for running
    # heofon, so focus on the first "heofon" instance and build from there.
    parts = base_path.parts[:base_path.parts.index('heofon') + 1]

    # generate the path to the output folder
    heofon_root_path = pathlib.Path('/').joinpath(*list(parts)) / 'heofon'
    output_path = pathlib.Path('/').joinpath(*list(parts)) / 'heofon/output'
    testrun_path = output_path / timestamped_name

    # create the output path if it doesn't exist
    if not output_path.exists():
        output_path.mkdir()

    # create the testrun folder (it won't already exist)
    if not testrun_path.exists():
        testrun_path.mkdir()

    return heofon_root_path, testrun_path


def create_test_output_subfolder(path, folder):
    """
        Create a folder `folder` at path `path`.

        :param path:
        :param folder:
        :return:
    """
    # generate the path to the output subfolder
    folder_path = path / folder
    if not folder_path.exists():
        folder_path.mkdir()
    logger.info(f"Created sub-folder: {str(folder)}")
    return folder_path
