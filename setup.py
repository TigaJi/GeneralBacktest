from setuptools import setup

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='GeneralBacktest',
    url='https://github.com/TigaJi/GeneralBacktest',
    author='Dailin Ji',
    author_email='dj2194@nyu.edu',
    # Needed to actually package something
    packages=['GeneralBacktest'],
    # Needed for dependencies
    install_requires=['numpy','pandas','pydrive','oauth2client'],
    # *strongly* suggested for sharing
    version='0.1',
    # The license can be anything you like
    license='SUPR',
    description='A simple, realistic tool to backtest trading strategies.',
    long_description=open('README.md').read(),
)