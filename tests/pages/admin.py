import asyncio


class Admin(object):
    """Объект для страниц администрирования"""

    def __init__(self, driver, username, password):
        self.current_page = None
        self.driver = driver
        self.username = username
        self.password = password
        self.user_list = []

    async def create_user(self, username, password, is_superuser=False):
        await self.driver.get('/admin/apps/user/add/')
        if not await self.is_logged_in():
            await self.login()
        await self.driver.wait_for_element(10, 'div#user-tools')
        f_username = await self.driver.get_element('input#id_username')
        f_password1 = await self.driver.get_element('input#id_password1')
        f_password2 = await self.driver.get_element('input#id_password2')
        await f_username.send_keys(username)
        await f_password1.send_keys(password)
        await f_password2.send_keys(password)
        await asyncio.sleep(self.driver.time_wait)
        save_button = await self.driver.get_element('input[name="_save"]')
        await save_button.click()
        f_success_text = await self.driver.wait_for_element(10, 'li.success')
        success_text = await f_success_text.get_text()
        assert username in success_text
        if is_superuser:
            f_is_superuser = await self.driver.get_element('input#id_is_superuser')
            await f_is_superuser.click()
            save_button = await self.driver.get_element('input[name="_save"]')
            await save_button.click()
        self.user_list.append({
            'username': username,
            'password': password,
            'is_superuser': is_superuser
        })

    async def is_logged_in(self):
        url = await self.driver.get_url()
        return '/admin/login/' not in url

    async def login(self):
        f_username = await self.driver.get_element('input[name="username"]')
        f_password = await self.driver.get_element('input[name="password"]')
        submit = await self.driver.get_element('input[type="submit"]')
        await f_username.send_keys(self.username)
        await f_password.send_keys(self.password)
        await submit.click()