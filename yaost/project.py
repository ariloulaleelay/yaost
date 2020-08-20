import os
import sys
import time
import inspect
import argparse
import subprocess
import logging
import json
import uuid
import hashlib
from .module_watcher import ModuleWatcher
from .local_logging import get_logger

logger = get_logger(__name__)


class Project(object):
    _single_run_guard = False

    def __init__(self, name='Untitled', fa=3.0, fs=0.5, fn=None):
        self._fa = fa
        self._fs = fs
        self._fn = fn
        self.name = name
        self.parts = {}

    def add_part(self, name_or_method, model=None):
        method = None
        try:
            if callable(name_or_method):
                method = name_or_method
                name_or_method = name_or_method.__name__.lower().replace('_', '-')
                model = method()
                if not model.kwargs.get('_module_name'):
                    model = model.module_name(method.__name__)
            self.parts[name_or_method] = model
        except:  # noqa
            logger.exception("failed to add model")
        return method

    def get_part(self, name):
        return self.parts[name]

    def build_stl(self, args):
        self.build(args, stl_only=True)

    def build(self, args, stl_only=False):
        self.build_scad(args)
        cache = self._read_cache(args.cache_file)
        if 'scad_cache' not in cache:
            cache['scad_cache'] = {}

        if not os.path.exists(args.build_directory):
            os.makedirs(args.build_directory)

        for name, model in self.parts.items():
            scad_file_path = os.path.join(args.scad_directory, name + '.scad')

            extension = '.stl'
            if model.is_2d:
                extension = '.dxf'
                if stl_only:
                    continue
            logger.info('building %s%s', name, extension)
            target_directory = args.build_directory
            if stl_only:
                target_directory = args.stl_directory

            result_file_path = os.path.join(target_directory, name + extension)

            if os.path.exists(result_file_path) and not args.force:
                hc = self._get_files_hash(scad_file_path, result_file_path)
                if cache['scad_cache'].get(scad_file_path, '') == hc:
                    continue

            command_args = [
                'openscad',
                scad_file_path,
                '-o', result_file_path,
            ]
            subprocess.call(command_args, shell=False)
            hc = self._get_files_hash(scad_file_path, result_file_path)
            cache['scad_cache'][scad_file_path] = hc
        self._write_cache(args.cache_file, cache)

    def build_scad(self, args):
        if not os.path.exists(args.scad_directory):
            os.makedirs(args.scad_directory)

        for name, model in self.parts.items():
            logger.info('building %s.scad', name)
            file_path = os.path.join(args.scad_directory, name + '.scad')
            with open(file_path, 'w') as fp:
                for key in ('fa', 'fs', 'fn'):
                    value = getattr(self, '_{}'.format(key), None)
                    if value is not None:
                        fp.write('${}={:.4f};\n'.format(key, value))
                cache = {}
                node_index = 0
                for node in model.traverse_children_deep_first():
                    node_string = node.to_string(cache=cache)
                    if node.depth > 1 and node.id not in cache:
                        node_index += 1
                        module_name = node.kwargs.get('_module_name', '')
                        if module_name:
                            module_name = 'n{}_{}'.format(node_index, module_name)
                        else:
                            module_name = 'n{}'.format(node_index)
                        fp.write('module {}(){{{}}} // {}\n'.format(
                            module_name, node_string, node.id
                        ))
                        cache[node.id] = '{}();'.format(module_name)
                fp.write(model.to_string(cache=cache))

    def watch(self, args):
        try:
            import __main__

            def build_scad_generator(args, script_path):
                def real_scad_generator(*args_array, **kwargs_hash):
                    command_args = [
                        __main__.__file__,
                        '--scad-directory', args.scad_directory,
                    ]
                    if args.debug:
                        command_args.append('--debug')
                    command_args.append('build-scad')
                    try:
                        subprocess.call(command_args, shell=False)
                    except OSError:
                        time.sleep(0.1)
                        subprocess.call(command_args, shell=False)

                return real_scad_generator
            callback = build_scad_generator(args, __main__.__file__)
            mw = ModuleWatcher(__main__.__file__, callback)
            try:
                callback()
                mw.start_watching()
                while True:
                    time.sleep(0.1)
            finally:
                mw.stop_watching()
        except ImportError:
            raise

    def _get_caller_module_name(self, depth=1):
        frm = inspect.stack()[depth + 1]
        mod = inspect.getmodule(frm[0])
        return mod.__name__

    def _read_cache(self, cache_file):
        result = {}
        if not os.path.exists(cache_file):
            return {}
        try:
            with open(cache_file, 'r') as fp:
                result = json.load(fp)
        except:  # noqa
            logger.error('reading cache failed', exc_info=True)
            result = {}
        return result

    def _write_cache(self, cache_file, cache):
        try:
            with open(cache_file, 'w') as fp:
                json.dump(cache, fp, ensure_ascii=False)
        except:  # noqa
            logger.error('writing cache failed', exc_info=True)
            return
        return

    def _get_files_hash(self, *filenames):
        try:
            h = hashlib.sha256()
            for filename in filenames:
                h.update(b'\0\0\0\1\0\0')
                with open(filename, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):  # noqa
                        h.update(chunk)
            return h.hexdigest()
        except Exception as e:  # noqa
            logger.error("hashing gone wrong %s %s", filename, e)
            return str(uuid.uuid4())

    def run(self):
        if Project._single_run_guard:
            return
        Project._single_run_guard = True

        parser = argparse.ArgumentParser(sys.argv[0])
        parser.add_argument('--scad-directory', type=str, help='directory to store .scad files', default='scad')
        parser.add_argument('--stl-directory', type=str, help='directory to store .stl files', default='stl')
        parser.add_argument('--build-directory', type=str, help='directory to store result files', default='build')
        parser.add_argument('--cache-file', type=str, help='file to store some cahces', default='.yaost.cache')
        parser.add_argument('--force', action='store_true', help='force action', default=False)
        parser.add_argument('--debug', action='store_true', help='enable debug output', default=False)
        parser.set_defaults(func=lambda args: parser.print_help())
        subparsers = parser.add_subparsers(help='sub command help')

        watch_parser = subparsers.add_parser('watch', help='watch project and rebuild scad files')
        watch_parser.set_defaults(func=self.watch)

        build_scad_parser = subparsers.add_parser('build-scad', help='build scad files')
        build_scad_parser.set_defaults(func=self.build_scad)

        build_stl_parser = subparsers.add_parser('build-stl', help='build scad and stl files')
        build_stl_parser.set_defaults(func=self.build_stl)

        build_parser = subparsers.add_parser('build', help='build all files')
        build_parser.set_defaults(func=self.build)

        args = parser.parse_args()

        loglevel = logging.INFO
        if args.debug:
            loglevel = logging.DEBUG
        logging.basicConfig(level=loglevel, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        args.func(args)
