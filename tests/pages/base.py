import re
from arsenic import keys, browsers
from arsenic.errors import NoSuchElement
from pages.locators import BasePageLocators as locators


class WaitForPageChange(object):

    def __init__(self, driver, timeout=10, element='html'):
        self.driver = driver
        self.timeout = timeout
        self.element = element

    async def __aenter__(self):
        html = await self.driver.get_element(self.element)
        self.id = html.id

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.driver.wait(self.timeout, self.page_changed)

    async def page_changed(self):
        html = await self.driver.get_element(self.element)
        return html.id != self.id


class BasePage(object):
    CSS = 'css'
    XPATH = 'xpath'

    def __init__(self, driver):
        self.driver = driver
        self.url = None
        self.get_element_func = {
            self.CSS: self.driver.get_element,
            self.XPATH: self.get_element_by_xpath
        }

    async def login(self, username, password):
        login_link = await self.driver.get_element(locators.LOGIN_LINK)
        async with WaitForPageChange(self.driver):
            await login_link.click()
        await self.set_text(locators.USERNAME_XPATH, username, by='xpath')
        await self.set_text(locators.PASSWORD_XPATH, password, by='xpath')
        await self.submit_form(0)

    async def logout(self):
        username_link = await self.driver.get_element(locators.USERNAME_LINK_2)
        await username_link.click()
        logout_link = await self.driver.get_element(locators.LOGOUT_LINK)
        async with WaitForPageChange(self.driver):
            await logout_link.click()

    async def login_if_not(self, username, password):
        username_link = await self.driver.get_element(locators.USERNAME_LINK)
        text = await username_link.get_text()
        if await username_link.get_attribute('href') == '/login/':
            await self.login(username, password)
        elif not username in text:
            await self.logout()
            await self.login(username, password)
        else:
            return False
        return True

    async def get_url(self):
        self.url = await self.driver.get_url()

    async def get_element_by_xpath(self, selector):
        element_id = await self.driver._request(
            url='/element',
            method='POST',
            data={
                'using': 'xpath',
                'value': selector
            }
        )
        return self.driver.create_element(element_id)

    async def get_elements_by_xpath(self, selector):
        element_ids = await self.driver._request(
            url='/elements',
            method='POST',
            data={
                'using': 'xpath',
                'value': selector
            }
        )
        return [self.driver.create_element(element_id) for element_id in element_ids]

    async def get_text(self, element_id, by=CSS):
        element = await self.get_element_func[by](element_id)
        return await element.get_text()

    async def set_text(self, locator, text, by=CSS):
        element = await self.get_element_func[by](locator)
        await element.send_keys(f'{keys.CONTROL}+A')
        # issue with ChromeDriver Ctrl+A: workaround
        if isinstance(self.driver.browser, browsers.Chrome):
            if by == self.CSS:
                await self.driver.execute_script('document.querySelector("{}").select();'.format(
                    locator.replace('"', '\\"'))
                )
            elif by == self.XPATH:
                await self.driver.execute_script("document.evaluate('{}', document.body).iterateNext().select();".format(
                    locator.replace("'", "\\'"))
                )
        await element.send_keys(text)

    async def set_codemirror_text(self, locator, text):
        element = await self.driver.get_element(locator)
        await element.click()
        _text = text.replace('"', '\\"')
        await self.driver.execute_script(f'var _editor = document.querySelector("{locator}").CodeMirror;'
                                         f'_editor.setValue("{_text}");')

    async def select_by_value(self, locator, value, by=CSS):
        element = await self.get_element_func[by](locator)
        await element.select_by_value(value)

    async def submit_form(self, form_id=0):
        submits = await self.driver.get_elements(locators.SUBMIT)
        submit = submits[form_id]
        await submit.click()

    async def reload_page(self):
        if self.url is not None:
            url = re.findall(r'//[^/]+(.+)', self.url)[0]
            await self.driver.get(url)

    async def is_403(self):
        try:
            await self.get_element_by_xpath(locators.HEADER_403_XPATH)
        except NoSuchElement:
            return False
        else:
            return True