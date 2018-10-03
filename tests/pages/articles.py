import re
from pages.base import BasePage, WaitForPageChange
from pages.locators import ArticlesPageLocators, ArticleViewPageLocators, ArticleEditPageLocators
from arsenic.errors import NoSuchElement
from utils.exceptions import *


class ArticlesPage(BasePage):
    """Объект для страницы раздела статей"""

    def __init__(self, driver):
        super().__init__(driver)
        self.locators = ArticlesPageLocators

    async def create_article(self, **kwargs):
        add_article_link = await self.driver.get_element(self.locators.ARTICLE_ADD_LINK)
        async with WaitForPageChange(self.driver):
            await add_article_link.click()
        await self.set_text(self.locators.INPUT_TITLE, kwargs['title'])
        await self.set_text(self.locators.INPUT_DESCRIPTION, kwargs['description'])
        if 'status' in kwargs:
            try:
                f_status = await self.driver.get_element(self.locators.SELECT_STATUS)
            except NoSuchElement:
                raise NoStatusElement
            else:
                await f_status.select_by_value(kwargs['status'])
        await self.set_codemirror_text(self.locators.INPUT_TEXT, kwargs['text'])
        async with WaitForPageChange(self.driver):
            await self.submit_form()
        res = ArticleViewPage(self.driver)
        await res.get_url()
        return res

    async def get_articles(self, _filter=None):
        res = list()
        article_els = await self.get_elements_by_xpath(self.locators.ARTICLE_LIST_ITEMS_XPATH)
        for el in article_els:
            article = dict()
            obj = await el.get_element(self.locators.ARTICLE_TITLE)
            href = await obj.get_attribute('href')
            span = await el.get_element(self.locators.ARTICLE_LIKES)
            article['id'] = int(re.findall(r'/articles/([0-9]+)/', href)[0])
            article['title'] = await obj.get_text()
            likes = await span.get_text()
            article['likes'] = int(likes)
            if not callable(_filter) or callable(_filter) and _filter(article):
                res.append(article)
        return res

    async def load_article(self, article_id):
        article_link = await self.driver.get_element(self.locators.ARTICLE_LINK.format(article_id))
        async with WaitForPageChange(self.driver):
            await article_link.click()
        res = ArticleViewPage(self.driver)
        await res.get_url()
        return res


class ArticleViewPage(BasePage):
    """Объект для страницы просмотра статьи"""

    def __init__(self, driver, id=None):
        super().__init__(driver)
        self.locators = ArticleViewPageLocators
        self.id = id
        self.title = None
        self.description = None
        self.text = None
        self.editable = None
        self.likes = None

    async def get_data(self):
        res = dict()
        res['id'] = int(re.findall(r'/articles/([0-9]+)/', self.url)[0])
        res['title'] = await self.get_text(self.locators.TITLE)
        res['description'] = await self.get_text(self.locators.DESCRIPTION)
        res['text'] = await self.get_text(self.locators.TEXT)
        try:
            await self.driver.get_element(self.locators.EDIT_BUTTON)
        except NoSuchElement:
            res['editable'] = False
        else:
            res['editable'] = True
        res['likes'] = await self.get_text(self.locators.LIKES)
        self.id = res['id']
        self.title = res['title']
        self.description = res['description']
        self.text = res['text']
        self.editable = res['editable']
        self.likes = res['likes']
        return res

    async def open_edit_page(self):
        if not self.editable:
            raise EntityNotEditable("User cannot edit the article")
        f_edit_button = await self.driver.get_element(self.locators.EDIT_BUTTON)
        async with WaitForPageChange(self.driver):
            await f_edit_button.click()
        res = ArticleEditPage(self.driver, id=self.id)
        await res.get_url()
        return res

    async def like_article(self):
        b_set_rate = await self.driver.get_element(self.locators.LIKE_BUTTON)
        if await b_set_rate.get_attribute('data-xaction') == '1':
            async with WaitForPageChange(self.driver, element=self.locators.LIKE_BUTTON):
                await b_set_rate.click()

    async def unlike_article(self):
        b_set_rate = await self.driver.get_element(self.locators.LIKE_BUTTON)
        if await b_set_rate.get_attribute('data-xaction') == '0':
            async with WaitForPageChange(self.driver, element=self.locators.LIKE_BUTTON):
                await b_set_rate.click()

    async def is_liked(self):
        b_set_rate = await self.driver.get_element(self.locators.LIKE_BUTTON)
        attr = await b_set_rate.get_attribute('data-xaction')
        return attr == '0'

    async def get_like_count(self):
        count = await self.get_text(self.locators.LIKE_COUNT)
        return int(count)


class ArticleEditPage(BasePage):
    """Объект для страницы редактирования статьи"""

    def __init__(self, driver, id=None):
        super().__init__(driver)
        self.id = id
        self.locators = ArticleEditPageLocators

    async def edit_article(self, **kwargs):
        for arg in kwargs:
            if arg == 'title':
                await self.set_text(self.locators.TITLE, kwargs[arg])
            elif arg == 'description':
                await self.set_text(self.locators.DESCRIPTION, kwargs[arg])
            elif arg == 'status':
                await self.select_by_value(self.locators.STATUS, kwargs[arg])
            elif arg == 'text':
                await self.set_codemirror_text(self.locators.TEXT, kwargs[arg])
        await self.submit_form()
