import argparse
import datetime
import fnmatch
import functools
import hashlib
import inspect
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from typing import List

from .base import BaseObject
from .local_logging import get_logger
from .module_watcher import ModuleWatcher

logger = get_logger(__name__)


def alphabet_encode(number: int, alphabet='0123456789ABCDEFGHJKLMNPRSTUVWXYZ', padding: int = 0) -> str:
    """Converts an integer to a base|alphabet_length| string."""
    if not isinstance(number, int):
        raise TypeError('number must be an integer')

    number = abs(number)

    chunks: List[str] = []
    while number or len(chunks) < padding:
        chunks.append(alphabet[number % len(alphabet)])
        number = number // len(alphabet)
    return ''.join(reversed(chunks))


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
        instance = None
        for key in dir(class_):
            if key.startswith('_'):
                continue
            value = getattr(class_, key)
            if not hasattr(value, '__yaost_part__'):
                continue
            if instance is None:
                instance = class_()
            self.add_part(f'{class_.__name__}.{key}', getattr(instance, key))
        return class_

    def _get_class_that_defines_method(self, meth):
        if isinstance(meth, functools.partial):
            return self._get_class_that_defines_method(meth.func)

        if inspect.ismethod(meth) or (
            inspect.isbuiltin(meth)
            and getattr(meth, '__self__', None) is not None
            and getattr(meth.__self__, '__class__', None)
        ):
            for cls in inspect.getmro(meth.__self__.__class__):
                if meth.__name__ in cls.__dict__:
                    # NOTE we don't want to reconstruct class
                    # if it was counstructed outside
                    # return cls
                    return None
            meth = getattr(meth, '__func__', meth)

        if inspect.isfunction(meth):
            cls = getattr(
                inspect.getmodule(meth),
                meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0],
                None,
            )
            if isinstance(cls, type):
                return cls

        return getattr(meth, '__objclass__', None)

    def part(self, method):
        self.parts[method.__qualname__] = method
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

                # method = method_
                method = model
            self.parts[name_or_method] = method
        except:  # noqa
            logger.exception('failed to add model')
        return method

    def build_stl(self, args):
        self.build(args, stl_only=True)

    def iterate_parts(self):
        for name in sorted(self.parts):
            method_or_object = self.parts[name]
            try:
                cls = self._get_class_that_defines_method(method_or_object)

                if isinstance(method_or_object, BaseObject):
                    yield name, method_or_object
                elif cls is not None:
                    obj = cls()
                    model = method_or_object(obj)
                else:
                    model = method_or_object()

                yield name, model
            except:  # noqa
                logger.exception(f'failed to run model {name}')
                continue

    def build(self, args, stl_only=False):
        self.build_scad(args)
        cache = self._read_cache(args.cache_file)
        now_ts = datetime.datetime.now().strftime('%Y%d%m%H%M%S')
        if 'scad_cache' not in cache:
            cache['scad_cache'] = {}
        if 'projects' not in cache:
            cache['projects'] = {}

        if self.name not in cache['projects']:
            cache['projects'][self.name] = {}

        if 'version' not in cache['projects'][self.name]:
            cache['projects'][self.name]['version'] = 0

        version = cache['projects'][self.name]['version']

        if not os.path.exists(args.build_directory):
            os.makedirs(args.build_directory)

        for name, model in self.iterate_parts():
            if args.include and not fnmatch.fnmatch(name, args.include):
                continue

            scad_file_path = os.path.join(args.scad_directory, self.name, name + '.scad')

            extension = '.stl'
            if model.is_2d:
                extension = '.svg'
                if stl_only:
                    continue
            logger.info('building %s%s', name, extension)
            target_directory = args.build_directory
            if stl_only:
                target_directory = args.stl_directory

            result_file_path = os.path.join(target_directory, name + extension)

            cache_record = cache['scad_cache'].get(scad_file_path, {})
            if not isinstance(cache_record, dict):
                cache_record = {}
            scad_hash = self._get_files_hash(scad_file_path)
            if os.path.exists(result_file_path) and not args.force:
                build_hash = self._get_files_hash(result_file_path)
            else:
                build_hash = ''

            if cache_record.get('build_hash', '') == build_hash and cache_record.get('scad_hash', '') == scad_hash:
                continue

            command_args = [
                'openscad',
                scad_file_path,
                '-o',
                result_file_path,
                '-D',
                f'timestamp="{now_ts}"',
                '-D',
                f'hash="{scad_hash[:8]}"',
                '-D',
                f'version="{version:06d}"',
                '-D',
                f'mark="{version}."',
                '-D',
                f'cmark="{alphabet_encode(version, padding=2)}"',
            ]
            subprocess.call(command_args, shell=False)

            build_hash = self._get_files_hash(result_file_path)
            cache['scad_cache'][scad_file_path] = {
                'scad_hash': scad_hash,
                'build_hash': build_hash,
                'version': version + 1,
            }
            cache['projects'][self.name]['version'] = version + 1
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
                fp.write('timestamp="0000-00-00T00:00:00";\n')
                fp.write('hash="00000000";\n')
                fp.write('version="000000";\n')
                fp.write('mark="000.";\n')
                fp.write('cmark="00";\n')
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
                    '--scad-directory',
                    args.scad_directory,
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
            with open(cache_file) as fp:
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
            '--scad-directory',
            type=str,
            help='directory to store .scad files',
            default='scad',
        )
        parser.add_argument(
            '--stl-directory',
            type=str,
            help='directory to store .stl files',
            default='stl',
        )
        parser.add_argument(
            '--build-directory',
            type=str,
            help='directory to store result files',
            default='build',
        )
        parser.add_argument(
            '--cache-file',
            type=str,
            help='file to store some cahces',
            default='.yaost.cache',
        )
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
        build_parser.add_argument('--include', type=str, help='regex to build specified models only', default='')
        build_parser.set_defaults(func=self.build)

        args = parser.parse_args()

        loglevel = logging.INFO
        if args.debug:
            loglevel = logging.DEBUG
        logging.basicConfig(level=loglevel, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        args.func(args)
