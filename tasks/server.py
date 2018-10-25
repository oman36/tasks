from flask import Flask
from flask import jsonify
from flask import request

from .task import run_command
from .exceptions import TasksBaseException

app = Flask(__name__)


@app.route('/', methods=['POST'])
def hello_world():
    try:
        result = run_command(request.json)
    except TasksBaseException as er:
        return jsonify({
            'status': 'ERROR',
            'error_code': er.get_code(),
            'error_msg': er.get_message(),
        })

    return jsonify({
        'result': result,
    })