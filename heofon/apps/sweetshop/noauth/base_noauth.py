import logging
import time


from heofon.apps.sweetshop.base_page import BaseWrapperPageObject

logger = logging.getLogger(__name__)


class NoAuthBasePageObject(BaseWrapperPageObject):
    """
        Base PO class for all no-authentication pages. Any class methods
        or class properties general to all of those pages go here.
    """
    # str enum, either 'noauth' or 'auth', as appropriate
    page_auth_mode = 'noauth'

    def generate_nav_path(self, target):
        """
            Convert the desired `target` str into a list of two str nav targets,
            where the first is an activator for a dynamic sub-menu, and the
            second is the actual desired page.

            :param target:
            :return: list of stage1 and stage 2 nav targets
        """
        map_destination_to_path = {
            'Home': ['Home', 'Home'],
            'Sweets': ['Sweets', 'Sweets'],
            'About': ['About', 'About'],
            'Login': ['Login', 'Login'],
            'Basket': ['Basket', 'Basket'],
        }
        return map_destination_to_path[target]

    def top_menu_goto(self, destination):
        """
            This is a multi-stage navigation interaction with the top nav.
            Click `target2` to navigate to the targeted page.

            :param destination: str, identifier text for desired destination
            :return next_page: page object
        """
        pwpage = self.pwpage

        target1, target2 = self.generate_nav_path(destination)
        # map of targets to selector and PO info
        target_links = {
            'Home': {
                'sel_stage1': "nav a.navbar-brand",
                'stage2': {
                    'Home': {
                        'sel': "nav a.navbar-brand",
                        'po': 'sweetshop home page',
                        'target': '/'
                    }
                },
            },
            'Sweets': {
                'sel_stage1': "nav a:has-text('Sweets')",
                'stage2': {
                    'Sweets': {
                        'sel': "nav a:has-text('Sweets')",
                        'po': 'sweetshop sweets page',
                        'target': '/sweets'
                    },
                },
            },
            'About': {
                'sel_stage1': "nav a:has-text('About')",
                'stage2': {
                    'About': {
                        'sel': "nav a:has-text('About')",
                        'po': 'sweetshop about page',
                        'target': '/about'
                    },
                },
            },
            'Login': {
                'sel_stage1': "nav a:has-text('Login')",
                'stage2': {
                    'Login': {
                        'sel': "nav a:has-text('Login')",
                        'po': 'sweetshop login page',
                        'target': '/login'
                    },
                },
            },
            'Basket': {
                'sel_stage1': "nav a:has-text('Basket')",
                'stage2': {
                    'Basket': {
                        'sel': "nav a:has-text('Basket')",
                        'po': 'sweetshop basket page',
                        'target': '/basket'
                    },
                },
            },
        }

        # get the stage1 nav target element
        selector = target_links[target1]['sel_stage1']
        stage1 = pwpage.locator(selector)
        logger.info(f"\nstage1 str: '{selector}'")

        # # mouseover to trigger the sub menu (no worries if there is no sub-menu)
        # # however, this really needs a check that *something* happened here
        # self._goto_and_hover(stage1, name=destination)
        # self.save_screenshot(f"hover for target1")

        # click to trigger sub menu
        # msg = f"multi-stage nav action, clicked {target1}"
        # self._click_element(stage1, target1, msg=msg)
        # self.save_screenshot(f"click for target1")

        # get the stage2 nav target element
        selector = target_links[target1]['stage2'][target2]['sel']
        stage2_link = pwpage.locator(selector)
        logger.info(f"\nstage2 str: '{selector}'")
        # self._goto_and_hover(stage2_link, name=target2)
        # self.save_screenshot(f"hover for target2")

        event = f"clicked {target2} destination link"
        name = f"destination link {target2}"

        # get the page object identifier for the target page
        po_selector = target_links[target1]['stage2'][target2]['po']
        logger.info(f"\nstage2 po_selector: '{po_selector}'")

        # click the primary link, which will load the new page object
        next_page = self._click_and_load_new_page(stage2_link,
                                                  po_selector=po_selector,
                                                  name=name,
                                                  change_url=True,
                                                  actions={'unhover': (0, 400)})

        return next_page
