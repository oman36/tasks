import argparse
import json
import sys

tasks_inited = dict()


def error(msg):
    sys.stderr.write('ERROR: {}\n'.format(msg))


def task(name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        tasks_inited[name] = wrapper
        return wrapper

    return decorator


class BaseTask:
    def __init_subclass__(cls) -> None:
        if not hasattr(cls, 'name') or not isinstance(getattr(cls, 'name'), str):
            error('Task must have string parameter "name"')

        if not hasattr(cls, 'run') or not callable(getattr(cls, 'run')):
            error('Task must have method "run"')

        task(cls.name)(cls.run)

        super().__init_subclass__()


def run_cli():
    parser = argparse.ArgumentParser(description="calculate X to the power of Y")
    parser.add_argument("task_name")
    parser.add_argument("--params", required=False)
    args = parser.parse_args()

    try:
        params = dict() if args.params is None else json.loads(args.params)
    except json.decoder.JSONDecodeError:
        error('Invalid json string was passed as params')

    if args.task_name not in tasks_inited:
        error('Task "{}" does not exits'.format(args.task_name))

    print(tasks_inited[args.task_name](**params))


__all__ = ['task', 'BaseTask']
