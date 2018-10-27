import json
import os

from flask import Flask
from flask import abort
from flask import jsonify
from flask import request
from flask import send_file

from .exceptions import TasksBaseException
from .orm import Task, session_factory, globals_sessions
from .settings import SETTINGS
from .task import WebTask, check_limit

app = Flask(__name__)


@app.route('/', methods=['POST'])
def run_task():
    globals_sessions[0] = session_factory()

    data = request.json
    try:
        web_task = WebTask(
            data['task_name'],
            params=data['params'],
            email=data.get('email'),
        )

        check_limit(web_task.task_name)

        result = web_task.run()

    except TasksBaseException as er:
        return jsonify({
            'status': 'ERROR',
            'error_code': er.get_code(),
            'error_msg': er.get_message(),
        })

    if 'email' in data:
        return jsonify({
            'status': 'ok',
        })

    response = {
        'result': str(result),
    }

    if web_task.model.files:
        response['files'] = [{
                'name': file_name,
                'url': f'{request.host_url}files/{web_task.model.id}/{file_name}',
            } for file_name in json.loads(web_task.model.files)]

    return jsonify(response)


@app.route('/files/<int:task_id>/<string:filename>', methods=['GET'])
def files(task_id, filename):
    task_from_db = session_factory().query(Task).get(task_id)

    if task_from_db is None or filename not in json.loads(task_from_db.files or '[]'):
        abort(404)

    return send_file(os.path.join(SETTINGS['files']['web_dir'], str(task_id), filename))
