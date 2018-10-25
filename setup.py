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
            'jsonschema',
            'flask',
            'gevent',
      ],
      zip_safe=False)