from setuptools import setup, find_packages

setup(
    name="mighty-game",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,  # static, templates 폴더를 포함하기 위해 필요
    install_requires=[
        "flask",
        "flask-socketio",
        "eventlet",
    ],
    python_requires=">=3.7",
)
