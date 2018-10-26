import hashlib
import json
import os
import time

import jsonschema

from .exceptions import (
    BadRequestException,
    FatalException,
    TaskNotExistException,
)
from .orm import Session, Task
from .settings import SETTINGS

tasks_inited = dict()


def task(name, json_schema=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if name in tasks_inited:
            raise FatalException('Task "{}" already exists'.format(name))

        tasks_inited[name] = {
            'callback': wrapper,
            'json_schema': dict() if json_schema is None else json_schema,
        }
        return wrapper

    return decorator


class BaseTask:
    def __init_subclass__(cls) -> None:
        if not hasattr(cls, 'name') or not isinstance(getattr(cls, 'name'), str):
            raise FatalException('Task must have string parameter "name"')
        elif not hasattr(cls, 'run') or not callable(getattr(cls, 'run')):
            raise FatalException('Task must have method "run"')
        else:
            params = {
                'name': cls.name,
                'json_schema': cls.json_schema if hasattr(cls, 'json_schema') else None,
            }
            task(**params)(cls.run)

        super().__init_subclass__()


class Result:
    tmp_dir = SETTINGS.get('files', {}).get('tmp_dir', '/tmp/task_files/')

    def __init__(self, msg: str, files: list):
        self.msg = msg
        self.files = files

        if not os.path.isdir(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        for file in self.files:
            file['data'].seek(0)
            file_tmp_name = hashlib.md5((file['name'] + str(time.time())).encode()).hexdigest()
            file['tmp_path'] = os.path.join(self.tmp_dir, file_tmp_name)
            with open(file['tmp_path'], 'wb+') as output:
                for chunk in iter(lambda: file['data'].read(1024), bytes()):
                    output.write(chunk)

    def __str__(self):
        return self.msg


def run_command(args: dict, task_in_db=None):
    if 'task_name' not in args:
        raise BadRequestException('task_name is required')

    if args['task_name'] not in tasks_inited:
        raise TaskNotExistException(args['task_name'])

    called_task = tasks_inited[args['task_name']]

    try:
        jsonschema.validate(args['params'], called_task['json_schema'])
    except jsonschema.ValidationError as er:
        raise BadRequestException(er.__str__())

    session = Session()

    if args['task_name'] != 'runserver':
        if task_in_db is None:
            task_in_db = Task(
                name=args['task_name'],
                params=json.dumps(args['params']),
                status='new',
            )
            session.add(task_in_db)
            session.commit()
        else:
            session.add(task_in_db)

    result = called_task['callback'](**args['params'])

    if args['task_name'] != 'runserver':
        task_in_db.status = 'finished'
        task_in_db.result = str(result)
        session.commit()
    session.close()

    return result
