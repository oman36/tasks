import copy
from multiprocessing import Process, Pool
from time import sleep

from gevent.pywsgi import WSGIServer

from .cli import run_cli
from .server import app as wsgi_app
from .task import BaseTask, task, Result, WebTask
from .orm import Task as TaskModel, session_factory, globals_sessions
from .settings import SETTINGS


def restart_task(task_obj):
    globals_sessions[0] = session_factory()
    globals_sessions[0].add(task_obj)
    task_obj.status = 'pending'
    globals_sessions[0].commit()

    WebTask(task_obj).run()


def restart_tasks():
    session = session_factory()
    pool_size = min(10, SETTINGS['limits']['global'])

    session.query(TaskModel).filter_by(status='pending').update({'status': 'new'})
    session.commit()

    pool = Pool(pool_size)
    queryset = session.query(TaskModel).filter_by(status='new').order_by('created_at')

    while True:
        exist_more = True
        offset = 0
        limits = copy.deepcopy(SETTINGS['limits']['names'])
        filtered = []
        current_queryset = queryset
        while exist_more and len(filtered) < pool_size:
            tasks = current_queryset[offset:offset + pool_size]
            offset += pool_size
            exist_more = len(tasks) == pool_size

            for current in tasks:
                if current.name in limits:
                    limits[current.name] -= 1

                    if limits[current.name] == 0:
                        current_queryset = current_queryset.filter(TaskModel.name != current.name)

                    if limits[current.name] < 0:
                        continue
                filtered.append(current)

        if len(filtered) == 0:
            sleep(5)
            continue

        pool.map(restart_task, filtered)


@task(name='runserver')
def run_server(host='', port=5000):
    Process(target=restart_tasks).start()
    http_server = WSGIServer((host, port), wsgi_app)
    http_server.serve_forever()


__all__ = ['task', 'BaseTask', 'run_cli', 'Result']
