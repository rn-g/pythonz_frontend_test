import pytest
import allure
import random
import string
from pages.main import MainPage
from utils.asserts import *
from utils.exceptions import *

pytestmark = pytest.mark.asyncio


async def test_user_create_article(session, users, data):
    """Создание статьи обычным пользователем
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
    with allure.step('Проверить что данные созданной статьи соответствуют введенным'):
        article_page_data = await view_page.get_data()
        assert dict_common_fields_equal(article_page_data, data[0])


async def test_user_edit_own_article(session, users, data):
    """Изменение своей статьи обычным пользователем до публикации
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
        new_data = await view_page.get_data()
        new_data['title'] = data[1]['title']
        new_data['text'] = data[1]['text']
    with allure.step('Нажать на кнопку редактирования статьи'):
        edit_page = await view_page.open_edit_page()
    with allure.step('Изменить статью, ввести новые данные'):
        await edit_page.edit_article(**new_data)
        await view_page.reload_page()
    with allure.step('Проверить что данные измененной статьи соответствуют введенным'):
        article_page_data = await view_page.get_data()
        assert dict_common_fields_equal(article_page_data, new_data)


async def test_superuser_create_article(session, users, data):
    """Создание статьи суперпользователем
    """
    with allure.step('Войти под суперпользователем'):
        user = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
    with allure.step('Проверить что данные созданной статьи соответствуют введенным'):
        article_page_data = await view_page.get_data()
        assert dict_common_fields_equal(article_page_data, data[0])


async def test_superuser_edit_foreign_article(session, users, data):
    """Изменение чужой статьи суперпользователем
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
    with allure.step('Войти под суперпользователем, открыть страницу созданной статьи'):
        new_data = await view_page.get_data()
        await view_page.login_if_not(superuser['username'], superuser['password'])
        await view_page.reload_page()
        new_data['title'] = data[1]['title']
        new_data['description'] = data[1]['description']
        new_data['text'] = data[1]['text']
    with allure.step('Нажать на кнопку редактирования статьи'):
        edit_page = await view_page.open_edit_page()
    with allure.step('Изменить статью, ввести новые данные'):
        await edit_page.edit_article(**new_data)
        await view_page.reload_page()
    with allure.step('Проверить что данные измененной статьи соответствуют введенным'):
        article_page_data = await view_page.get_data()
        assert dict_common_fields_equal(article_page_data, new_data)


async def test_published_article_visibility(session, users, data):
    """Публикация статьи и проверка ее видимости в списке
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
    with allure.step('Войти под суперпользователем, открыть страницу созданной статьи'):
        new_data = await view_page.get_data()
        await view_page.login_if_not(superuser['username'], superuser['password'])
        await view_page.reload_page()
    with allure.step('Нажать на кнопку редактирования статьи'):
        new_data['status'] = '2'
        edit_page = await view_page.open_edit_page()
    with allure.step('Изменить статус на "Опубликован"'):
        await edit_page.edit_article(**new_data)
    with allure.step('Перейти в раздел "Статьи"'):
        await articles_page.reload_page()
    with allure.step('Проверить что опубликованная статья появилась в списке'):
        article_list = await articles_page.get_articles()
        target = [x for x in article_list if x['id'] == new_data['id'] and x['title'] == new_data['title']]
        assert len(target) == 1


