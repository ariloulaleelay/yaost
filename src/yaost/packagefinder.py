import os
from types import ModuleType
from importlib import import_module


# TODO make this function work with any python
# currently working wity python >= 3.5
def import_from_file(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('__not_main__', path)
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return foo


class PackageFinder(object):

    def _find_required_modules(self, module, processed_modules=None):
        if module.__name__ in ('__builtin__', '__future__'):
            return

        if processed_modules is None:
            processed_modules = set()

        if module in processed_modules:
            return processed_modules

        processed_modules.add(module)
        names = dir(module)
        for name in names:
            if name[0] == '_':
                continue
            obj = getattr(module, name)
            if isinstance(obj, ModuleType):
                self._find_required_modules(obj, processed_modules)
            elif hasattr(obj, '__module__') and obj.__module__ is not None:
                # in case of 'import somename from somemodule'
                # somename will be in globals and somemodule not
                # to get somemodule we need to get somename.__module__
                try:
                    obj = import_module(obj.__module__)
                    self._find_required_modules(obj, processed_modules)
                except ImportError:
                    pass

        return processed_modules

    def get_files_list(self, script_path):
        script_path = os.path.abspath(script_path)
        module = import_from_file(script_path)
        modules = self._find_required_modules(module)
        files = set()
        for module in modules:
            if not hasattr(module, '__file__') or module.__file__ == '':
                continue
            files.add(os.path.abspath(module.__file__))
        return list(files)
