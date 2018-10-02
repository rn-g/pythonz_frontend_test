# pythonz_frontend_test
Автотесты frontend для проекта pythonz. 

**Развертывание**
- Получаем исходный код проекта:

`git clone https://github.com/ruslankl029/pythonz_frontend_test.git`
- Переходим в корневую папку проекта:

`сd pythonz_frontend_test`
- Создаем виртуальное окружение:

`virtualenv -p /usr/bin/python3 venv/`
- Активируем созданное виртуальное окружение: 

`. venv/bin/activate`
- Запускаем скрипт установки зависимостей и настройки приложения:

`python setup.py install`
- Запускаем сервер приложения:

`python pythonz/manage.py runserver`

**Запуск тестов**
- Настройка pytest в файле `setup.cfg`. По умолчанию тесты запускаются в 2 потока с генерацией отчетов allure:

`
[tool:pytest]
addopts = --ignore=venv --ignore=pythonz/tests -n 2 --alluredir=tests/allure-results
`
- Настройка параметров запуска тестов в файле `tests/config.json`. Возможен выбор браузеров: `firefox` или `chrome`. 
Для запуска тестов `geckodriver` или `chromedriver` должны находиться в переменной окружения PATH. Параметр `db_path` 
содержит путь до sqlite БД приложения. После выполнения тестов файл БД возвращается в начальное состояние.
- Запуск:

`python setup.py test`

**Просмотр отчета**

`allure serve tests/allure-results`