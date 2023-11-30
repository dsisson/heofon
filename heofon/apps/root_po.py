import logging
import importlib
import time
import pytest
import pdb
# from axe_selenium_python import Axe
#
from heofon.framework.exceptions import PageUnloadException
from heofon.framework.exceptions import PageLoadException
# from welkin.framework.exceptions import PageIdentityException
# from welkin.framework.exceptions import ControlInteractionException
#
# from welkin.framework import checks
from heofon.framework import utils, utils_file

logger = logging.getLogger(__name__)


class RootPageObject(object):

    def load_po(self, po_id, cross_auth_boundary=False):
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
        new_pageobject_instance = pageobject_class(self.pwpage)

        return new_pageobject_instance

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
