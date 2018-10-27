import argparse
import json
import sys

from .exceptions import BadRequestException
from .orm import Base, init as orm_init
from .settings import init_settings, SETTINGS
from .task import Task


def run_cli(settings_file):
    init_settings(settings_file)
    engine = orm_init(SETTINGS['db'])

    Base.metadata.create_all(engine)

    parser = argparse.ArgumentParser(description="calculate X to the power of Y")
    parser.add_argument("task_name")
    parser.add_argument("--params", required=False)
    parser.add_argument("--result-dir", required=False)
    args = vars(parser.parse_args())

    try:
        args['params'] = json.loads(args.get('params') or '{}')
    except json.decoder.JSONDecodeError:
        raise BadRequestException('Invalid json string was passed as params')

    result = Task(args['task_name'], args['params'], result_dir=args['result_dir']).run()

    sys.stdout.write(str(result) + '\n')
