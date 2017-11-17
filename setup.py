from setuptools import setup

setup(name='genTaskTime',
      version='0.1dev',
      description='Task timing from DSL',
      url='https://github.com/LabNeuroCogDevel/genTaskTime',
      author='Will Foran',
      author_email='WillForan+python@gmail.com',
      license='GPLv3',
      packages=['genTaskTime'],
      entry_points={
          'console_scripts': ['genTaskTime=genTaskTime:main'],
      },
      install_requires=[
          'anytree',
          'tatsu'
          ],
      zip_safe=False)
