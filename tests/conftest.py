import logging
import pytest
import time
import sys
from pathlib import Path

from heofon.framework import utils, utils_file

logger = logging.getLogger(__name__)
# setting up the log file filenames
TESTRUN_LOGFILE_NAME = 'runlog.txt'
TESTCASE_LOGFILE_NAME = 'testlog.txt'
# hacky global counter for iterating over collected
# tests in pytest_runtest_setup()
COUNT = 1


def update_namespace(data: dict, verbose: bool = False):
    """
        Supporting method to simplify the addition of data into this
        framework's hacky namespace solution, which is just the addition
        of a dictionary as a property on the pytest instance triggered by
        this test run invocation.

        Any change to this dict is global and will have side effects.

        :param data: dict of items to add to the namespace
        :param verbose: bool, whether to output additional logging
        :return: None
    """
    try:
        pytest.custom_namespace
    except AttributeError:
        pytest.custom_namespace = {}
        if verbose:
            logger.info(f"\nnamespace doesn't exist, so creating it")

    for k, v in data.items():
        pytest.custom_namespace[k] = v
        if verbose:
            logger.info(f"\nadded namespace '{k}': '{v}'")

def pytest_addoption(parser):
    """
        Define command line options and arguments.

        :param parser: Pytest parser object
        :return: None
    """
    parser.addoption('--tier',
                     action='store',
                     dest='tier',
                     choices=['qa', 'stage', 'prod'],
                     default='stage',
                     help='Specify the tier: "qa", "stage", "prod".')

    if '--help' in sys.argv:
        # If pytest is invoked with the "help" option, we don't want to
        # generate the HTML results report because that will error out.
        # Don't create any output folders or logs.
        pass
    else:
        initialize_logging()
    logger.info(f"sys.argv: {sys.argv}")

# #########################################
# framework fixtures ######################
# #########################################
# 0.1
def initialize_logging():
    """
        Create the test framework's namespace in the pytest object,
        create the testrun's output folder, and start logging.

        :return: None
    """
    namespace_data = {}

    # set timestamp for the start of this test run;
    # this is used globally for this run
    timestamp = time.strftime('%y%m%d-%H%M%S')
    namespace_data['timestamp'] = timestamp

    # create the output folder for this test run
    welkin_folder, testrun_folder = utils_file.create_test_output_folder(timestamp)

    # save the welkin folder as a global config
    namespace_data['welkin_folder'] = str(welkin_folder)

    # save the output folder as a global config
    namespace_data['testrun_output_path_object'] = testrun_folder
    namespace_data['testrun_output_path'] = str(testrun_folder)

    path_to_logfile = str(testrun_folder / TESTRUN_LOGFILE_NAME)
    namespace_data['testrun_root_log'] = path_to_logfile

    # start logging; nothing that happens before this gets logged!
    log_kwargs = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(name)s::%(funcName)s() [%(levelname)s] %(message)s'
            },
        },
        'handlers': {
            'default': {
                'class': 'logging.FileHandler',
                'filename': path_to_logfile,
                'mode': 'a',
                'formatter': 'detailed'
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': False
            },
        }
    }
    set_logging_config(log_kwargs)

    # update our hacky namespace
    update_namespace(namespace_data, verbose=True)
    logger.info(f"\nnamespace:\n{utils.plog(pytest.custom_namespace)}")

# 0.2
def set_logging_config(kwargs):
    """
        Configure and start the framework logging.

        :param output_path: Path object for path to testrun output folder
        :return filename: Path object for path to log file
    """
    import logging.config
    # start logging
    logging.config.dictConfig(kwargs)
    filename = kwargs['handlers']['default']['filename']
    logger.info(f"created log file at '{filename}'.")
    return filename

