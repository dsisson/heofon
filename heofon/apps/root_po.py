import logging
import importlib
import time
import pytest
import pdb
# from axe_selenium_python import Axe
#
from heofon.framework.exceptions import PageUnloadException
from heofon.framework.exceptions import PageLoadException
# from heofon.framework.exceptions import PageIdentityException
# from heofon.framework.exceptions import ControlInteractionException
#
# from heofon.framework import checks
from heofon.framework import utils, utils_file, utils_playwright

logger = logging.getLogger(__name__)


class RootPageObject(object):

    def resolve_po(self, po_id, cross_auth_boundary=False, **opts):
        """
            Using the string id of the pageobject for the desired page,
            identify the pageobject's class and instantiate it.

            The importing of the modules and classes has to be done
            dynamically -- and in this method -- in order to avoid
            recursive import loops on start up.

            This uses the data model in the PO's wrapper routings.py for
            a mapping between the page/PO name with the module and
            the object name for that PO.

            What makes this method a little more complicated is the fact
            that the PO instantiation has to be aware of crossing the
            boundary between noauth and auth pages, because those PO
            modules live in separate folders. This boundary is in play
            when logging in from a noauth page (at which point the user
            should be known to the system for subsequent pages), or when
            logging out from an auth page (at which point the user should
            be forgotten by the system).

            :param po_id: str, key for the page object in the POM data model
            :param cross_auth_boundary: bool, true to trigger a switch between
                                        auth and noath routing, or vice versa
            :param opts: dict, pass-through parameters for the PO's __init__()
            :return: page object for the target page
        """
        # import the routings module for the appropriate wrapper
        # the path (minus the file name) lives in this wrapper's BasePageObject
        import_path_to_routings = self.routings_path + 'routings'
        logger.info(f"\nPath to routings module for this wrapper:\n{import_path_to_routings}")
        routings = importlib.import_module(import_path_to_routings)

        routing_map = None
        root_path_to_module = None

        # load the correct mapping dict from the wrapper's routings.py file,
        # based on whether the next PO will be noauth or auth
        if self.page_auth_mode == 'noauth':
            if cross_auth_boundary:
                # handle the auth boundary crossing here if needed
                # need to load the auth map
                routing_map = routings.auth_pageobjects
                root_path_to_module = routings.AUTH_PATH
                pass
            else:
                # load the noauth map
                routing_map = routings.noauth_pageobjects
                root_path_to_module = routings.NOAUTH_PATH
        elif self.page_auth_mode == 'auth':
            if cross_auth_boundary:
                # handle the auth boundary crossing here if needed
                # need to load the noauth map
                routing_map = routings.noauth_pageobjects
                root_path_to_module = routings.NOAUTH_PATH
            else:
                # load the auth map
                routing_map = routings.auth_pageobjects
                root_path_to_module = routings.AUTH_PATH
        else:
            msg = f"page_auth_mode can only be 'noauth' or 'auth'; " \
                  f"'{self.page_auth_mode}' is not valid."
            logger.error(msg)
            raise ValueError(msg)

        # get the str module name for the new PO
        page_object_data = routing_map[po_id]

        # assemble the str dot-notation path for the module
        module_path = root_path_to_module + page_object_data['module']

        # dynamically import the module `module_path`
        logger.info(f"\nPath to page object: {module_path} --> '{po_id}'.")
        path_to_module = importlib.import_module(module_path)

        # dynamically translate from the str name of the PO
        # to the PO's class
        pageobject_class = getattr(path_to_module, page_object_data['object'])

        # instantiate a class instance for the PageObject.
        # Note: at this point, in this method, `self` refers to the old PO
        unvalidated_pageobject = pageobject_class(self.pwpage)
        return unvalidated_pageobject

    def load_po(self, po_id, cross_auth_boundary=False, **opts):
        """
            Load the page object for the page that has been navigated to,
            and return it.

            The philosophy behind this method is that there are three layers
            of abstraction to driving a browser programmatically from test code:
                1. our test code interacts with the browser and triggers browser
                events.
                2. the browser acts on these interactions and triggers, changing
                its state.
                3. we abstract and manage expected browser context with our page
                object model. Our test code operates in this abstraction layer.

            Every time the browser changes its state, we must update our
            expectations about the browser state. To do this, we must force
            reloads of the page object model when ever we take a state-changing
            interaction. We do this by loading and returning an updated page
            object on taking test actions.

            This method load_pageobject() is responsible for managing the model's
            state transitions, but performing checks that the current browser page
            is the one we expect to be on.

            :param po_id: str, key for the page object in the POM data model
            :param cross_auth_boundary: bool, true to trigger a switch between
                                        auth and noath routing, or vice versa
            :param opts: dict, pass-through parameters for the PO's __init__()
            :return: page object for the target page
        """
        # get the previous page's name; remember that the browser has changed
        # state and we are trying to catch the page object up to the browser
        last_page = self.name  # noqa: F841

        # get the pageobject for the expected new page
        # at this point, we do NOT know if the browser loaded the page correctly!
        new_pageobject_instance = self.resolve_po(
            po_id, cross_auth_boundary=False, **opts)

        # TODO: actually verify page load
        event = f"loaded page '{po_id}'"

        # perform a series of data collection and file-writes for the NEW page
        # which has NOT YET been instantiated as a page object

        # write the cookies FOR THE NEW PAGE to a file
        new_pageobject_instance.save_cookies(filename=event)

        # write browser console logs FOR THE NEW PAGE to files
        new_pageobject_instance.save_browser_logs(filename=event)

        # write webstorage FOR THE NEW PAGE to files
        new_pageobject_instance.save_webstorage(event=event, set_this_event=False)

        # with this return, the page object model is now in sync
        # with the browser
        return new_pageobject_instance

    # #######################################
    # browser data methods
    # #######################################
    def save_cookies(self, filename=''):
        """
            Get the current page's cookies and save to a file.

            The filename can be specified by the calling code, but the
            expectation is that this is either:
            1. an event string, because the trigger for saving these cookies
               could be a page object load or reload
            2. the default of the page object's name

            :param filename: str filename for the log file;
                             defaults to PO name
            :return: None
        """
        fname = filename if filename else self.name
        # get the cookies from the driver and save to the PO
        self.cookies = self.pwpage.context.cookies()
        # and also write them to a file
        utils_file.write_cookies_to_file(self.cookies, self.url, fname=fname)

    def save_webstorage(self, event, set_this_event=True):
        """
            Get the localStorage and sessionStorage for the current page (if
            available), and then write them to logfiles.

            Note: because the storage is closely tied to app state (if this
            is a React app), use the event as the base for the file name!

            Note: sometimes we don't want to call set_event() for the event
            `event`.

            :param event: str, name of the event
            :param set_this_event: bool, true to call set_event for this event
            :return: None
        """
        data = self.get_webstorage()
        if set_this_event:
            self.set_event(event)
        utils_file.write_webstorage_to_files(data,
                                             current_url=self.url,
                                             pageobject_name=self.name,
                                             event=event)

    def get_webstorage(self):
        """
            Wrapper to call methods to get browser local and session storage
            for the current page and convert to python dicts.

            :return: tuple of local storage dict and session storage dict
        """
        local = utils_playwright.get_local_storage(self.pwpage)
        session = utils_playwright.get_session_storage(self.pwpage)
        return local, session

    def save_browser_logs(self, filename=''):
        """
            Grab the Chrome driver console and network logs and write them
            to files.

            :param filename: str filename for the log file;
                             defaults to PO name
            :return:
        """
        # set the cleaned file name
        fname = filename if filename else self.name

        console_log = utils_playwright.get_console_log(self.pwpage)

        # write the scan logs to /console
        utils_file.write_console_log_to_file(log=console_log,
                                             url=self.url, fname=fname)

    # #######################################
    # page object transition methods
    # #######################################
    def _click_and_load_new_page(self, element, name, po_selector,
                                 change_url=True, **actions):
        """
            Perform a click action on an element, then return a new page object
            for the page that the browser has loaded.

            The `change_url` controls the expectation of the url changing
            after this click action. This is a little bit hacky.

            Log the timestamp for the click action and save to timings.txt

            Note: Single page apps built with frameworks like React could
            make the transition between pages a little tougher to model if
            they don't change the urls for logical pages.

            :param element: webelement (for link, button, etc.)
            :param name: str, identifier for element
            :param po_selector: str, name of the target PO
            :param change_url: bool, True if url should change
            :param actions: dict, could contain key/value pairs for
                                  'pre_action' and 'post_action'
            :return next_page: page object for the next page
        """
        pwpage = self.pwpage  # minor disambiguation

        # perform the click action
        # wait = WebDriverWait(driver, 20)
        if change_url:
            old_url = self.url
            logger.info(f"Old url: {old_url}")

            # some methods will insert a 'target url' key into the `actions`
            # payload, which means that a redirect is expected. If this key
            # is present, then wait for the target url to be present.
            target_url = actions.get('target url')
            logger.info(f"target url: {target_url}")
            self._click_element(element, name, **actions)

        #     if target_url:
        #         # expect a redirect
        #         try:
        #             self._click_element(element, name, **actions)
        #             wait.until(EC.url_to_be(target_url))
        #             new_url = driver.current_url
        #             logger.info(f"New url: {new_url}")
        #         except TimeoutException:
        #             msg = f"URL did not change as required from '{old_url} to {target_url}'."
        #             logger.error(msg)
        #             logger.info(f"actual URL: {driver.current_url}")
        #             # self.save_screenshot(f"failed while leave {self.name}")
        #             # self.save_browser_logs()
        #             # self.save_webstorage(event=msg)
        #             raise PageUnloadException(msg)
        #
        #     else:
        #         try:
        #             self._click_element(element, name, **actions)
        #             wait.until(EC.url_changes(old_url))
        #             new_url = driver.current_url
        #             logger.info(f"New url: {new_url}")
        #         except TimeoutException:
        #             msg = f"URL did not change as required from '{old_url}'."
        #             logger.error(msg)
        #             # self.save_screenshot(f"failed to leave {self.name}")
        #             # self.save_browser_logs()
        #             # self.save_webstorage(event=msg)
        #             raise PageUnloadException(msg)
        # else:
        #     self._click_element(element, name, **actions)

        # load and return the PO for the next page
        logger.info(f"\nLoading page object for '{po_selector}'.")
        if actions.get('pass through to PO'):
            # In some special cases a PO's __init__() might require
            # additional args
            next_page = self.load_po(po_selector, **actions)
        else:
            next_page = self.load_po(po_selector)
        return next_page

    def set_event(self, event_name, page_name=None):
        """
            Add an event to the current page object's properties.

            An `event` is an interaction with the browser and/or site that
            MAY cause a change in page state by triggering Javascript logic
            to manipulate the DOM.

            Optionally set the name of the current page as `page_name`.
            Typically, it's ok to just use the current page objects name property

            For now, we just log the fact of the event.

            :param event_name: str, name of the event
            :param page_name: str, name of page where the event occurred
            :return: None
        """
        this_event = {
            '_timestamp': time.time(),
            'event': event_name,
            'on page': page_name if page_name else self.name
        }
        logger.info(f"\nbrowser interaction event:\n{utils.plog(this_event)}")

    # #######################################
    # interaction event wrappers
    # #######################################
    def _click_element(self, element, name, msg=None, **actions):
        """
            Wrap the actual clicking of an element. This allows for the
            insertion of additional check points and error checking and
            handling.

            :param element: webdriver element
            :param name: str, identifier for element
            :param msg: str, optional specified event msg
            :return: None
        """
        event = f"clicked element '{name}'"
        element.click()
        self.set_event(msg if msg else event)
        # self.save_screenshot(f"after click {name}")
        # if actions.get('actions'):
        #     if actions['actions'].get('unhover'):
        #         self._unhover()
        #         x, y = actions['actions']['unhover']
        #         self._unhover(x=x, y=y)
        #         # self.save_screenshot(f"after unhover {name}")

    def save_screenshot(self, filename=''):
        """
            Wrap the PW Page's screenshot functionality to generate and save
            the screenshot.

            There's alot not yet supported;
            see https://playwright.dev/python/docs/api/class-page#page-screenshot
            for more details.

            :param filename: str filename for the screenshot (not including
                             the path)
            :return: None
        """
        # the current test's screenshot folder
        logger.info(f"\namespace:\n{utils.plog(pytest.custom_namespace)}")
        path = pytest.custom_namespace['current test case']['screenshots folder']

        # set the filename
        fname = filename if filename else self.name
        clean_name = utils_file.path_proof_name(fname + '.png')
        logger.info(f"\nGenerating screenshot for '{clean_name}'.")

        path_to_screenshot = path / clean_name
        logger.info(f"\nfull path: '{path_to_screenshot}'.")
        # use the PW Page object that's attached to our pageobject to screenshot
        self.pwpage.screenshot(path=path_to_screenshot, full_page=True)
