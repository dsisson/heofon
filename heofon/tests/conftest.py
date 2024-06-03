import logging
import pytest
import time
import sys
from pathlib import Path

from heofon.framework import utils, utils_file

logger = logging.getLogger(__name__)

# setting up the log file filenames
FRAMEWORK = 'heofon'
TESTRUN_LOGFILE_NAME = 'runlog.txt'
TESTRUN_HTML_REPORT = 'report.html'
TESTCASE_LOGFILE_NAME = 'testlog.txt'
TESTCASE_PLAYWRIGHT_TRACING = 'trace.zip'

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
            logger.info('\nnamespace doesn\'t exist, so creating it')

    for key, value in data.items():
        # sometimes we feed in a value that's a dict, so handle nesting
        if isinstance(value, dict):
            for k, v in data[key].items():
                # update the hacky namespace object
                pytest.custom_namespace[key] = {k: value}
                if verbose:
                    logger.info(f"\nadded namespace '{k}': '{v}'")
        # update the hacky namespace object
        pytest.custom_namespace[key] = value
        if verbose:
            logger.info(f"\nadded namespace '{key}': '{value}'")


def pytest_addoption(parser):
    """
        Define command line options and arguments.

        Options here should be synced with the list of important options
        in pytest_configure(), so that get written to the hacky custom
        namespace.


        :param parser: Pytest parser object
        :return: None
    """
    parser.addoption('--tier',
                     action='store',
                     dest='tier',
                     choices=['qa', 'stage', 'prod'],
                     default='stage',
                     help='Specify the tier: "qa", "stage", "prod".')

    parser.addoption('--browser',
                     action='store',
                     dest='browser',
                     choices=['chromium', 'headless_chromium'],
                     default='chromium',
                     help='Specify the browser to use: "chromium", "headless_chromium".')

    parser.addoption('--tracing',
                     action='store',
                     dest='playwright_tracing',
                     choices=['on', 'off'],
                     default='off',
                     help='Specify whether to trace Playwright.')

    # if '--help' in sys.argv:
    #     # If pytest is invoked with the "help" option, we don't want to
    #     # generate the HTML results report because that will error out.
    #     # Don't create any output folders or logs.
    #     pass
    # else:
    #     initialize_logging()
    # logger.info(f"\nsys.argv: {sys.argv}")


# 1.0
def pytest_configure(config):
    """
        This pytest hook happens BEFORE test collection.

        1. Here we are calling initialize_logging(), which:
            + triggers the creation of output folders
            + enables logging
            + dynamically re-writes the output path used by the
              pytest-html reports plugin

            This requires that pytest.ini includes the following line so
            that there is a htmlpath attribute to modify:
                addopts = --html=output/report.html

        2. extracting important options and adding them to the
          custom namespace

        :param config: pytest Config object
        :return: None
    """
    initialize_logging(config)
    logger.info(f"sys.argv: {sys.argv}")

    # extract the values of the following sys.args options
    # and push them into the namespace
    namespace_data = {}
    opts = ['browser', 'tier']
    for item in opts:
        namespace_data[item] = config.getoption(item)

    # update our hacky namespace
    update_namespace(namespace_data, verbose=True)

    # based on the browser, also set a devtools flag that
    # will control the creation of some output folders; we need to
    # not add folders for unsupported browser info methods
    if config.getoption('browser') in ['chromium', 'headless_chromium']:
        update_namespace({'devtools_supported': True}, verbose=True)
    else:
        update_namespace({'devtools_supported': False}, verbose=True)



# 2.0
def pytest_sessionstart(session):
    """
        Set up the test run.

        Use configure_pytest_session() for any global test session and
        fixture logic.

        :param session: pytest request object (which is the context
                        of the calling text method)
        :return: None
    """
    logger.info(f"{'-' * 10}")
    # the following line outputs some interesting info for debugging test runs
    # logging.info(f"\nsession.__dict__:\n{utils.plog(session.__dict__)}")


