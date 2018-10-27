from multiprocessing import Process, Pool

from gevent.pywsgi import WSGIServer

from .cli import run_cli
from .server import app as wsgi_app
from .task import BaseTask, task, Result, WebTask
from .orm import Task as TaskModel, session_factory, globals_sessions


def restart_task(task_obj):
    globals_sessions[0] = session_factory()
    WebTask(task_obj).run()


def restart_tasks():
    session = session_factory()
    pool = Pool(10)
    while True:
        tasks = session.query(TaskModel).filter_by(status='new')[0:10]
        if len(tasks) == 0:
            break

        pool.map(restart_task, tasks)


@task(name='runserver')
def run_server(host='', port=5000):
    Process(target=restart_tasks).start()
    http_server = WSGIServer((host, port), wsgi_app)
    http_server.serve_forever()


__all__ = ['task', 'BaseTask', 'run_cli', 'Result']
