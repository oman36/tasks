from setuptools import setup

setup(name='tasks',
      version='0.2',
      description='Manager for delayed tasks',
      url='http://github.com/oman36/tasks',
      author='Petrov Vladimir',
      author_email='neoman36@gmail.com',
      license='MIT',
      packages=['tasks'],
      install_requires=[
            'jsonschema',
      ],
      zip_safe=False)