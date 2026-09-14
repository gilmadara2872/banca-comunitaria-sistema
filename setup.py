from setuptools import setup

setup(
    name='banca-app',
    version='1.0.0',
    packages=[],
    install_requires=[
        'Flask==2.3.3',
        'Flask-CORS==3.0.10',
        'gunicorn==20.1.0',
    ],
    entry_points={
        'console_scripts': [
            'banca-app=run:main',
        ],
    },
)
