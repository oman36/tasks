import json
import os

from flask import Flask
from flask import abort
from flask import jsonify
from flask import request
from flask import send_file

from .exceptions import TasksBaseException
from .orm import Task, session_factory, globals_sessions, row2dict, paginator
from .settings import SETTINGS
from .task import WebTask, check_limit, interpreted_task_list

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return send_file(os.path.join(SETTINGS['static_path'], 'index.html'))


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


@app.route('/static/<string:filename>', methods=['GET'])
def static_files(filename):
    return send_file(os.path.join(SETTINGS['static_path'], filename))


@app.route('/get_list_of_task_types', methods=['GET'])
def get_list_of_task_types():
    return jsonify([t.to_dict() for t in interpreted_task_list.tasks_inited.values()])


@app.route('/get_limits', methods=['GET'])
def get_limits():
    return jsonify(SETTINGS['limits'])


@app.route('/get_in_progress', methods=['GET'])
def in_progress():
    globals_sessions[0] = session_factory()
    queryset = globals_sessions[0].query(Task)\
        .filter(Task.status != 'finished')\
        .order_by(Task.status.desc(), Task.created_at)

    return jsonify([row2dict(t) for t in queryset])


@app.route('/get_completed', methods=['GET'])
def get_completed():
    globals_sessions[0] = session_factory()
    queryset = globals_sessions[0].query(Task)\
        .filter(Task.status == 'finished')\
        .order_by(Task.created_at.desc())

    def transformer(row):
        row = row2dict(row)

        if row['files']:
            row['files'] = [
                {'name': f, 'url': '{}files/{}/{}'.format(request.host_url, row['id'], f)}
                for f in json.loads(row['files'])
            ]
        return row

    return jsonify(paginator(
        queryset,
        int(request.args.get('page', 1)),
        transformer=transformer,
    ))
