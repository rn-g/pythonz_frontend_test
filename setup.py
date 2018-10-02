from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess


class InstallWrapper(install):

    def run(self):
        subprocess.call('pip install -r ./pythonz/requirements.txt')
        subprocess.call('python ./pythonz/manage.py migrate')
        # add robot user to db to avoid error
        subprocess.call('python ./tests/workaround.py')
        # create superuser
        subprocess.call('python ./pythonz/manage.py shell -c "from django.contrib.auth import get_user_model; '
                        'User = get_user_model(); '
                        'User.objects.create_superuser(\'root\', \'admin@example.com\', \'123456\')'
                        'if len(User.objects.filter(username=\'root\')) == 0 else None"')


def parse_requirements(f_name):
    with open(f_name, 'r') as f:
        return f.read().splitlines()


tests_require = parse_requirements('tests/requirements.txt')
setup(
    name='pythonz-frontend-test',
    packages=find_packages(),
    setup_requires=['pytest-runner'],
    tests_require=tests_require,
    cmdclass={
        'install': InstallWrapper
    }
)