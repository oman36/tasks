import os
import json

import jsonschema

from .exceptions import FatalException

SETTINGS = {}


def init_settings(filename):
    json_schema = {
        "type": "object",
        "properties": {
            "db": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    }
                },
                "required": ["url"]
            },
            "email": {
                "type": "object",
                "properties": {
                    "from": {
                        "type": "string"
                    },
                    "host": {
                        "type": "string"
                    },
                    "port": {
                        "type": "integer"
                    },
                    "pass": {
                        "type": "string"
                    }
                },
                "required": ["from", "host", "port"]
            },
            "files": {
                "type": "object",
                "properties": {
                    "tmp_dir": {
                        "type": "string"
                    },
                    "web_dir": {
                        "type": "string"
                    },
                },
                "required": ["web_dir"]
            },
            "limits": {
                "type": "object",
                "properties": {
                    "global": {
                        "type": "number",
                        "minimum": 1
                    },
                    "names": {
                        "type": "object",
                    }
                },
                "required": ["global", "names"]
            },
        },
        "required": ["files", "db", "email", "limits"]
    }

    with open(filename) as conf:
        try:
            SETTINGS.update(**json.load(conf))
        except json.JSONDecodeError:
            raise FatalException('Invalid json file was passed as settings file')

    if 'DB_URL' in os.environ:
        SETTINGS['db']['url'] = os.environ['DB_URL']

    if 'SMTP_FROM' in os.environ:
        SETTINGS['email']['from'] = os.environ['SMTP_FROM']
    if 'SMTP_HOST' in os.environ:
        SETTINGS['email']['host'] = os.environ['SMTP_HOST']
    if 'SMTP_PORT' in os.environ:
        SETTINGS['email']['port'] = os.environ['SMTP_PORT']
    if 'SMTP_PASS' in os.environ:
        SETTINGS['email']['pass'] = os.environ['SMTP_PASS']

    try:
        jsonschema.validate(SETTINGS, json_schema)
    except jsonschema.ValidationError as er:
        raise FatalException(er.__str__())
