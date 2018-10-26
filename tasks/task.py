import jsonschema
import json

from .exceptions import (
    BadRequestException,
    FatalException,
    TaskNotExistException,
)
from .orm import Session, Task

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

    return result
