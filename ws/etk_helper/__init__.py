import os

from .em_base_generator import EmBaseGenerator

ebg = EmBaseGenerator(os.path.join(os.path.dirname(__file__), 'template.tpl'))


def generate_base_etk_module(*args, **kwargs):
    return ebg.generate_em_base(*args, **kwargs)
