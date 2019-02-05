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

    def __init__(self, name='Untitled', fa=3.0, fs=0.5):
        self._fa = fa
        self._fs = fs
        self.name = name
        self.parts = {}

    def add_part(self, name_or_method, model=None):
        method = None
        try:
            if callable(name_or_method):
                method = name_or_method
                name_or_method = name_or_method.__name__.lower().replace('_', '-')
                model = method()
            self.parts[name_or_method] = model
        except:  # noqa
            logger.exception("failed to add model")
            pass
        return method

    def get_part(self, name):
        return self.parts[name]

    def build_stl(self, args):
        self.build_scad(args)
        cache = self._read_cache(args.cache_file)
        if 'scad_cache' not in cache:
            cache['scad_cache'] = {}

        if not os.path.exists(args.stl_directory):
            os.makedirs(args.stl_directory)

        for name, _ in self.parts.items():
            logger.info('building %s.stl', name)
            scad_file_path = os.path.join(args.scad_directory, name + '.scad')
            stl_file_path = os.path.join(args.stl_directory, name + '.stl')

            if os.path.exists(stl_file_path) and not args.force:
                hc = self._get_files_hash(scad_file_path, stl_file_path)
                if cache['scad_cache'].get(scad_file_path, '') == hc:
                    continue

            command_args = [
                'openscad',
                scad_file_path,
                '-o', stl_file_path,
            ]
            subprocess.call(command_args, shell=False)
            hc = self._get_files_hash(scad_file_path, stl_file_path)
            cache['scad_cache'][scad_file_path] = hc
        self._write_cache(args.cache_file, cache)

    def build_scad(self, args):
        if not os.path.exists(args.scad_directory):
            os.makedirs(args.scad_directory)

        for name, model in self.parts.items():
            logger.info('building %s.scad', name)
            file_path = os.path.join(args.scad_directory, name + '.scad')
            with open(file_path, 'w') as fp:
                fp.write('$fa={:.4f};\n$fs={:.4f};\n'.format(self._fa, self._fs))
                fp.write(model.to_string())

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
            return uuid.uuid4()

    def run(self):
        if Project._single_run_guard:
            return
        Project._single_run_guard = True

        parser = argparse.ArgumentParser(sys.argv[0])
        parser.add_argument('--scad-directory', type=str, help='directory to store .scad files', default='scad')
        parser.add_argument('--stl-directory', type=str, help='directory to store .stl files', default='stl')
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

        args = parser.parse_args()

        loglevel = logging.INFO
        if args.debug:
            loglevel = logging.DEBUG
        logging.basicConfig(level=loglevel, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        args.func(args)
