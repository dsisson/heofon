import logging

from heofon.framework import utils_webstorage

logger = logging.getLogger(__name__)


def get_console_log(pwpage):
    """
        Get the current state of the browser console log.

        NOTE: this doesn't actually work yet.

        :param pwpage: playwright page instance
        :return content: dict
    """

    script = """() => {
    if (console.history) {
        return console.history.map(msg => ({
            type: msg.level,
            text: msg.args.join(' ')
        }));
    } else {
        return [];
        }
    }"""

    # run the script
    content = pwpage.evaluate(script)
    return content


def get_local_storage(pwpage):
    """
        Get the window localStorage content for this browser session.

        This uses javascript called by selenium, and then has to do a bunch
        of cleanup in the returned content.

        :param pwpage: playwright page instance
        :return content: dict
    """
    # set the javascript logic
    script = """() => {
        const localStorage = window.localStorage;
        const items = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            items[key] = localStorage.getItem(key);
        }
        return items;
    }"""

    # run the script
    content = pwpage.evaluate(script)

    # convert this dirty data into a real dict
    cleaned_content = utils_webstorage. \
        convert_web_storage_data_to_dict(content, source='local')
    return cleaned_content


def get_session_storage(pwpage):
    """
        Get the window sessionStorage content for this browser session.

        This uses javascript called by selenium, and then has to do a bunch
        of cleanup in the returned content.

        :param pwpage: playwright page instance
        :return content: dict
    """
    # set the javascript logic
    script = """() => {
        const sessionStorage = window.sessionStorage;
        const items = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            items[key] = sessionStorage.getItem(key);
        }
        return items;
    }"""

    # run the script
    content = pwpage.evaluate(script)

    # convert this dirty data into a real dict
    cleaned_content = utils_webstorage. \
        convert_web_storage_data_to_dict(content, source='session')
    return cleaned_content
