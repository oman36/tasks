from gevent.pywsgi import WSGIServer

from .cli import run_cli
from .server import app as wsgi_app
from .task import BaseTask, task, run_command


@task(name='runserver')
def run_server(host='', port=5000):
    http_server = WSGIServer((host, port), wsgi_app)
    http_server.serve_forever()


__all__ = ['task', 'BaseTask', 'run_cli']
