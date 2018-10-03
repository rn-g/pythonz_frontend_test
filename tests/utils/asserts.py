"""
Вспомогательные функции для ассертов в тестах
"""


def dict_common_fields_equal(dict1, dict2):
    s = dict1.keys() & dict2.keys()
    c_dict1 = {k: v for k, v in dict1.items() if k in s}
    c_dict2 = {k: v for k, v in dict2.items() if k in s}
    return c_dict1 == c_dict2