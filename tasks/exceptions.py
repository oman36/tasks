import sys


class TasksBaseException(BaseException):
    code = 0

    def __init__(self, message):
        self.message = message

    def get_code(self):
        return self.code

    def get_message(self):
        return self.message

    def __str__(self):
        return f'[{self.code}] {self.message}'


class FatalException(TasksBaseException):
    code = 500

    def __init__(self, message):
        sys.stderr.write('Fatal error: ' + message + '\n')
        super().__init__('Server error')


class TaskNotExistException(TasksBaseException):
    code = 404

    def __init__(self, task_name):
        super().__init__('Task "{}" does not exits'.format(task_name))


class BadRequestException(TasksBaseException):
    code = 400


class TaskLimitException(TasksBaseException):
    code = 502
