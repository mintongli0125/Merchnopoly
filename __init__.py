from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from typing import Any
import __main__
_object = object

def update_path():
    import sys
    import os.path

    name = sys._getframe(1).f_globals["__name__"]
    package = sys.modules[name]
    name = name.split(".")

    try:
        import _renpy
        if hasattr(_renpy, '__file__') and _renpy.__file__ != "built-in":
            libexec = os.path.dirname(_renpy.__file__)
            package.__path__.append(os.path.join(libexec, *name))
    except ImportError:
        return

from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode

update_path()

import renpy.compat.pickle as pickle
import sys
import os
import copy
import types
import site
from collections import namedtuple

################################################################################ Version

try:
    from renpy.vc_version import official, nightly, version_name, version
except ImportError:
    import renpy.versions
    version_dict = renpy.versions.get_version()

    official = version_dict["official"]
    nightly = version_dict["nightly"]
    version_name = version_dict["version_name"]
    version = version_dict["version"]

official = official and getattr(site, "renpy_build_official", False)
VersionTuple = namedtuple("VersionTuple", ["major", "minor", "patch", "commit"])
version_tuple = VersionTuple(*(int(i) for i in version.split(".")))
version_only = ".".join(str(i) for i in version_tuple)

if not official:
    version_only += "+unofficial"
elif nightly:
    version_only += "+nightly"

version = "Ren'Py " + version_only
script_version = 5003000
savegame_suffix = "-LT1.save"
bytecode_version = 1

################################################################################ Platform

windows = False
macintosh = False
linux = False
android = False
ios = False
emscripten = False
experimental = "RENPY_EXPERIMENTAL" in os.environ
import platform

def get_windows_version():
    import ctypes
    class OSVERSIONINFOEXW(ctypes.Structure):
        _fields_ = [('dwOSVersionInfoSize', ctypes.c_ulong),
                    ('dwMajorVersion', ctypes.c_ulong),
                    ('dwMinorVersion', ctypes.c_ulong),
                    ('dwBuildNumber', ctypes.c_ulong),
                    ('dwPlatformId', ctypes.c_ulong),
                    ('szCSDVersion', ctypes.c_wchar * 128),
                    ('wServicePackMajor', ctypes.c_ushort),
                    ('wServicePackMinor', ctypes.c_ushort),
                    ('wSuiteMask', ctypes.c_ushort),
                    ('wProductType', ctypes.c_byte),
                    ('wReserved', ctypes.c_byte)]
    try:
        os_version = OSVERSIONINFOEXW()
        os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
        retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
        if retcode != 0:
            return (10, 0)
        return (os_version.dwMajorVersion, os_version.dwMinorVersion)
    except Exception:
        return (10, 0)

if platform.win32_ver()[0]:
    windows = get_windows_version()
elif os.environ.get("RENPY_PLATFORM", "").startswith("ios"):
    ios = True
elif platform.mac_ver()[0]:
    macintosh = True
elif "ANDROID_PRIVATE" in os.environ:
    android = True
elif sys.platform == 'emscripten' or "RENPY_EMSCRIPTEN" in os.environ:
    emscripten = True
else:
    linux = True

arch = os.environ.get("RENPY_PLATFORM", "unknown-unknown-unknown").rpartition("-")[2]
mobile = android or ios or emscripten
macapp = False

################################################################################ Backup

safe_mode_checked = False
autoreload = False
session = { }
backup_blacklist = {
    "renpy",
    "renpy.compat",
    "renpy.compat.dictviews",
    "renpy.object",
    "renpy.log",
    "renpy.bootstrap",
    "renpy.debug",
    "renpy.display",
    "renpy.display.pgrender",
    "renpy.display.presplash",
    "renpy.display.scale",
    "renpy.display.swdraw",
    "renpy.display.test",
    "renpy.six",
    "renpy.text.ftfont",
    "renpy.test",
    "renpy.test.testast",
    "renpy.test.testexecution",
    "renpy.test.testkey",
    "renpy.test.testmouse",
    "renpy.test.testparser",
    "renpy.gl2",
    "renpy.gl",
    "renpycoverage",
    }

type_blacklist = (
    types.ModuleType,
    )

