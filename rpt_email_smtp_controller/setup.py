from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='rpt_email_smtp_controller',
    version='0.1',
    description='custom alert email subject',
    long_description=readme(),
    url='',
    author='renzhang',
    author_email='renzhang@freewheel.tv',
    license='MIT',
    packages=['rpt_email_smtp_controller'],
    test_suite='nose.collector',
    tests_require=['nose'],
    install_requires=[
        'airflow==1.8.0'
    ],
    zip_safe=False
)
