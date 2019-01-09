import os

from .em_base_generator import EmBaseGenerator
from .em_additional_em_helper import *

ebg = EmBaseGenerator(os.path.join(os.path.dirname(__file__), 'template.tpl'))


def generate_base_etk_module(*args, **kwargs):
    return ebg.generate_em_base(*args, **kwargs)