name_blacklist = {
    "renpy.loadsave.autosave_not_running",
    "renpy.python.unicode_re",
    "renpy.python.string_re",
    "renpy.python.store_dicts",
    "renpy.python.store_modules",
    "renpy.text.text.VERT_FORWARD",
    "renpy.text.text.VERT_REVERSE",
    "renpy.savelocation.scan_thread_condition",
    "renpy.savelocation.disk_lock",
    "renpy.character.TAG_RE",
    "renpy.display.im.cache",
    "renpy.display.render.blit_lock",
    "renpy.display.render.IDENTITY",
    "renpy.loader.auto_lock",
    "renpy.display.screen.cprof",
    "renpy.audio.audio.lock",
    "renpy.audio.audio.periodic_condition",
    "renpy.webloader.queue_lock",
    "renpy.persistent.MP_instances",
    "renpy.exports.sdl_dll",
    "renpy.sl2.slast.serial",
    "renpy.gl2.gl2draw.default_position",
    }

class Backup(_object):
    def __init__(self):
        self.variables = { }
        self.objects = { }
        self.names = { }
        for m in sys.modules.values():
            if m is None:
                continue
            self.backup_module(m)
        self.objects_pickle = pickle.dumps(self.objects, highest=True)
        self.objects = { }

    def backup_module(self, mod):
        """
        Makes a backup of `mod`, which must be a Python module.
        """
        try:
            name = mod.__name__
        except Exception:
            return
        if not name.startswith("renpy"):
            return
        if name in backup_blacklist:
            return
        if name.startswith("renpy.styledata"):
            return
        self.names[mod] = set(vars(mod).keys())
        for k, v in vars(mod).items():
            if k.startswith("__") and k.endswith("__"):
                continue
            if isinstance(v, type_blacklist):
                continue
            if name + "." + k in name_blacklist:
                continue
            idv = id(v)
            self.variables[mod, k] = idv
            self.objects[idv] = v
            try:
                pickle.dumps(v, highest=True)
            except Exception:
                print("Cannot pickle", name + "." + k, "=", repr(v))
                print("Reduce Ex is:", repr(v.__reduce_ex__(pickle.PROTOCOL)))

    def restore(self):
        if not self.names:
            return
        for mod, names in self.names.items():
            modvars = mod.__dict__
            for name in set(modvars.keys()) - names:
                del modvars[name]
        objects = pickle.loads(self.objects_pickle)
        for k, v in self.variables.items():
            mod, field = k
            setattr(mod, field, objects[v])

backup = None

################################################################################ Import

def plog(level, even, *args):
    """
    Empty version of renpy.plog that is replaced by the real implementation
    in import_all.
    """
    return


def import_all():
    import renpy
    import renpy.config
    import renpy.log
    import renpy.arguments
    import renpy.compat.fixes
    import renpy.display
    import renpy.debug
    import renpy.object
    import renpy.game
    import renpy.preferences
    import renpy.loader

    if not PY2:
        import renpy.py3analysis
    else:
        import renpy.py2analysis

    import renpy.pyanalysis
    import renpy.parameter
    import renpy.ast
    import renpy.atl
    import renpy.curry
    import renpy.color
    import renpy.easy
    import renpy.encryption
    import renpy.execution
    import renpy.lexer
    import renpy.loadsave
    import renpy.savelocation
    import renpy.savetoken
    import renpy.persistent
    import renpy.scriptedit
    import renpy.parser
    import renpy.performance
    import renpy.pydict
    import renpy.revertable
    import renpy.rollback
    import renpy.python
    import renpy.script
    import renpy.statements
    import renpy.util
    import renpy.versions

    global plog
    plog = renpy.performance.log

    import renpy.styledata
    import renpy.style
  
    renpy.styledata.import_style_functions()
    sys.modules[pystr('renpy.styleclass')] = renpy.style

    import renpy.substitutions
  
    import renpy.translation
    import renpy.translation.scanstrings
    import renpy.translation.generation
    import renpy.translation.dialogue
    import renpy.translation.extract
    import renpy.translation.merge
  
    import renpy.display
    import renpy.display.presplash
    import renpy.display.pgrender
    import renpy.display.scale
    import renpy.display.module
    import renpy.display.render
    import renpy.display.displayable
    import renpy.display.core
    import renpy.display.scenelists
    import renpy.display.swdraw
  
    import renpy.text
    import renpy.text.ftfont
    import renpy.text.font
    import renpy.text.textsupport
    import renpy.text.texwrap
    import renpy.text.text
    import renpy.text.extras
    import renpy.text.shader

    sys.modules[pystr('renpy.display.text')] = renpy.text.text

    import renpy.gl
    import renpy.gl2
  
    import renpy.display.layout
    import renpy.display.viewport
    import renpy.display.transform
    import renpy.display.motion
    import renpy.display.behavior
    import renpy.display.transition
    import renpy.display.movetransition
    import renpy.display.im
    import renpy.display.imagelike
    import renpy.display.image
    import renpy.display.video
    import renpy.display.focus
    import renpy.display.anim
    import renpy.display.particle
    import renpy.display.joystick
    import renpy.display.controller
    import renpy.display.minigame
    import renpy.display.screen
    import renpy.display.dragdrop
    import renpy.display.imagemap
    import renpy.display.predict
    import renpy.display.emulator
    import renpy.display.tts
    import renpy.display.gesture
    import renpy.display.model
    import renpy.display.quaternion
    import renpy.display.error

    import renpy.audio
    import renpy.audio.audio
    import renpy.audio.music
    import renpy.audio.sound
    import renpy.audio.filter

    import renpy.ui
    import renpy.screenlang

    import renpy.sl2
    import renpy.sl2.slast
    import renpy.sl2.slparser
    import renpy.sl2.slproperties
    import renpy.sl2.sldisplayables

    import renpy.lint
    import renpy.warp
    import renpy.editor
    import renpy.memory
    import renpy.exports
    import renpy.character
    import renpy.add_from
    import renpy.dump
  
    import renpy.gl2.gl2draw
    import renpy.gl2.gl2mesh
    import renpy.gl2.gl2model
    import renpy.gl2.gl2polygon
    import renpy.gl2.gl2shader
    import renpy.gl2.gl2texture
    import renpy.gl2.live2d

    import renpy.minstore
    import renpy.defaultstore

    import renpy.test
    import renpy.test.testmouse
    import renpy.test.testfocus
    import renpy.test.testkey
    import renpy.test.testast
    import renpy.test.testparser
    import renpy.test.testexecution

    import renpy.main

    global six
    import six
    sys.modules[pystr('renpy.six')] = six
    global backup
    backup = Backup()

    post_import()


