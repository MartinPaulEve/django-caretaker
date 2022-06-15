import importlib
import types


class PluginLoader(type):
    @staticmethod
    def patch(database):
        module_dict = {
            'caretaker.frontend.frontends.database_exporters.django.sqlite':
                'SQLiteDatabaseExporter'
        }
        modules = []

        for module_name, class_name in module_dict.items():
            module = __import__(module_name)
            class_ref = getattr(module, class_name)
            patcher = class_ref()
            patcher.patch(databases)
