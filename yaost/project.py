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


class Project:
    _single_run_guard = False

    def __init__(
        self,
        name='Untitled',
        fa=3.0,
        fs=0.5,
        fn=None,
    ):
        self._fa = fa
        self._fs = fs
        self._fn = fn
        self.name = name
        self.parts = {}

    def add_class(self, class_):
        obj = class_()
        for key in dir(class_):
            value = getattr(class_, key, None)
            if not getattr(value, '__yaost_part__', False):
                continue
            name = class_.__name__ + '.' + value.__name__
            self.parts[name] = getattr(obj, key)
        return class_

    def part(self, method):
        method.__yaost_part__ = True
        return method

    def add_part(self, name_or_method, model=None):
        method = None
        try:
            if callable(name_or_method):
                method = name_or_method
                name_or_method = method.__name__.replace('_', '-')
            else:
                def method_():
                    return model
                method = method_
            self.parts[name_or_method] = method
        except:  # noqa
            logger.exception('failed to add model')
        return method

    def build_stl(self, args):
        self.build(args, stl_only=True)

    def iterate_parts(self):
        for name in sorted(self.parts):
            method = self.parts[name]
            try:
                model = method()
            except: # noqa
                logger.exception(f'failed to run model {name}')
                continue
            yield name, model

    def build(self, args, stl_only=False):
        self.build_scad(args)
        cache = self._read_cache(args.cache_file)
        if 'scad_cache' not in cache:
            cache['scad_cache'] = {}

        if not os.path.exists(args.build_directory):
            os.makedirs(args.build_directory)

        for name, model in self.iterate_parts():
            scad_file_path = os.path.join(args.scad_directory, self.name, name + '.scad')

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
        for name, model in self.iterate_parts():
            file_path = os.path.join(args.scad_directory, self.name, name + '.scad')
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as fp:
                for key in ('fa', 'fs', 'fn'):
                    value = getattr(self, f'_{key}', None)
                    if value is not None:
                        fp.write(f'${key}={value:.6f};\n')
                scad_code = model.to_scad()
                fp.write(scad_code)
                fp.write('\n')
        logger.info('scad build done')

    def watch(self, args):
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
            with open(cache_file, 'w', encoding='utf-8') as fp:
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
                with open(filename, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):  # noqa
                        h.update(chunk)
            return h.hexdigest()
        except Exception as e:  # noqa
            logger.error('hashing gone wrong %s %s', filename, e)
            return str(uuid.uuid4())

    def run(self):
        if Project._single_run_guard:
            return
        Project._single_run_guard = True

        parser = argparse.ArgumentParser(sys.argv[0])
        parser.add_argument(
            '--scad-directory', type=str, help='directory to store .scad files', default='scad'
        )
        parser.add_argument(
            '--stl-directory', type=str, help='directory to store .stl files', default='stl'
        )
        parser.add_argument(
            '--build-directory', type=str, help='directory to store result files', default='build'
        )
        parser.add_argument(
            '--cache-file', type=str, help='file to store some cahces', default='.yaost.cache'
        )
        parser.add_argument(
            '--force', action='store_true', help='force action', default=False
        )
        parser.add_argument(
            '--debug', action='store_true', help='enable debug output', default=False
        )
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
        logging.basicConfig(
            level=loglevel, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        args.func(args)
