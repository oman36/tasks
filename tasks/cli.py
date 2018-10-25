import argparse
import json
import sys

from .exceptions import BadRequestException
from .task import run_command


def run_cli():
    parser = argparse.ArgumentParser(description="calculate X to the power of Y")
    parser.add_argument("task_name")
    parser.add_argument("--params", required=False)
    args = vars(parser.parse_args())

    try:
        args['params'] = json.loads(args.get('params') or '{}')
    except json.decoder.JSONDecodeError:
        raise BadRequestException('Invalid json string was passed as params')
    sys.stdout.write(str(run_command(args)) + '\n')
