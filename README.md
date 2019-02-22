## Система отложенного запуска задач
### Общее описание
#### Описание задачи
Код для задач должен оформляться в виде функции (с использованием декоратора) или через наследование базового класса (необходимо реализовать оба варианта описания задачи).

Пример:
```python
# file: my_tasks.py
import tasks


@tasks.task(name='multiprint')
def multi_print(msg, count=10):
    return '\n'.join(msg for _ in xrange(count))

class Multiply(tasks.BaseTask):
    name = 'mult'

    def run(operands):
        return reduce(lambda x, y: x*y, operands)


if __name__ == '__main__':
    tasks.run_cli()
```

Пример запуска задач через командную строку
```bash
$ python my_tasks.py multiprint --params '{"msg": "hello", "count": 2}'
hello
hello
$ python my_tasks.py mult --params '{"operands": [3, 2, 8]}'
48
```

#### Валидация параметров
Есть возможность добавить валидацию входных параметров с использованием json-schema

```python
@tasks.task(name='multiprint',
            json_schema={'type': 'object',
                         'properties': {
                             'msg': {'type': 'string'},
                             'count': {'type': 'integer', 'minimum': 1}
                         },
                         'required': ['msg']})
def multi_print(msg, count=1):
    return '\n'.join(msg for _ in xrange(count))


class Multiply(BaseTask):
    name = 'mult'
    json_schema = {'type': 'object',
                   'properties': {
                       'operands': {'type': 'array',
                                    'minItems': '1',
                                    'items': {'type': 'number'}}
                    },
                    'required': ['operands']}

    def run(operands):
        return reduce(lambda x, y: x*y, operands)
```

Для валидации используется модуль: [jsonschema](https://pypi.org/project/jsonschema/)

#### HTTP Json API
Есть возможность запустить сервер, который слушает HTTP соединения и принимает POST запросы, где в теле описано какую задачу запускать и с какими параметрами.
Запрос должен иметь вид:
```json
{
  "task_name": "multiprint",
  "params": {"msg": "hello", "count": 2}
}
```

результат приходит в ответе в json формате:

```json
{
  "result": "hello\nhello"
}
```

в случае ошибки сервер сообщает об этом:
```json
{
  "status": "ERROR",
  "error_code": 100,
  "error_msg": "some message"
}
```

Запуск сервера:
```bash
$ python my_tasks.py runserver
```

Таким образом в режиме сервера могут выполняться сразу несколько задач.
При выключении сервера запоминается состояние и если какие-то из задач не успели выполниться, то они перезапускаются.
Параметры подключения к базе данных хранится в отдельном файле с конфигурацией.
```json
{
  "db": {
    "url" :"sqlite+pysqlite:///file.db",
  }
}
```

#### Отправка результата по почте
Если в запросе указан ключ `email`, то результат необходимо отправить на указанный email.
```json
{
  "task_name": "multiprint",
  "params": {"msg": "hello", "count": 3},
  "email": "example@domain.com"
}
```

Если задача принята (т.е. указан правильный тип задачи и параметры проходят валидацию) сервер ответит (не дожидаясь окончания выполнения задачи):
```json
{
  "status": "OK"
}
```

При успешном завершении задачи результат будет написан в теле письма:
```
hello
hello
hello
```

#### Возможность прикреплять файлы к результату

Пример описания задачи:
```python
@tasks.task(name='get_statistics')
def get_statistics():
    prepare_stats_file('/tmp/stats.tsv')

    with open('/tmp/stats.tsv') as fd:
        return tasks.Result(
            msg='Complete statistics',
            files=[
                {'name': 'statistics.tsv', 'data': fd}
            ]
        )
```
в секции с файлами в `data` необходимо передавать file-like объект.

При запуске из командной строки файлы будут сохранены в текущей директории.
Также есть возможность указать в какой директории сохранять результаты:

```bash
$ python my_tasks.py multiprint --result-dir /path/to/results/
Complete statistics
```
При запуске через http api без почты результаты будут в виде ссылок по которым можно скачать файлы.
```json
{
  "result": "some result",
  "files": [
    {"name": "statistics.tsv", "url": "http://example.com/results/8"}
  ]
}
```

При запуске через http api с указанием почты прикрепляются к письму.

#### Квотирование
Есть возможность ограничить количество одновременно запущенных задач при работе сервера (в конфиге на момент старта):
```json
{
  "limits": {
    "global": 15,
    "names": {
      "some_task": 4
    }
  }
}
```

* глобально - общее количество одновременно запущенных задач
* по названию задачи - количество одновременно запущенных задач с определенным типом (названием)

Остальные задачи вставают в очередь.

#### Web-интерфейс
Web-интерфейсе работает на порту 5000 и в нём можно посмотреть:
* список зарегистрированных типов задач и их ограничения на количество одновременных запусков (если имеются);
* список запущенных задач;
* список завершенных задач со статусом и результатами.
Так же есть форма в web-интерфейсе, где можно выбрать тип задачи, указать json-параметры строкой (как в cli) и запустить ее.

#### Автоматическая форма работает в тестовом режиме
Парсит json-схему для создания форм создания задач с полями (с правильными типами).