def post_import():
    import renpy

    renpy.python.create_store("store")
    renpy.store = sys.modules['store']
    renpy.exports.store = renpy.store
    sys.modules['renpy.store'] = sys.modules['store']

    import subprocess
    sys.modules[pystr('renpy.subprocess')] = subprocess

    for k, v in renpy.defaultstore.__dict__.items():
        renpy.store.__dict__.setdefault(k, v)

    renpy.store.eval = renpy.defaultstore.eval

    for k, v in globals().items():
        renpy.exports.__dict__.setdefault(k, v)


def issubmodule(sub, module):
    return sub == module or sub.startswith(module + ".")


def reload_all():
    import renpy
    renpy.audio.audio.quit()
    renpy.style.reset()
    renpy.display.im.cache.quit()
    renpy.loader.quit_importer()
    renpy.exports.free_memory()
    renpy.display.render.screen_render = None
    renpy.display.render.mark_sweep()
    renpy.display.interface = None

    if not renpy.session.get("_keep_renderer", False):
        renpy.display.draw.quit()
        renpy.display.draw = None

    py_compile_cache = renpy.python.py_compile_cache
    reload_modules = renpy.config.reload_modules

    for i in list(sys.modules.keys()):
        if issubmodule(i, "store") or i == "renpy.store":
            m = sys.modules[i]
            if m is not None:
                m.__dict__.reset()
            del sys.modules[i]
        elif any(issubmodule(i, m) for m in reload_modules):
            del sys.modules[i]

    backup.restore()
    renpy.python.old_py_compile_cache = py_compile_cache
    renpy.display.im.reset_module()
    post_import()
    renpy.loader.init_importer()

if 1 == 0:
    store = None

if 1 == 0:
    from . import add_from
    from . import arguments
    from . import ast
    from . import atl
    from . import audio
    from . import bootstrap
    from . import character
    from . import color
    from . import compat
    from . import config
    from . import curry
    from . import debug
    from . import defaultstore
    from . import display
    from . import dump
    from . import easy
    from . import editor
    from . import encryption
    from . import error
    from . import execution
    from . import exports
    from . import game
    from . import gl
    from . import gl2
    from . import lexer
    from . import lexersupport
    from . import lint
    from . import loader
    from . import loadsave
    from . import log
    from . import main
    from . import memory
    from . import minstore
    from . import object
    from . import parameter
    from . import parser
    from . import performance
    from . import persistent
    from . import preferences
    from . import py2analysis
    from . import py3analysis
    from . import pyanalysis
    from . import pydict
    from . import python
    from . import revertable
    from . import rollback
    from . import savelocation
    from . import savetoken
    from . import screenlang
    from . import script
    from . import scriptedit
    from . import sl2
    from . import statements
    from . import style
    from . import styledata
    from . import substitutions
    from . import test
    from . import text
    from . import translation
    from . import uguu
    from . import ui
    from . import update
    from . import util
    from . import vc_version
    from . import versions
    from . import warp
    from . import webloader
