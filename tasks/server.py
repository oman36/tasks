import json
import os
import shutil

from flask import Flask
from flask import jsonify
from flask import request
from flask import send_file
from flask import abort

from .email import send_email
from .exceptions import TasksBaseException
from .orm import Task, Session
from .settings import SETTINGS
from .task import run_command, Result

app = Flask(__name__)


@app.route('/', methods=['POST'])
def run_task():
    data = request.json
    try:
        task_in_db = Task(
            name=data['task_name'],
            params=json.dumps(data['params']),
            status='new',
        ) if not 'email' in data else None

        result = run_command(data, task_in_db=task_in_db)
    except TasksBaseException as er:
        return jsonify({
            'status': 'ERROR',
            'error_code': er.get_code(),
            'error_msg': er.get_message(),
        })

    if 'email' in data:
        send_email(
            [data['email']],
            'Task {} was completed.'.format(data['task_name']),
            str(result),
            result.files if isinstance(result, Result) else []
        )

        return jsonify({
            'status': 'ok',
        })

    response = {
        'result': str(result),
    }

    if isinstance(result, Result):
        session = Session()
        session.add(task_in_db)
        result_dir = os.path.join(SETTINGS['files']['web_dir'], str(task_in_db.id))
        response['files'] = []

        if not os.path.isdir(result_dir):
            os.makedirs(result_dir)

        for file_data in result.files:
            file_name = file_data['name']
            shutil.move(file_data['tmp_path'], os.path.join(result_dir, file_name))

            response['files'].append({
                'name': file_name,
                'url': f'{request.host_url}files/{task_in_db.id}/{file_name}',
            })

        task_in_db.files = json.dumps(response['files'])
        session.commit()

    response['files'] = result.files

    return jsonify(response)


@app.route('/files/<int:task_id>/<string:filename>', methods=['GET'])
def files(task_id, filename):
    session = Session()
    task_in_db = session.query(Task).get(task_id)
    for file in json.loads(task_in_db.files or '[]'):
        if file['name'] != filename:
            continue
        return send_file(os.path.join(SETTINGS['files']['web_dir'], str(task_in_db.id), filename))

    abort(404)
