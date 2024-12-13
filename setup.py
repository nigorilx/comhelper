from setuptools import setup, find_packages

setup(
    name="comhelper",
    version="1.0",
    packages=find_packages(),  # 自动查找包
    install_requires=[
        "requests",
        "questionary",
        "rich",
        "pyperclip",
    ],
    package_data={
        'comhelper': ['prompt.txt', 'prompt_check.txt', 'prompt_chat.txt'],  # 确保包含 comhelper 包内的文件
    },
    include_package_data=True,  # 让 setuptools 自动包括 package_data 中列出的文件
    entry_points={
        'console_scripts': [
            'comhelper = comhelper.comhelper:main',  # 设置入口点为 main 函数
        ],
    },
)
