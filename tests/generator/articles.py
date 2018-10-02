import random
import string


class ArticleGenerator(object):

    @classmethod
    def generate(cls):
        return {
            'title': 'title_' + ''.join(random.choice(string.ascii_letters) for m in range(10)),
            'description': 'description_' + ''.join(random.choice(string.ascii_letters) for m in range(10)),
            'text': 'text_' + ''.join(random.choice(string.ascii_letters) for m in range(10))
        }