# 3.0
def pytest_collection_modifyitems(items):
    """
        A pytest hook called after test collection used to modify or
        reorder test items.

        :param items: list, list of test item objects
        :return: None
    """
    logger.info("no actions taken.")


# 4.0
def pytest_collection_finish(session):
    """
        A pytest hook called after test collection has finished; we now know
        what tests will be run.

        :param session: pytest Session object
        :return: None
    """
    logger.info("no actions taken.")
    # logger.info(f"\nsession.__dict__:\n{utils.plog(session.__dict__)}")


# 5.0
def pytest_runtestloop(session):
    """
        A pytest hook called before the tests.
    """
    pass


# 6.0
def pytest_runtest_protocol(item, nextitem):
    """
        A pytest hook called before the tests.
    """
    pass


# 7.0
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    """
        A pytest hook run before the test is executed.

        We use this to:
        1. Create the folder to hold the logger output for the test.
           That folder is named with this syntax:
            <<number>>_<<test case name minus the "test">>_<<tier>>,
            which will look something like this:
                1_foo[some param]
                2_bar

        2. Trigger the creation of sub-folders for specific kinds of
           verbose output, depending on the types of applications being
           tested against.

           For example, if we are testing against a webapp,
           we create this kind of folder structure:
           - output (already exists)
               |- 210927-123456 (testrun folder, already exists)
                   |- 1_foo (test folder, created here)
                       |- accessibility (created here)
                       |- console (created here)
                       |- cookies (created here)
                       |- downloads (created here)
                       |- network (created here)
                       |- screenshots (created here)
                       |- webstorage (created here)

        3. Switch the logger from the root logger to the apps logger.
           This in effect moves the logging "firehose" from pointing at
           `TESTRUN_LOGFILE_NAME` to pointing at `TESTCASE_LOGFILE_NAME`.

        4. When the test case (test method) exits, the logger is
           re-pointed at the root logger.

        :param item: a test method.
        :return: None
    """
    logger.info(f"\n### Set up for test {item.name} ###")
    namespace_data = {}

    # extract the test method name, tweak it, and use it for
    # naming a folder in the testrun folder for the logging
    # of this current test
    try:
        test_name = item.__dict__['name']
    except KeyError:
        test_name = item.name
    # insert COUNT so that the folders sort by collection order
    short_name = f"{COUNT}_{test_name[5:]}"

    # extract the fixture names associated with this current test
    fixtures = []
    referenced_fixtures = item.__dict__['_fixtureinfo'].names_closure
    logger.info(f"\nreferenced_fixtures: {referenced_fixtures}")
    for this_fixture in referenced_fixtures:
        fixtures.append(this_fixture)
    # `COUNT` is used in the naming of the test output folder;
    # we need them to increment for each collected test
    globals()['COUNT'] += 1  # this is hacky because there is no iterator

    # create the output folder for this test case
    test_run_path = pytest.custom_namespace['testrun paths']['folder']
    testcase_folder_path = test_run_path / short_name
    create_test_output_subfolder(testcase_folder_path)

    # set up the appropriate sub-folders and
    # special log files for this test case
    set_up_testcase_reporting(testcase_folder_path, fixtures)

    # set up global namespace path-to-this-testcase value
    namespace_data['this_test'] = testcase_folder_path
    logger.warning("\n### Changing log output path to the test case path. ###\n\n")

    # redirect logging from the test run logger to the test case logger
    path_to_logfile = str(testcase_folder_path / TESTCASE_LOGFILE_NAME)
    logger.info(f"\n{'#' * 30}\n=====>> Testcase {item.name} "
                f"logged to {path_to_logfile}\n{'#' * 30}\n\n")
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
            'foo': {
                'class': 'logging.FileHandler',
                'filename': path_to_logfile,
                'mode': 'a',
                'formatter': 'detailed'
            }
        },
        'loggers': {
            '': {  # root
                'handlers': ['foo'],
                'level': 'INFO',
                'propagate': False
            },
            'heofon.apps': {
                'handlers': ['foo'],
                'level': 'INFO',
                'propagate': False
            },
        }
    }
    filename = set_logging_config(log_kwargs)  # noqa: F841

    # update our hacky namespace
    update_namespace(namespace_data, verbose=True)

    yield


