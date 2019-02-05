#!/usr/bin/env python

import pyinotify
import os
from .packagefinder import PackageFinder


class ModuleWatcher(pyinotify.ProcessEvent):
    """
    Automatically reload any modules or packages as they change
    """

    def __init__(self, script_path, callback=None):
        "El constructor"

        self.wm = pyinotify.WatchManager()
        self.notifier = None

        pf = PackageFinder()
        self._callback = callback
        self._files = set(pf.get_files_list(script_path))
        self._directories = set()
        for filename in self._files:
            if not os.path.exists(filename):
                continue
            dirname = os.path.dirname(filename.rstrip('/'))
            self._directories.add(dirname)

        for dirname in self._directories:
            self.wm.add_watch(dirname, pyinotify.ALL_EVENTS)

    def start_watching(self):
        "Start the pyinotify watch thread"

        if self.notifier is None:
            self.notifier = pyinotify.ThreadedNotifier(self.wm, self)
        self.notifier.start()

    def stop_watching(self):
        "Stop the pyinotify watch thread"

        if self.notifier is not None:
            self.notifier.stop()

    def process_IN_MODIFY(self, event):
        "A file of interest has changed"

        # Is it a file I know about?
        if event.pathname not in self._files:
            return
        if self._callback is not None:
            getattr(self, '_callback')(event.pathname)
