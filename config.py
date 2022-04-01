from util.util import Utils
from typing import List
import yaml
import pathlib


class Config(object):
    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            try:
                with open(f"{Utils.get_project_root().joinpath(pathlib.PurePath('config.yaml'))}", "r") as in_yaml:
                    cls.yaml = yaml.load(in_yaml, Loader=yaml.FullLoader)
            except FileNotFoundError:
                cls.yaml = None
        return cls._instance

    def has_yaml(self) -> bool:
        return hasattr(self, 'yaml') and self.yaml is not None

    def get_admin_ids(self) -> List[int]:
        """Return a list of admin user IDs"""
        default = []
        if not self.has_yaml():
            return default
        elif 'admin' in self.yaml and 'admin_ids' in self.yaml['admin']:
            return self.yaml['admin']['admin_ids']
        return default
