import random
import string


class UserGenerator(object):

    @classmethod
    def generate(cls, is_superuser=False):
        return {
            'username': 'user_{}'.format(''.join(random.choice(string.ascii_letters + string.digits)
                                                 for m in range(5))),
            'password': ''.join(random.choice(string.ascii_letters) for m in range(10)),
            'is_superuser': is_superuser
        }