# 8.0
def pytest_runtest_teardown(item, nextitem):
    """
        A pytest hook run at test teardown.

        :param item: a test method
        :param nextitem: a test method to be run next
        :return: None
    """
    logger.info(f"\n### Tear down for test {item.name} ###")
    path_to_logfile = pytest.custom_namespace['testrun paths']['logfile']

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
            '': {  # root
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': False
            },
        }
    }

    logger.info('\n### Closing test case logfile ###\n\n')
    filename = set_logging_config(log_kwargs)
    logger.info(f"\n### Reset logfile to {filename} ###\n\n\n")


# 9.0
def pytest_sessionfinish(session, exitstatus):
    """
        This hook is called after the whole test run finishes.
    """
    logger.info('No actions taken.')


# 10.0
def pytest_unconfigure(config):
    """
        This hook is the last pytest action, the final cleanup for
        the pytest run.

        This is where you would include logic for processing summary data.

        :param config: pytest config option
        :return: None
    """
    pass


@pytest.fixture(scope='session', autouse=True)
def configure_test_session(request):
    """
        Use configure_test_session() for any global test session and
        fixture logic.

        :param request: pytest request object (context of the
                        calling test method)
        :return: None
    """
    logger.info('--------------')
    logger.info('request.session.__dict__: %s' % request.session.__dict__)
    # logger.info('request.config.__dict__: %s' % request.config.__dict__)
    logger.info('sys.argv: %s' % sys.argv)
    logger.info('--------------')


# #########################################
# framework fixtures ######################
# #########################################
def set_logging_config(kwargs):
    """
        Configure and start the framework logging.

        :param kwargs: dict, logger config arguments
        :return filename: Path object for path to log file
    """
    import logging.config
    # start logging
    logging.config.dictConfig(kwargs)
    filename = kwargs['handlers']['default']['filename']
    logger.info(f"\ncreated log file at '{filename}'.")
    return filename

# 1.1
def initialize_logging(config):
    """
        Create the test framework's namespace in the pytest object,
        create the testrun's output folder, and start logging.

        :param config: pytest config object
        :return: None
    """
    namespace_data = {}

    # set timestamp for the start of this test run;
    # this is used globally for this run
    timestamp = time.strftime('%y%m%d-%H%M%S')
    namespace_data['timestamp'] = timestamp

    # update our hacky namespace
    update_namespace(namespace_data, verbose=True)

    # create the output folder for this test run
    framework_folder, testrun_folder = create_run_output_folder(timestamp)
    path_to_logfile = str(testrun_folder / TESTRUN_LOGFILE_NAME)

    # Change the path specified for the html test results report to include
    # the testrun's timestamp output folder. The report is generated by the
    # pytest-html report plugin, and is invoked by the command line argument
    # specified in pytest.ini: `--html=output/report.html`
    htmlreport_path = testrun_folder / TESTRUN_HTML_REPORT

    # Note: the pytest-html plugin relies on config.option.htmlpath.
    # So, even though the testrun-specific path is in the namespace,
    # we need to push that path back into the config object.
    html_path = str(htmlreport_path)
    config.option.htmlpath = html_path

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

    # create test run paths for namespace
    paths = {'testrun paths': {
                'folder': testrun_folder,
                'logfile': testrun_folder / TESTRUN_LOGFILE_NAME,
                'html report': htmlreport_path
    }}
    # update our hacky namespace
    logging.info('\n--> setting paths in namespace')
    update_namespace(paths, verbose=True)

    # set up test case namespacing
    update_namespace({'test cases': {}})

    logger.info(f"\nnamespace:\n{utils.plog(pytest.custom_namespace)}")

