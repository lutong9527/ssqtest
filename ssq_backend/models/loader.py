# models/loader.py

import os
import importlib
import pkgutil


def load_models():
    """
    自动扫描 models 目录并导入所有模型文件
    """

    package_dir = os.path.dirname(__file__)
    package_name = os.path.basename(package_dir)

    for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):

        if is_pkg:
            continue

        # 跳过基础文件
        if module_name in ["base", "registry", "loader", "__init__"]:
            continue

        importlib.import_module(f"{package_name}.{module_name}")
