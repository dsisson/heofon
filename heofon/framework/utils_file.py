import logging
import json
import pathlib
import time
import pytest

from heofon.framework import utils

logger = logging.getLogger(__name__)


def path_proof_name(name):
    """
        Some characters used in naming page objects or screenshots are
        not safe for paths, so clean up those names.

        :param name: str, name to be used for a file
        :return clean_name: transformed and presumed safe name
    """
    if not name:
        clean_name = 'None'
    else:
        # the most common problems are a slash
        clean_name = name.replace('/', '-')
        # and spaces
        clean_name = clean_name.replace(' ', '_')
        # and quotes
        clean_name = clean_name.replace('"', '')
        clean_name = clean_name.replace("'", '')

    return clean_name


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
        :return folder_path: Path object path to this folder
    """
    # generate the path to the output subfolder
    folder_path = path / folder
    if not folder_path.exists():
        folder_path.mkdir()
    logger.info(f"Created sub-folder: {str(folder)}")
    return folder_path


def write_cookies_to_file(cookies, url, fname=''):
    """
        Save cookies as json to a file.

        :param cookies: list of dicts
        :param url: str, url for the current page
        :param fname: str, first part of filename, will be appended with
                           timestamp; defaults to empty string
        :return: None
    """
    filename = f"{time.strftime('%H%M%S')}_{path_proof_name(fname)}.txt"
    path = pytest.custom_namespace['current test case']['cookies folder'] / filename
    with open(path, 'w') as f:
        f.write(f"{url}\n")  # write the url as the first line
        f.write(utils.plog(cookies))
    logger.info(f"\nSaved cookies: {path}.")


def write_webstorage_to_files(data, current_url, pageobject_name,
                              event):
    """
        Write the localStorage and sessionStorage content to a log file.

        Note 1: the data is a cleaned up representation of the json data;
                however, the file is NOT json.
        Note 2: the timing of when the content is written may be significant.

        :param data: list, localStorage dict and sessionStorage dict
        :param current_url: str, url for the current page
        :param pageobject_name: str, name for the current pageobject
        :param event: str, descriptor for an interaction with the React app
        :return: None
    """
    base_filename = f"{time.strftime('%H%M%S')}_" \
                    f"{path_proof_name(event)}"
    path = pytest.custom_namespace['current test case']['webstorage folder'] / base_filename

    # unpack the data
    local_storage, session_storage = data

    # write the local storage
    local_filename = f"{path}_local.json"
    _write_local_to_file(local_storage, event, pageobject_name,
                         current_url, local_filename)

    # write the session storage
    session_filename = f"{path}_session.json"
    _write_session_to_file(session_storage, event, pageobject_name,
                           current_url, session_filename)

def _write_local_to_file(data, event, pageobject_name, source_url, output_url):
    """
        Write the local storage to a json file in the webstorage folder.

        Note: several heofon key-value pairs will be inserted into that data.

        :param data: dict of local storage log pulled from the browser
        :param event: str, descriptor for an interaction with the React app
        :param pageobject_name: str, name of pageobject
        :param source_url: str, full url of the page that generated the logs
        :param output_url: str, full local path for the output file
        :return: None
    """
    # add key/value for the page url
    data.update({'_storage type': 'local'})
    data.update({'_page': source_url})
    data.update({'_page object name': pageobject_name})
    data.update({'_precipitating event': event})

    with open(output_url, 'a') as f:
        f.write(utils.plog(data))
    logger.info(f"Saved local storage log: {output_url}.")


def _write_session_to_file(data, event, pageobject_name, source_url, output_url):
    """
        Write the session storage to a json file in the webstorage folder.

        Note: several heofon key-value pairs will be inserted into that data.

        :param data: dict of session storage log pulled from the browser
        :param event: str, descriptor for an interaction with the React app
        :param pageobject_name: str, name of pageobject
        :param source_url: str, full url of the page that generated the logs
        :param output_url: str, full local path for the output file
        :return: None
    """
    # add key/value for the page url
    data.update({'_storage type': 'session'})
    data.update({'_page': source_url})
    data.update({'_page object name': pageobject_name})
    data.update({'_precipitating event': event})

    with open(output_url, 'a') as f:
        f.write(utils.plog(data))
    logger.info(f"Saved session storage log: {output_url}.")


def write_console_log_to_file(log, url, fname=''):
    """
        Write the chrome devtools console logs to a file.

        :param log: dict
        :param url: str, url for the current page
        :param fname: str, first part of filename, will be appended with
                           timestamp; defaults to empty string
        :return: None
    """
    filename = f"{time.strftime('%H%M%S')}_{path_proof_name(fname)}.json"
    path = pytest.custom_namespace['current test case']['console folder'] / filename

    log.insert(0, f"_page: {url}")
    logger.info(f"\nconsole logs: {utils.plog(log)}.")

    # # add key/value for the page url
    # log.update({'_page': url})

    with open(path, 'a') as f:
        f.write(utils.plog(log))
    logger.info(f"\nSaved console logs (and bad headers): {path}.")
