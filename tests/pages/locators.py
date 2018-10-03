"""
Модуль содержит классы с константами локаторов страниц
"""


class BasePageLocators(object):
    USERNAME_LINK = 'ul.nav.navbar-right a'
    USERNAME_LINK_2 = 'ul.nav.navbar-right a[href="#"]'
    LOGOUT_LINK = 'a[href="/logout/"]'
    LOGIN_LINK = 'a[href="/login/"]'
    USERNAME_XPATH = '(.//form)[2]//input[@id="id_username"]'
    PASSWORD_XPATH = '(.//form)[2]//input[@id="id_password"]'
    SUBMIT = 'input[type="submit"]'
    HEADER_403_XPATH = './/div[@class="page-header"]/h1[contains(text(), "403")]'


class MainPageLocators(object):
    ARTICLE_LINK = 'a[href="/articles/"]'
    ARTICLE_LIST_XPATH = "(.//div[contains(@class, 'card')])[1]/ul"


class ArticlesPageLocators(object):
    ARTICLE_LINK = 'a[href="/articles/{}/"]'
    ARTICLE_ADD_LINK = 'a[href="/articles/add/"]'
    INPUT_TITLE = 'input[name="title"]'
    INPUT_DESCRIPTION = 'textarea[name="description"]'
    INPUT_TEXT = 'div.CodeMirror'
    SELECT_STATUS = 'select[name="status"]'
    ARTICLE_LIST_ITEMS_XPATH = '(.//li[@class="marg__b_mid"]/parent::ul/parent::div)[1]/ul/li'
    ARTICLE_TITLE = 'h4 a'
    ARTICLE_LIKES = 'div span.label'


class ArticleViewPageLocators(object):
    TITLE = 'ul.breadcrumb li.active'
    DESCRIPTION = 'div.lead'
    TEXT = 'div.py_user'
    EDIT_BUTTON = 'div#page_controls button[type="submit"]'
    LIKES = 'div#rate_box span.label'
    LIKE_BUTTON = 'button#set_rate'
    LIKE_COUNT = 'button#set_rate span'


class ArticleEditPageLocators(object):
    TITLE = 'input[name="title"]'
    DESCRIPTION = 'textarea[name="description"]'
    STATUS = 'select[name="status"]'
    TEXT = 'div.CodeMirror'