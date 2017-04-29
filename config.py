import json
import os
import sys

FROTZ_EXE_PATH = '/usr/local/bin/dfrotz'
FROTZ_SAVE_PATH = '/var/www/frotz/saves'
FROTZ_DATA_MAP = {
    'zork1': {
        'path': '/var/www/frotz/data/ZORK1.DAT',
        'header': 13,
        'load': 6,
        'save': 3,
    }
}

ENVIRONMENT_SETTING_PREFIX = 'FROTZ_'
ENVIRONMENT_SETTING_SUFFIXES = {
    '__BOOL': lambda x: bool(int(x)),
    '__INT': lambda x: int(x),
    '__JSON': lambda x: json.loads(x),
}
this_module = sys.modules[__name__]
for key, value in os.environ.items():
    if key.startswith(ENVIRONMENT_SETTING_PREFIX):
        for suffix, fn in ENVIRONMENT_SETTING_SUFFIXES.items():
            if key.endswith(suffix):
                value = fn(value)
                key = key[:-len(suffix)]
        setattr(
            this_module,
            key[len(ENVIRONMENT_SETTING_PREFIX):],
            value
        )