# 1.1.1
def create_run_output_folder(timestamped_name):
    """
        Every pytest invocation triggers a bunch of logging actions. During
        the pytest start up routines, logging is enabled and configured,
        including the creation of timestamped folders for the output, which is
        managed below.

        :param timestamped_name: str
        :return: PosixPath tuple, framework_root_path & testrun_path
    """
    # Get the absolute path to the current local directory.
    # This Path object will look like
    # PosixPath('/Users/<<name>>/dev/framework/framework')
    base_path = Path.cwd()

    # Get the path parts up to and including the first instance of `framework`.
    # We can't be certain that we are in the correct directory for running
    # framework, so focus on the first "framework" instance and build from there.
    parts = base_path.parts[:base_path.parts.index(FRAMEWORK) + 1]

    # generate the path to the output folder
    framework_root_path = Path('/').joinpath(*list(parts)) / FRAMEWORK
    output_path = Path('/').joinpath(*list(parts)) / f"{FRAMEWORK}/output"
    testrun_path = output_path / timestamped_name

    # create the output path if it doesn't exist
    if not output_path.exists():
        output_path.mkdir()

    # create the testrun folder (it won't already exist)
    if not testrun_path.exists():
        testrun_path.mkdir()

    return framework_root_path, testrun_path

# 7.1
def create_test_output_subfolder(path):
    """
        Create a folder `folder` at path `path`.

        :param path: Path path to the requested folder
        :return: None
    """
    if not path.exists():
        path.mkdir()
        logger.info(f"\nCreated sub-folder: {str(path)}")
    else:
        logger.info("\nSub-folder already exists.")

# 7.2
def set_up_testcase_reporting(testcase_folder, fixturenames):
    """
        For every specific test instance being run, create the various output
        folders needed for the different kinds of reporting and logging (beyond
        the core framework log). Depending on the "types" of apps being pulled
        into the test instance (via fixtures), different kinds of data will
        be logged or saved, so create the folders appropriate to this test's
        apps.

        :param testcase_folder: Path, path to the current test case's folder
        :param fixturenames: list, string fixture names for this testcase
        :return: None
    """
    if '--collect-only' in sys.argv:
        # if pytest is invoked with the --collect-only option, don't
        # create the testrun subfolders
        msg = "Subfolders NOT created because this testrun is collect-only."
        logger.info(msg)
    else:
        logger.info(f"\nfixturenames: {fixturenames}")
        logger.info(f"\ntestcase_folder: {testcase_folder}")
        testcase = testcase_folder.parts[-1]

        # #############################################
        # after you add an app fixture to conftest.py, you must add
        # the str name for that app fixture to the appropriate list
        # below. This allows you to use that app fixture as a test
        # method argument and have the appropriate folders and
        # logging in place.
        # #############################################
        integrations = ['auth']  # not used, but helps with context  # noqa: F841
        drivers = ['driver']
        web_apps = ['sweetshop']
        apis = []

        # set up config for folder requirements
        required_folders = {
            'api': ['requests'],
            'driver': ['driver'],  # browser/driver logging
            'web_app': ['cookies',  # cookies
                        'screenshots',  # screenshots from POM and tests, etc.
                        'accessibility',  # reports generated by POM for every page
                        'webstorage'  # local and session
                        ]
        }

        # only create folders and logs appropriate to the app fixtures
        is_api = len(set(fixturenames).intersection(apis))
        is_driver = len(set(fixturenames).intersection(drivers))
        is_webapp = len(set(fixturenames).intersection(web_apps))
        logger.info(f"\napp types: is_api {is_api}; is_webapp: {is_webapp}")

        # some folders are common to all
        folders_to_create = ['integrations', 'downloads']
        if is_api:
            folders_to_create.extend(required_folders['api'])
        if is_driver:
            folders_to_create.extend(required_folders['driver'])
        if is_webapp:
            folders_to_create.extend(required_folders['web_app'])
            if pytest.custom_namespace.get('devtools_supported'):
                # some capabilities are currently restricted to Chrome browsers
                folders_to_create.extend(['network', 'console', 'metrics'])

        # #############################################
        # For the current test case, create the relevant child folders
        # to which various logging and output will be written.
        # Note: This mechanism relies on side effects! Specifically,
        # various framework write methods pull paths from the custom
        # namespace, and those paths are overwritten here in
        # set_up_testcase_reporting(). This will be a problem
        # if we attempt to parallelize the execution of the
        # collected tests.
        # #############################################
        paths = {testcase: {}}  # set up individual test case namespace
        current_testcase = {'current test case': {'name': testcase}}
        for folder in folders_to_create:
            this_folder_path = testcase_folder / folder
            create_test_output_subfolder(this_folder_path)
            logger.info(f"\ncreated folder '{folder}': {this_folder_path}")

            # update local data model
            paths[testcase][f"{folder} folder"] = this_folder_path

        # manually *add* (not overwrite) this test case info to the namespace
        pytest.custom_namespace['test cases'].update(paths)

        # overwrite the namespace entry for 'current test case'
        current_testcase['current test case'].update(paths[testcase])
        update_namespace(current_testcase, verbose=True)

        logger.info(f"\nnamespace after test folder creation:"
                    f"\n{utils.plog(pytest.custom_namespace)}")





