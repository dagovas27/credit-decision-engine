import importlib

import credit_engine

LAYERS = ["schemas", "bronze", "silver", "gold", "ml", "decision", "monitoring"]


def test_package_has_version():
    assert credit_engine.__version__ == "0.1.0"


def test_all_layer_packages_import():
    for layer in LAYERS:
        importlib.import_module(f"credit_engine.{layer}")
