import importlib

from django.db.backends.base.base import BaseDatabaseWrapper


class DatabasePatcher:
    @staticmethod
    def patch(database: BaseDatabaseWrapper) -> (bool, object):
        module_dict = {
            'caretaker.frontend.frontends.database_exporters.django.sqlite':
                'SQLiteDatabaseExporter'
        }

        for module_name, class_name in module_dict.items():
            # load the modules to see if we find a match
            module = importlib.import_module(module_name)
            class_ref = getattr(module, class_name)
            patcher = class_ref()

            # patch the underlying module
            if patcher.patch(database):
                return True, patcher

        return False, None

    @staticmethod
    def can_handle(database: BaseDatabaseWrapper, patcher) -> bool:
        return patcher.handles in database.settings_dict['ENGINE']
