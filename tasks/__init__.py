from multiprocessing import Process, Pool
import json

from gevent.pywsgi import WSGIServer

from .cli import run_cli
from .server import app as wsgi_app
from .task import BaseTask, task, run_command
from .orm import Task, Session


def restart_task(task_obj: Task):
    run_command({
        'task_name': task_obj.name,
        'params': json.loads(task_obj.params),
    }, task_obj)


def restart_tasks():
    session = Session()
    pool = Pool(10)
    while True:
        tasks = session.query(Task).filter_by(status='new')[0:10]
        if len(tasks) == 0:
            break
        pool.map(restart_task, tasks)


@task(name='runserver')
def run_server(host='', port=5000):
    Process(target=restart_tasks).start()
    http_server = WSGIServer((host, port), wsgi_app)
    http_server.serve_forever()


__all__ = ['task', 'BaseTask', 'run_cli']