# # 0.2
# def set_logging_config(kwargs):
#     """
#         Configure and start the framework logging.
#
#         :param output_path: Path object for path to testrun output folder
#         :return filename: Path object for path to log file
#     """
#     import logging.config
#     # start logging
#     logging.config.dictConfig(kwargs)
#     filename = kwargs['handlers']['default']['filename']
#     logger.info(f"created log file at '{filename}'.")
#     return filename


# 1.1


def add_opts_to_namespace(config):
    """
        Add the CLI args from pytest_addoption() to the
        pytest.custom_namespace dict.

        New addopts have to be manually added to this list; however,
        they can still be access through request.config.option.<foo>.

        This pytest.custom_namespace dict is created in pytest_configure().

        :param config: pytest config option
        :return: None
    """
    namespace_data = {}
    opts = ['browser', 'tier']
    for item in opts:
        namespace_data[item] = config.getoption(item)

    # update our hacky namespace
    update_namespace(namespace_data, verbose=True)




# 1.3
def set_up_tier_globals(config):
    """
        The tier is specified at run time (the default is STAGE tier).
        Determine the tier-specific configuration settings and strings to use
        during testing against the specified tier.

        Of particular importance here are:
        + application models, critical for e2e testing; we need to know what
          apps are available for the current tier
        + user models, critical for e2e testing; we need to know the users
          for these apps
        + safe handling of the credentials for users
        + apps we will integrate with during the test run

        Note: this logic is in a method called by pytest_configure instead of
        in a test fixture because tests are collected *before* fixtures are
        parsed; this means that the globals set by the command line parsers
        don't get set until *after* the tests which call them are collected.

        The config object is introspected for the desired parameter value.

        The values set here are pushed into a pytest global environment
        variable called `custom_namespace`; this is available when you import
        pytest into a module. This namespace is now set in initialize_logging().

        Context example example:
        $ pytest tests --tier=stage

        Some general values can be accessed directly:
        >>> pytest.custom_namespace['tier']
        stage

        :param config: pytest config object
        :return: None
    """
    namespace_data = {}
    this_tier = config.option.tier
    namespace_data['tier'] = this_tier
    logger.info(f"this_tier: '{this_tier}'.")

    # update our hacky namespace
    update_namespace(namespace_data, verbose=True)

    return None


@pytest.fixture
def browser(request):
    """
        Determine the browser driver to use based on the `browser` parameter
        specified at the command line.

        The request object is introspected for the desired parameter value.

        For example:
        $ pytest tests --browser=chrome

        :param request: pytest request object
        :return: str, identifier for the appropriate browser driver
    """
    this_browser = request.config.option.browser
    logger.info('this_browser = %s' % this_browser)

    # # hack!
    # if not this_browser:
    #     this_browser = 'headless_chromium'

    return this_browser


