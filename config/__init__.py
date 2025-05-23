#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :__init__.py
@说明    :
@时间    :2025/05/22 11:29:12
@作者    :ljw
@版本    :1.0
'''


import os
import sys
import logging
import logging.config as logging_config
import yaml


from tools.utils.utils import create_directory


class Config:
    '''配置信息'''

    # 项目目录
    if getattr(sys, "frozen", False):
        PROJ_PATH = os.path.normpath(os.path.join(
            sys.executable,
            os.pardir,  # 上一级目录(..)
        ))
    else:
        PROJ_PATH = os.path.normpath(os.path.join(
            os.path.abspath(__file__),
            os.pardir,  # 上一级目录(..)
            os.pardir,  # 上一级目录(..)
        ))

    # 配置目录
    CONFIG_DIR = os.path.join(PROJ_PATH, "config")
    STATIC_DIR = os.path.join(PROJ_PATH, "build")

    # 日志目录
    LOGS_DIR = os.path.join(PROJ_PATH, "logs")
    create_directory(LOGS_DIR)

    # 缓存目录
    TEMP_DIR:str = os.path.join(PROJ_PATH, "temp")
    create_directory(TEMP_DIR)

    # 日志配置
    LOGGING_DIC = {
        'version': 1,
        'disable_existing_loggers': False,
        # 日志输出格式
        'formatters': {
            'standard': {
                'format': "[%(levelname)s][%(asctime)s][%(threadName)s:%(thread)d][task_id:%(name)s][%(filename)s:%(lineno)d]"
                "[%(message)s]"
            },
            'simple': {
                'format': "[%(levelname)s] [%(asctime)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
        },
        'filters': {},
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                # 日志文件名
                'filename': os.path.join(LOGS_DIR, "logmind.log"),
                # 日志文件的最大值,这里设置15M
                'maxBytes': 1500 * 1024 * 1024,
                # 日志文件的数量,设置最大日志数量为10
                'backupCount': 1000,
                # 日志格式
                'formatter': 'standard',
                # 文件编码
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            'global': {
                'handlers': ["file"],
                'level': 'INFO',
                'propagate': False,  # 默认为True，向上（更高level的logger）传递，通常设置为False即可，否则会一份日志向上层层传递
            },
            'apscheduler.scheduler': {
                'handlers': ["file"],
                'level': 'ERROR',
                'propagate': False,  # 默认为True，向上（更高level的logger）传递，通常设置为False即可，否则会一份日志向上层层传递
            },
            '': {
                'handlers': ["file"],
                'level': 'INFO',
                'propagate': False,  # 默认为True，向上（更高level的logger）传递，通常设置为False即可，否则会一份日志向上层层传递
            }
        }
    }
    logging_config.dictConfig(LOGGING_DIC)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    logging.getLogger('apscheduler.executors.default').propagate = False
    log = logging.getLogger("global")

    # 项目配置
    PROJECE_CONFIG: dict = {
        "debug": False,
        "description": """## Logmind 
        Logmind 是一个基于 FastAPI 的日志分析平台，支持多种数据源的接入和分析。
        能够快速解析和分析日志数据，提供可视化的分析结果。并生成markdown格式的报告。""",
        "title": "Logmind",
        "version": "0.0.1"
    }

    # 启动配置
    STARTUP_CONFIG = {"host": "127.0.0.1", "port": 8878}
    DEBUG = True if sys.gettrace() else False
    config = "dev.yaml" if DEBUG else "prod.yaml"
    MONGOCONFIG = {"uri": "mongodb://192.168.174.136:27017",
                   "max_pool_size": 100,
                   "min_pool_size": 10,
                   "connect_timeout": 30000, 
                   }

    def __init__(self):
        with open(os.path.join(self.CONFIG_DIR, self.config), "r", encoding="utf_8_sig") as file:
            try:
                for key, value in yaml.safe_load(file).items():
                    setattr(self, key, value)
            except Exception:
                self.log.error("yaml配置文件格式不正确!")


setting = Config()
