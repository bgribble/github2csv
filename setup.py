

# build with 'python ./setup.py install' 
from setuptools import setup

setup (name = 'github2csv',
       version = '0.01',  
       description = '',
       py_modules = ['github2csv', 'review'],
       entry_points = { 'console_scripts': [ 'github2csv=github2csv:main', 
                                             'review2csv=review:main'] })