# def browser_chromium():
#     """
#         Launch the local browser, which will block other activities
#         on the computer.
#     """
#     from selenium import webdriver
#     from selenium.webdriver.chrome.options import Options
#
#     chrome_options = Options()  # noqa: F841
#     # default_dir = {'download.default_directory': None#}
#     # chrome_options.add_experimental_option('prefs')
#
#     capabilities = base_chrome_capabilities()
#     # this_driver = webdriver.Chrome(options=chrome_options,
#     #                                desired_capabilities=capabilities)
#     this_driver = webdriver.Chrome(desired_capabilities=capabilities)
#     return this_driver
#
#
# def browser_chromium_headless():
#     """
#         This allows for full-page screenshots, as well as not blocking
#         use of the local computer.
#     """
#     from selenium import webdriver
#     from selenium.webdriver.chrome.options import Options
#
#     chrome_options = Options()
#     chrome_options.add_argument('--headless')
#     # default_dir = {'download.default_directory': None#}
#     # chrome_options.add_experimental_option('prefs')
#
#     capabilities = base_chrome_capabilities()
#     this_driver = webdriver.Chrome(options=chrome_options,
#                                    desired_capabilities=capabilities)
#
#     # logger.info(f"\nbrowser options:\n{chrome_options.__dict__}")
#     return this_driver


@pytest.fixture(scope="function")
def pwpage(request, browser):
    """
        Identify the appropriate browser driver to instantiate, and then
        instantiate a Playwright Page object for a single tab in that browser.
        (Note to be confused with anything from a page object model)

        This fixture is scoped to `function`, so it will launch and quit the driver
        for EACH calling test function.

        Call this fixture by passing the name as a parameter:
        def some_test(self, page):
            etc.

        :param request: pytest request object (context of the calling test method)
        :param browser: str, browser driver identifier
        :yield pwpage: playwright page instance
    """
    logger.info(f"\nRequested '{browser}' driver.")
    pwpage = None

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        if browser == 'chromium':
            this_browser = playwright.chromium.launch(headless=False)
        elif browser == 'headless_chromium':
            this_browser = playwright.chromium.launch(headless=True)
        else:
            msg = f"\nError: '{browser}' is not a valid selection."
            logger.error(msg)
            raise ValueError(msg)

        context = this_browser.new_context()

        if request.config.option.playwright_tracing == 'on':
            # To enable playwright tracing, we need to start it before
            # any test actions are taken.
            path_tracing = str(pytest.custom_namespace['this_test']) \
                           + TESTCASE_PLAYWRIGHT_TRACING
            context.tracing.start(screenshots=True)
            logger.info(f"\nGenerating tracing content.")


        # Create the Playwright Page instance, which is a single tab
        # in the browser. To disambiguate this while simultaneously
        # making it very confusing, we'll call this `pwpage`.
        pwpage = context.new_page()
        # logger.info(f"\npwpage.__dict__: {utils.plog(pwpage.__dict__)}")
        # logger.info(f"\ndir(pwpage): {utils.plog(dir(pwpage))}")

        yield pwpage

        if request.config.option.playwright_tracing == 'on':
            # To generate the trace file, we need to stop it after.
            context.tracing.stop(path=path_tracing)
            logger.info(f"\nSaving tracing output.")

        context.close()  # gracefully close and flush artifacts
        logger.info(f"\nClosing context.")
        this_browser.close()
        logger.info(f"\nQuitting browser.")


@pytest.fixture(scope='session')
def sweetshop(request):
    """
        This test fixture is a trigger for setting up authentication
        management for a generic web app.
        Note: not really, this is just an example to use for real apps
        that have actual users with real credentials in AWS.
    """
    pass
