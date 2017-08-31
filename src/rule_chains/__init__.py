import os

_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, 'config', path)


def get_grokit_config():
    return get_data('grokit.toml')


def get_names():
    return get_data('names')


def get_patterns(path=''):
    return os.path.join(_ROOT, 'patterns', path)
