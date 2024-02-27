import pytest
import logging
import re
from playwright.sync_api import Page, expect

from heofon.framework import utils
from heofon.apps.sweetshop.noauth import pages as pom

logger = logging.getLogger(__name__)


class SweetshopTests:

    def test_linear_navigation(self, pwpage, sweetshop):
        """
            Simple navigation flow.

            Use a simple page object model that minimally manages page object
            transitions.

            Note: this is not an actual test, because it has no explicit
            assertions. However, the page object model is performing a
            lot of checks and validations in the background, which allows
            this test case to provide a fairly simple API to page interactions.

            :param pwpage: playwright browser page instance
        """
        # we have a webdriver instance from this method's fixture `driver`,
        # which corresponds to the "browser" argument at the CLI invocation

        # instantiate the home page object by calling the PO
        # with the playwright browser page instance
        home_page = pom.HomePage(pwpage)
        home_page.save_screenshot('home page')

        id = 'Sweets'
        sweets_page = home_page.top_menu_goto(id)
        sweets_page.save_screenshot(f"{id} page")

        id = 'About'
        about_page = sweets_page.top_menu_goto(id)
        about_page.save_screenshot(f"{id} page")

        id = 'Login'
        login_page = about_page.top_menu_goto(id)
        login_page.save_screenshot(f"{id} page")

        id = 'Basket'
        basket_page = login_page.top_menu_goto(id)
        basket_page.save_screenshot(f"{id} page")

        id = 'Home'
        home_page = login_page.top_menu_goto(id)
        home_page.save_screenshot(f"{id} page again")

    @pytest.mark.parametrize('scenario',
                             [
                                 ['Sweets', 'Login', 'About'],
                                 ['About', 'Basket', 'Home'],
                                 ['Login', 'Home', 'Sweets'],
                                 ['Basket', 'About', 'Home'],  # expected broken link
                                 ['Basket', 'Sweets', 'Login'],
                                 ['Sweets', 'Basket', 'About'],  # expected broken link
                             ],
                             ids=['scenario01', 'scenario02', 'scenario03',
                                  'scenario04', 'scenario05', 'scenario06'])
    def test_dynamic_navigation(self, pwpage, sweetshop, scenario):
        """
            Dynamic navigation flows. Visit the pages specified in
            the fixture parameter `scenario`.

            Use a simple page object model that minimally manages page object
            transitions.

            Note: this is not an actual test, because it has no explicit
            assertions. However, the page object model is performing a
            lot of checks and validations in the background, which allows
            this test case to provide a fairly simple API to page interactions.
        """
        # we have a webdriver instance from this method's fixture `driver`,
        # which corresponds to the "browser" argument at the CLI invocation

        msg = f"testing navigation path: \nHome --> {'--> '.join(scenario)}"
        logger.info(f"\n{'#' * 60}\n{msg}\n{'#' * 60}\n")

        # instantiate the home page object by calling the PO
        # with the playwright browser page instance
        page = pom.HomePage(pwpage)
        page.save_screenshot('home page')

        for destination in scenario:
            logger.info(f"\nnavigating to {destination} page")
            page = page.top_menu_goto(destination)
            page.save_screenshot(f"{destination.lower()} page loaded")
