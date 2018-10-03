import re
from pages.articles import ArticlesPage
from pages.base import BasePage, WaitForPageChange
from pages.locators import MainPageLocators


class MainPage(BasePage):
    """Объект для главной страницы сайта"""

    def __init__(self, driver):
        super().__init__(driver)
        self.locators = MainPageLocators

    async def load(self):
        async with WaitForPageChange(self.driver):
            await self.driver.get('/')
        await self.get_url()

    async def open_articles_page(self):
        link = await self.driver.get_element(self.locators.ARTICLE_LINK)
        async with WaitForPageChange(self.driver):
            await link.click()
        res = ArticlesPage(self.driver)
        await res.get_url()
        return res

    async def get_article_list(self):
        res = list()
        article_list = await self.get_element_by_xpath(self.locators.ARTICLE_LIST_XPATH)
        article_els = await article_list.get_elements('li')
        for el in article_els:
            article = dict()
            obj = await el.get_element('a')
            href = await obj.get_attribute('href')
            if href == '':
                continue
            article['id'] = int(re.findall(r'/articles/([0-9]+)/', href)[0])
            article['title'] = await obj.get_text()
            res.append(article)
        return res