async def test_like_article(session, users, data):
    """Установка лайка статье
    """
    with allure.step('Войти под суперпользователем'):
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(superuser['username'], superuser['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Найти статью с количеством лайков равным 0, или создать новую статью со статусом "Опубликован"'):
        article_list = await articles_page.get_articles(_filter=lambda x: x['likes'] == 0)
        if len(article_list) == 0:
            data[0]['status'] = '2'
            view_page = await articles_page.create_article(**data[0])
        else:
            view_page = await articles_page.load_article(article_list[0]['id'])
    with allure.step('Открыть статью, поставить лайк, нажав на кнопку "Одобряю!"'):
        old_like_count = await view_page.get_like_count()
        await view_page.like_article()
    with allure.step('Проверить что количество лайков увеличилось на 1'):
        new_like_count = await view_page.get_like_count()
        assert new_like_count == old_like_count + 1


async def test_unlike_article(session, users, data):
    """Снятие лайка со статьи
    """
    with allure.step('Войти под суперпользователем'):
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(superuser['username'], superuser['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Найти статью с количеством лайков равным 0, или создать новую статью со статусом "Опубликован"'):
        article_list = await articles_page.get_articles(_filter=lambda x: x['likes'] == 0)
        if len(article_list) == 0:
            data[0]['status'] = '2'
            view_page = await articles_page.create_article(**data[0])
        else:
            view_page = await articles_page.load_article(article_list[0]['id'])
    with allure.step('Открыть статью, поставить лайк, нажав на кнопку "Одобряю!"'):
        if not await view_page.is_liked():
            await view_page.like_article()
    with allure.step('Запомнить количество лайков, убрать лайк, нажав на кнопку "Сбросить одобрение"'):
        old_like_count = await view_page.get_like_count()
        await view_page.unlike_article()
    with allure.step('Проверить что количество лайков уменьшилось на 1'):
        new_like_count = await view_page.get_like_count()
        assert new_like_count == old_like_count - 1


async def test_new_article_on_main_page(users, session, data):
    """Проверка отображения опубликованной статьи на главной странице сайта
    """
    with allure.step('Войти под суперпользователем'):
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(superuser['username'], superuser['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью со статусом "Опубликован"'):
        data[0]['status'] = '2'
        await articles_page.create_article(**data[0])
    with allure.step('Перейти на главную страницу'):
        await main_page.reload_page()
    with allure.step('Проверить что опубликованная статья появилась в начале списка виджета "Статьи"'):
        article_list = await main_page.get_article_list()
        assert len(article_list) > 0
        assert article_list[0]['title'] == data['title']


@pytest.mark.negative
async def test_user_view_foreign_draft_article(session, users, data):
    """Просмотр черновика статьи другим обычным пользователем
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
    with allure.step('Войти под другми обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][1]
        await view_page.login_if_not(user['username'], user['password'])
    with allure.step('Открыть страницу созданной статьи'):
        await view_page.reload_page()
    with allure.step('Проверить что открылась страница ошибки 403'):
        is_403 = await view_page.is_403()
        assert is_403


@pytest.mark.negative
async def test_user_can_change_article_state(session, users, data):
    """Изменение статуса статьи обычным пользователем
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Попытаться создать статью с указанием статуса "Опубликован". '
                     'Проверить что поле "Статус" недоступно'):
        data[0]['status'] = '2'
        with pytest.raises(NoStatusElement):
            await articles_page.create_article(**data[0])


@pytest.mark.negative
async def test_draft_article_visibility(session, users, data):
    """Проверка видимости статьи со статусом "Черновик" в списке статей
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
        new_data = await view_page.get_data()
    with allure.step('Войти под суперпользователем'):
        await view_page.login_if_not(superuser['username'], superuser['password'])
    with allure.step('Перейти на страницу просмотра созданной статьи'):
        await view_page.reload_page()
    with allure.step('Изменить статью, указать статус "Черновик"'):
        new_data['status'] = '1'
        edit_page = await view_page.open_edit_page()
        await edit_page.edit_article(**new_data)
    with allure.step('Перейти на страницу списка статей'):
        await articles_page.reload_page()
    with allure.step('Проверить что статья отсутствует в списке'):
        article_list = await articles_page.get_articles()
        target = [x for x in article_list if x['id'] == new_data['id'] and x['title'] == new_data['title']]
        assert len(target) == 0


@pytest.mark.negative
async def test_deleted_article_visibility(session, users, data):
    """Проверка видимости статьи со статусом "Удален" в списке статей
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
        new_data = await view_page.get_data()
    with allure.step('Войти под суперпользователем'):
        await view_page.login_if_not(superuser['username'], superuser['password'])
    with allure.step('Перейти на страницу просмотра созданной статьи'):
        await view_page.reload_page()
    with allure.step('Изменить статью, указать статус "Удален"'):
        new_data['status'] = '3'
        edit_page = await view_page.open_edit_page()
        await edit_page.edit_article(**new_data)
    with allure.step('Перейти на страницу списка статей'):
        await articles_page.reload_page()
    with allure.step('Проверить что статья отсутствует в списке'):
        article_list = await articles_page.get_articles()
        target = [x for x in article_list if x['id'] == new_data['id'] and x['title'] == new_data['title']]
        assert len(target) == 0


@pytest.mark.negative
async def test_archived_article_visibility(session, users, data):
    """Проверка видимости статьи со статусом "В архиве" в списке статей
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
        new_data = await view_page.get_data()
    with allure.step('Войти под суперпользователем'):
        await view_page.login_if_not(superuser['username'], superuser['password'])
    with allure.step('Перейти на страницу просмотра созданной статьи'):
        await view_page.reload_page()
    with allure.step('Изменить статью, указать статус "В архиве"'):
        new_data['status'] = '4'
        edit_page = await view_page.open_edit_page()
        await edit_page.edit_article(**new_data)
    with allure.step('Перейти на страницу списка статей'):
        await articles_page.reload_page()
    with allure.step('Проверить что статья отсутствует в списке'):
        article_list = await articles_page.get_articles()
        target = [x for x in article_list if x['id'] == new_data['id'] and x['title'] == new_data['title']]
        assert len(target) == 0


@pytest.mark.negative
async def test_deferred_article_visibility(session, users, data):
    """Проверка видимости статьи со статусом "К отложенной публикации" в списке статей
    """
    with allure.step('Войти под обычным пользователем'):
        user = [x for x in users if not x['is_superuser']][0]
        superuser = [x for x in users if x['is_superuser']][0]
        main_page = MainPage(session)
        await main_page.load()
        await main_page.login_if_not(user['username'], user['password'])
    with allure.step('Перейти в раздел "Статьи"'):
        articles_page = await main_page.open_articles_page()
    with allure.step('Создать новую статью'):
        view_page = await articles_page.create_article(**data[0])
        new_data = await view_page.get_data()
    with allure.step('Войти под суперпользователем'):
        await view_page.login_if_not(superuser['username'], superuser['password'])
    with allure.step('Перейти на страницу просмотра созданной статьи'):
        await view_page.reload_page()
    with allure.step('Изменить статью, указать статус "В архиве"'):
        new_data['status'] = '5'
        edit_page = await view_page.open_edit_page()
        await edit_page.edit_article(**new_data)
    with allure.step('Перейти на страницу списка статей'):
        await articles_page.reload_page()
    with allure.step('Проверить что статья отсутствует в списке'):
        article_list = await articles_page.get_articles()
        target = [x for x in article_list if x['id'] == new_data['id'] and x['title'] == new_data['title']]
        assert len(target) == 0
