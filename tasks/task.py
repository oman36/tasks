import hashlib
import json
import os
import shutil
import time

import jsonschema

from .exceptions import (
    BadRequestException,
    FatalException,
    TaskNotExistException,
    TaskLimitException,
)
from .orm import globals_sessions, Task as TaskModel
from .settings import SETTINGS
from .email import send_email


class InterpretedTask:
    def __init__(self, name, callback, json_schema):
        self.name = name
        self.callback = callback
        self.json_schema = json_schema or {}

    def validate_params(self, params):
        try:
            jsonschema.validate(params, self.json_schema)
        except jsonschema.ValidationError as er:
            raise BadRequestException(er.__str__())

    def run(self, **kwargs):
        return self.callback(**kwargs)

    def to_dict(self):
        return {
            'name': self.name,
            'json_schema': self.json_schema,
        }


class InterpretedTaskList:
    def __init__(self):
        self.tasks_inited = dict()

    def append(self, name, callback, json_schema=None):
        if name in self.tasks_inited:
            raise FatalException('Task "{}" already exists'.format(name))

        self.tasks_inited[name] = InterpretedTask(name, callback, json_schema)

    def get(self, name) -> InterpretedTask:
        if name not in self.tasks_inited:
            raise TaskNotExistException(name)

        return self.tasks_inited[name]


interpreted_task_list = InterpretedTaskList()


def task(name, json_schema=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        interpreted_task_list.append(name, wrapper, json_schema)

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


class Task:
    def __init__(self, task_name, params=None, result_dir=None):
        self.task_name = task_name
        self.params = params or {}
        self.result_dir = result_dir
        self.validate()

    def validate(self):
        self.get_interpreted_task().validate_params(self.params)

    def get_interpreted_task(self):
        return interpreted_task_list.get(self.task_name)

    def run(self):
        result = self.get_interpreted_task().run(**self.params)

        if isinstance(result, Result):
            self.handle_result(result)

        return result

    def handle_result(self, result):
        result_dir = self.result_dir or os.getcwd()

        if not os.path.isdir(result_dir):
            os.makedirs(result_dir)

        for file_data in result.files:
            try:
                shutil.move(file_data['tmp_path'], os.path.join(result_dir, file_data['name']))
            finally:
                del file_data['tmp_path']


class WebTask(Task):
    def __init__(self, task_name_or_model, params=None, email=None):

        if isinstance(task_name_or_model, str):

            if task_name_or_model == 'runserver':
                raise BadRequestException('Task name "runserver" is not allowed')

            super().__init__(task_name_or_model, params)

            self.model = TaskModel(
                name=self.task_name,
                params=json.dumps(self.params),
                status='new',
            )

            if email is not None:
                self.model.email = email

            self.save_model()

        else:
            self.model = task_name_or_model  # type:TaskModel
            self.task_name = self.model.name
            self.params = json.loads(self.model.params)

    def handle_result(self, result):
        if self.model.email:
            return

        result_dir = os.path.join(SETTINGS['files']['web_dir'], str(self.model.id))
        files = []

        if not os.path.isdir(result_dir):
            os.makedirs(result_dir)

        for file_data in result.files:
            file_name = file_data['name']
            shutil.move(file_data['tmp_path'], os.path.join(result_dir, file_name))

            files.append(file_name)

        self.model.files = json.dumps(files)
        self.save_model()

    def run(self):
        self.model.status = 'pending'
        self.save_model()

        result = super().run()

        self.model.status = 'finished'
        self.model.result = str(result)

        self.save_model()

        if self.model.email:
            send_email(
                [self.model.email],
                'Task {} was completed.'.format(self.task_name),
                str(result),
                result.files if isinstance(result, Result) else []
            )

        return result

    def save_model(self):
        globals_sessions[0].add(self.model)
        globals_sessions[0].commit()


def check_limit(name):
    if name in SETTINGS['limits']['names']:
        c = globals_sessions[0].query(TaskModel).filter_by(status='pending', name=name).count()
        if c >= SETTINGS['limits']['names'][name]:
            raise TaskLimitException(f'Limit for task type "{name}" was reached.'
                                     ' The task was put in a queue.')

    if SETTINGS['limits']['global'] <= globals_sessions[0].query(TaskModel).filter_by(status='pending').count():
        raise TaskLimitException('Limit for task was reached. The task was put in a queue.')
