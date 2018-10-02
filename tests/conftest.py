# -*- coding: utf-8 -*-
import os
import tempfile
import shutil
import json
import pytest
import asyncio
from arsenic import start_session, services, browsers, stop_session
from pages.admin import Admin
from generator.articles import ArticleGenerator
from generator.users import UserGenerator


target = None


def load_config(_file):
    global target
    if target is None:
        target_filename = _file
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), target_filename) \
            if os.path.basename(target_filename) == target_filename else target_filename
        with open(config_file) as f:
            target = json.load(f)
    return target


def pytest_generate_tests(metafunc):
    if 'data' in metafunc.fixturenames:
        data = None
        if metafunc.module.__name__ == 'articles':
            data = [ArticleGenerator.generate() for x in range(2)]
        if data:
            metafunc.parametrize('data', [data])


def pytest_addoption(parser):
    parser.addoption('--config-file', action='store', default='config.json')


@pytest.yield_fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    if os.name != 'nt':
        asyncio.get_child_watcher().attach_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def session(request):
    config = load_config(request.config.getoption('--config-file'))
    if 'db_path' in config:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, 'tmp_pythonz_db')
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), config['db_path']))
        if not os.path.isfile(temp_path):
            shutil.copy2(db_path, temp_path)
    if config['browser'] == 'firefox':
        service = services.Geckodriver()
        browser = browsers.Firefox()
    elif config['browser'] == 'chrome':
        service = services.Chromedriver()
        browser = browsers.Chrome()
    else:
        raise ValueError(f"Unrecognized browser {config['browser']}")
    session = await start_session(
        service,
        browser,
        bind=config['base_url']
    )
    try:
        yield session
    finally:
        await stop_session(session)
        if 'db_path' in config:
            if os.path.isfile(temp_path):
                shutil.copy2(temp_path, db_path)
                os.remove(temp_path)


@pytest.fixture(scope='session')
async def users(session, request):
    config = load_config(request.config.getoption('--config-file'))
    admin = Admin(session, config['superuser']['username'], config['superuser']['password'])
    # 1 суперпользователь и 2 обычных
    users = [UserGenerator.generate(is_superuser=bool(i % 2)) for i in range(3)]
    for u in users:
        await admin.create_user(u['username'], u['password'], u['is_superuser'])
    yield admin.user_list