import argparse
import json
import shutil
import sys
import os

from .exceptions import BadRequestException
from .orm import Base, init as orm_init
from .settings import init_settings, SETTINGS
from .task import run_command, Result


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

    result = run_command(args)

    if isinstance(result, Result):
        result_dir = args['result_dir'] or os.getcwd()

        if not os.path.isdir(result_dir):
            os.makedirs(result_dir)

        for file_data in result.files:
            try:
                shutil.move(file_data['tmp_path'], os.path.join(result_dir, file_data['name']))
            finally:
                del file_data['tmp_path']

    sys.stdout.write(str(result) + '\n')
