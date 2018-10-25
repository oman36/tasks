import argparse
import json
import sys

import jsonschema

tasks_inited = dict()


def error(msg):
    sys.stderr.write('ERROR: {}\n'.format(msg))


def task(name, json_schema=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        tasks_inited[name] = {
            'callback': wrapper,
            'json_schema': dict() if json_schema is None else json_schema,
        }
        return wrapper

    return decorator


class BaseTask:
    def __init_subclass__(cls) -> None:
        if not hasattr(cls, 'name') or not isinstance(getattr(cls, 'name'), str):
            error('Task must have string parameter "name"')
        elif not hasattr(cls, 'run') or not callable(getattr(cls, 'run')):
            error('Task must have method "run"')
        else:
            params = {
                'name': cls.name,
                'json_schema': cls.json_schema if hasattr(cls, 'json_schema') else None,
            }
            task(**params)(cls.run)

        super().__init_subclass__()


def run_cli():
    parser = argparse.ArgumentParser(description="calculate X to the power of Y")
    parser.add_argument("task_name")
    parser.add_argument("--params", required=False)
    args = parser.parse_args()

    try:
        params = dict() if args.params is None else json.loads(args.params)
    except json.decoder.JSONDecodeError:
        return error('Invalid json string was passed as params')

    if args.task_name not in tasks_inited:
        error('Task "{}" does not exits'.format(args.task_name))

    called_task = tasks_inited[args.task_name]

    try:
        jsonschema.validate(params, called_task['json_schema'])
    except jsonschema.ValidationError as er:
        return error(er.__str__())

    sys.stdout.write(str(called_task['callback'](**params)) + '\n')


__all__ = ['task', 'BaseTask']
