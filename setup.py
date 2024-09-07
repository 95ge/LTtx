import sys
from setuptools import setup, find_packages

# 完整的 setup.py 配置
setup(
    name='LTtx',
    version='7.1.5',
    description='LTtx通信系统，更适合Python宝宝的通信组件，采用socket进行封装，另外封装了一些常用的函数，后续将不断更新',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='95ge',
    author_email='445646258@qq.com',
    url='https://github.com/95ge/LTtx',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,  # 确保安装包中包含配置文件
    package_data={
        'tx': ['Config.txt'],  # 明确指定 tx 包内的 Config.txt 文件
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.5',
    install_requires=[
        'pandas_market_calendars',
        'pyzmq',
        'requests',
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'LTtx_server=tx.LTtx_server:main',
        ],
    },
)
