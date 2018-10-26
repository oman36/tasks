from setuptools import setup

setup(name='tasks',
    version='0.4',
    description='Manager for delayed tasks',
    url='http://github.com/oman36/tasks',
    author='Petrov Vladimir',
    author_email='neoman36@gmail.com',
    license='MIT',
    packages=['tasks'],
    install_requires=[
        'jsonschema==2.6.0',
        'Flask==1.0.2',
        'gevent==1.3.7',
        'SQLAlchemy==1.2.12',
        'alembic==1.0.1',
    ],
    zip_safe=False)
