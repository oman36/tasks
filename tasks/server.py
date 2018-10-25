from flask import Flask
from flask import jsonify
from flask import request

from .task import run_command
from .exceptions import TasksBaseException
from .email import send_email

app = Flask(__name__)


@app.route('/', methods=['POST'])
def hello_world():
    data = request.json
    try:
        result = run_command(data)
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
            result,
        )

    return jsonify({
        'result': result,
    })
