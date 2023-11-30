import logging
import time

from heofon.framework import utils
from heofon.apps.sweetshop.noauth.base_noauth import NoAuthBasePageObject


logger = logging.getLogger(__name__)
INIT_MSG = 'Instantiated PageObject for %s.'
PWINIT_MSG = 'Instantiated PW PageObject for %s.'


class BasePage(NoAuthBasePageObject):
    appname = 'sweetshop'
    domain = 'sweetshop.vivrichards.co.uk'


class HomePage(BasePage):
    name = 'sweetshop home page'
    title = 'Sweet Shop'
    url_path = '/'

    def __init__(self, pwpage):
        self.url = f"https://{self.domain}{self.url_path}"
        self.pwpage = pwpage
        self.pwpage.goto(self.url)
        logger.info('\n' + PWINIT_MSG % self.name)


class SweetsPage(BasePage):
    name = 'sweetshop sweets page'
    title = 'Sweet Shop'
    url_path = '/sweets'

    def __init__(self, pwpage):
        self.url = f"https://{self.domain}{self.url_path}"
        self.pwpage = pwpage
        logger.info('\n' + PWINIT_MSG % self.name)


class AboutPage(BasePage):
    name = 'sweetshop about page'
    title = 'Sweet Shop'
    url_path = '/about'

    def __init__(self, pwpage):
        self.url = f"https://{self.domain}{self.url_path}"
        self.pwpage = pwpage
        logger.info('\n' + PWINIT_MSG % self.name)


class LoginPage(BasePage):
    name = 'sweetshop login page'
    title = 'Sweet Shop'
    url_path = '/login'

    def __init__(self, pwpage):
        self.url = f"https://{self.domain}{self.url_path}"
        self.pwpage = pwpage
        logger.info('\n' + INIT_MSG % self.name)


class BasketPage(BasePage):
    name = 'sweetshop basket page'
    title = 'Sweet Shop'
    url_path = '/basket'

    def __init__(self, pwpage):
        self.url = f"https://{self.domain}{self.url_path}"
        self.pwpage = pwpage
        logger.info('\n' + INIT_MSG % self.name)
