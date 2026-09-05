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

################################################################################ Audio

renpy.update_path()

if 1 == 0:
    from . import audio
    from . import filter
    from . import music
    from . import renpysound
    from . import sound
    from . import webaudio

################################################################################ Compat

import future.standard_library
import future.utils
import builtins
import io
import sys
import operator
python_open = open
future.standard_library.install_aliases()
PY2 = future.utils.PY2

if PY2:
    open = io.open
    import re
    re.Pattern = re._pattern_type
else:
    open = builtins.open

def compat_open(*args, **kwargs):
    if (sys._getframe(1).f_code.co_flags & 0xa000) == 0xa000:
        return open(*args, **kwargs)
    else:
        return python_open(*args, **kwargs)

import codecs
strict_error = codecs.lookup_error("strict")
codecs.register_error("python_strict", strict_error)

if PY2:
    surrogateescape_error = codecs.lookup_error("surrogateescape")
    codecs.register_error("strict", surrogateescape_error)

import renpy
renpy.update_path()
basestring = future.utils.string_types
pystr = str
unicode = future.utils.text_type
str = builtins.str; globals()["str"] = future.utils.text_type
bord = future.utils.bord

if PY2:
    bchr = chr
else:
    def bchr(i):
        return bytes([i])
tobytes = future.utils.tobytes

from future.builtins import chr

def add_attribute(obj, name, value):
    pass

if PY2:
    try:
        from renpy.compat.dictviews import add_attribute
    except ImportError:
        print("Could not import renpy.compat.dictviews.", file=sys.stderr)
if PY2:
    range = xrange
else:
    range = builtins.range

round = builtins.round

if PY2:
    import types
    def text_write(self, s):
        if isinstance(s, bytes):
            s = s.decode("utf-8", "surrogateescape")
        return self._write(s)
    add_attribute(io.TextIOWrapper, "_write", io.TextIOWrapper.write)
    add_attribute(io.TextIOWrapper, "write", types.MethodType(text_write, None, io.TextIOWrapper)) # type: ignore
if PY2:
    import subprocess
    if hasattr(subprocess, 'Popen'):
        class Popen(subprocess.Popen):
            def __init__(self, *args, **kwargs):
                if ("stdout" not in kwargs) and ("stderr" not in kwargs) and ("stdin" not in kwargs):
                    kwargs.setdefault("close_fds", True)
                super(Popen, self).__init__(*args, **kwargs)

        subprocess.Popen = Popen
if PY2:
    intern_cache = {}
    def intern(s):
        return intern_cache.setdefault(s, s)
    sys.intern = intern

__all__ = [ "PY2", "open", "basestring", "str", "pystr", "range",
            "round", "bord", "bchr", "tobytes", "chr", "unicode", ]
if PY2:
    __all__ = [ bytes(i) for i in __all__ ]

if 1 == 0:
    from . import fixes
    from . import pickle

################################################################################ Display

from typing import Optional, Any
renpy.update_path()
import renpy.log

draw = None
interface = None
less_imagedissolve = False
touch = False
info = None
can_fullscreen = True

def get_info():
    global info
    if info is None:
        import pygame_sdl2 as pygame
        pygame.display.init()
        info = pygame.display.Info()
    return info

log = renpy.log.open("log", developer=False, append=False)
ic_log = renpy.log.open("image_cache", developer=True, append=False)
to_log = renpy.log.open("text_overflow", developer=True, append=True)

if 1 == 0:
    from . import accelerator
    from . import anim
    from . import behavior
    from . import controller
    from . import core
    from . import displayable
    from . import dragdrop
    from . import emulator
    from . import error
    from . import focus
    from . import gesture
    from . import im
    from . import image
    from . import imagelike
    from . import imagemap
    from . import joystick
    from . import layout
    from . import matrix
    from . import minigame
    from . import model
    from . import module
    from . import motion
    from . import movetransition
    from . import particle
    from . import pgrender
    from . import predict
    from . import presplash
    from . import quaternion
    from . import render
    from . import scale
    from . import scenelists
    from . import screen
    from . import swdraw
    from . import transform
    from . import transition
    from . import tts
    from . import video
    from . import viewport

################################################################################ Exports

import gc
import re
import time
import threading
import fnmatch
import pygame_sdl2

try:
    import emscripten
except ImportError:
    pass

import renpy.audio.sound as sound
import renpy.audio.music as music

from renpy.ast import (
    eval_who,
)
from renpy.atl import (
    atl_warper,
)
from renpy.bootstrap import (
    get_alternate_base,
)
from renpy.character import (
    display_say,
    predict_show_display_say,
    show_display_say,
)
from renpy.curry import (
    curry,
    partial,
)
from renpy.display.behavior import (
    Keymap,
    clear_keymap_cache,
    is_selected,
    is_sensitive,
    map_event,
    queue_event,
    run,
    run as run_action,
    run_periodic,
    run_unhovered,
)
from renpy.display.focus import (
    capture_focus,
    clear_capture_focus,
    focus_coordinates,
    get_focus_rect,
)
from renpy.display.im import (
    load_image,
    load_rgba,
    load_surface,
)
from renpy.display.image import (
    check_image_attributes,
    get_available_image_attributes,
    get_available_image_tags,
    get_ordered_image_attributes,
    get_registered_image,
    image_exists,
    image_exists as has_image,
    list_images,
)
from renpy.display.minigame import (
    Minigame,
)
from renpy.display.predict import (
    screen as predict_screen,
)
from renpy.display.screen import (
    ScreenProfile as profile_screen,
    current_screen,
    define_screen,
    get_displayable,
    get_displayable_properties,
    get_screen,
    get_screen_variable,
    get_widget,
    get_widget_properties,
    has_screen,
    hide_screen,
    set_screen_variable,
    show_screen,
    use_screen,
)
from renpy.display.tts import (
    speak as alt,
    speak_extra_alt,
)
from renpy.display.video import (
    movie_start_displayable,
    movie_start_fullscreen,
    movie_stop,
)
from renpy.easy import (
    displayable,
    predict,
    split_properties,
)
from renpy.editor import (
    launch_editor,
)
from renpy.execution import (
    not_infinite_loop,
    reset_all_contexts,
)
from renpy.exports.commonexports import (
    renpy_pure,
)
from renpy.gl2.gl2shadercache import (
    register_shader,
)

from renpy.gl2.live2d import (
    has_live2d,
)
from renpy.lexer import (
    unelide_filename,
)
from renpy.lint import (
    try_compile,
    try_eval,
)
from renpy.loader import (
    add_python_directory,
)
from renpy.loadsave import (
    can_load,
    copy_save,
    force_autosave,
    list_saved_games,
    list_slots,
    load,
    newest_slot,
    rename_save,
    save,
    scan_saved_game,
    slot_json,
    slot_mtime,
    slot_screenshot,
    unlink_save,
)
from renpy.memory import (
    diff_memory,
    profile_memory,
    profile_rollback,
)
from renpy.parser import (
    get_parse_errors,
)
from renpy.persistent import (
    register_persistent,
)
from renpy.pyanalysis import (
    const,
    not_const,
    pure,
)
from renpy.python import (
    py_eval as eval,
)
from renpy.rollback import (
    rng as random,
)
from renpy.savetoken import (
    get_save_token_keys,
)
from renpy.sl2.slparser import (
    CustomParser as register_sl_statement,
    register_sl_displayable,
)
from renpy.statements import (
    register as register_statement,
)
from renpy.text.extras import (
    ParameterizedText,
    check_text_tags,
    filter_text_tags,
)
from renpy.text.font import (
    register_bmfont,
    register_mudgefont,
    register_sfont,
    variable_font_info,
)
from renpy.text.shader import (
    TextShader,
    register_textshader,
)
from renpy.text.text import (
    BASELINE,
    language_tailor,
)
from renpy.text.textsupport import (
    DISPLAYABLE as TEXT_DISPLAYABLE,
    PARAGRAPH as TEXT_PARAGRAPH,
    TAG as TEXT_TAG,
    TEXT as TEXT_TEXT,
)
from renpy.translation import (
    change_language,
    get_translation_identifier,
    get_translation_info,
    known_languages,
    translate_string,
)
from renpy.translation.generation import (
    generic_filter as transform_text,
)
from renpy.ui import (
    Choice,
)

renpy_pure("check_text_tags")
renpy_pure("curry")
renpy_pure("filter_text_tags")
renpy_pure("has_screen")
renpy_pure("image_exists")
renpy_pure("Keymap")
renpy_pure("known_languages")
renpy_pure("ParameterizedText")
renpy_pure("partial")
renpy_pure("split_properties")
renpy_pure("unelide_filename")

from renpy.exports.actionexports import (
    confirm,
    display_notify,
    notify,
)
from renpy.exports.contextexports import (
    add_to_all_stores,
    call_in_new_context,
    call_replay,
    call_stack_depth,
    clear_game_runtime,
    clear_line_log,
    context_dynamic,
    context_nesting_level,
    context,
    current_interact_type,
    curried_call_in_new_context,
    curried_invoke_in_new_context,
    dynamic,
    end_replay,
    game_menu,
    get_game_runtime,
    get_line_log,
    get_mode,
    get_return_stack,
    get_skipping,
    invoke_in_new_context,
    is_init_phase,
    is_skipping,
    jump_out_of_context,
    last_interact_type,
    mode,
    pop_call,
    pop_return,
    scry,
    set_return_stack,
    stop_skipping,
)
from renpy.exports.debugexports import (
    error,
    get_filename_line,
    log,
    pop_error_handler,
    push_error_handler,
    warp_to_line,
    write_log
)
from renpy.exports.displayexports import (
    _find_image,
    add_layer,
    can_fullscreen,
    can_show,
    cancel_gesture,
    change_zorder,
    clear_attributes,
    clear_retain,
    Container,
    copy_images,
    count_displayables_in_layer,
    default_layer,
    display_reset,
    Displayable,
    easy_displayable,
    end_interaction,
    flush_cache_file,
    force_full_redraw,
    free_memory,
    get_adjustment,
    get_at_list,
    get_attributes,
    get_hidden_tags,
    get_image_bounds,
    get_image_load_log,
    get_mouse_name,
    get_mouse_pos,
    get_ongoing_transition,
    get_physical_size,
    get_placement,
    get_refresh_rate,
    get_renderer_info,
    get_showing_tags,
    get_texture_size,
    get_transition,
    get_zorder_list,
    hide,
    iconify,
    IgnoreEvent,
    image_size,
    image,
    is_mouse_visible,
    is_pixel_opaque,
    is_start_interact,
    layer_at_list,
    maximum_framerate,
    placement,
    predict_show,
    quit_event,
    redraw,
    render_to_file,
    render_to_surface,
    render,
    Render,
    reset_physical_size,
    restart_interaction,
    scene_lists,
    scene,
    screenshot_to_bytes,
    screenshot,
    set_focus,
    set_mouse_pos,
    set_physical_size,
    set_tag_attributes,
    show_layer_at,
    show,
    showing,
    shown_window,
    take_screenshot,
    timeout,
    toggle_fullscreen,
    transition,
)
from renpy.exports.fetchexports import (
    fetch_emscripten,
    fetch_pause,
    fetch_requests,
    fetch,
    FetchError,
    proxies
)
from renpy.exports.inputexports import (
    get_editable_input_value,
    input,
    set_editable_input_value,
    web_input,
)
from renpy.exports.loaderexports import (
    exists,
    file,
    fsdecode,
    fsencode,
    list_files,
    loadable,
    munge,
    notl_file,
    open_file,
)
from renpy.exports.mediaexports import (
    movie_cutscene,
    music_start,
    music_stop,
    play,
    toggle_music,
)

menu_args = None
menu_kwargs = None

from renpy.exports.menuexports import (
    choice_for_skipping,
    display_menu,
    get_menu_args,
    menu,
    MenuEntry,
    predict_menu,
)
from renpy.exports.persistentexports import (
    seen_label,
    mark_label_seen,
    mark_label_unseen,
    seen_audio,
    mark_audio_seen,
    mark_audio_unseen,
    seen_image,
    mark_image_seen,
    mark_image_unseen,
    save_persistent,
    is_seen,
)
from renpy.exports.platformexports import (
    check_permission,
    get_on_battery,
    get_sdl_dll,
    get_sdl_window_pointer,
    invoke_in_main_thread,
    invoke_in_thread,
    request_permission,
    variant,
    vibrate,
    open_url,
)
from renpy.exports.predictexports import (
    cache_pin,
    cache_unpin,
    expand_predict,
    predicting,
    start_predict_screen,
    start_predict,
    stop_predict_screen,
    stop_predict,
)
from renpy.exports.restartexports import (
    full_restart,
    get_autoreload,
    quit,
    reload_script,
    set_autoreload,
    utter_restart,
)
from renpy.exports.rollbackexports import (
    block_rollback,
    can_rollback,
    checkpoint,
    fix_rollback,
    get_identifier_checkpoints,
    get_roll_forward,
    in_fixed_rollback,
    in_rollback,
    retain_after_load,
    roll_forward_core,
    roll_forward_info,
    rollback,
    suspend_rollback,
)
from renpy.exports.sayexports import (
    count_dialogue_blocks,
    count_newly_seen_dialogue_blocks,
    count_seen_dialogue_blocks,
    curried_do_reshow_say,
    do_reshow_say,
    get_reshow_say,
    get_say_attributes,
    get_say_image_tag,
    get_side_image,
    last_say,
    LastSay,
    predict_say,
    reshow_say,
    say,
    scry_say,
    substitute,
    tag_quoting_dict,
    TagQuotingDict,
)
from renpy.exports.scriptexports import (
    get_all_labels,
    has_label,
    include_module,
    load_language,
    load_module,
    load_string,
    munged_filename,
)
from renpy.exports.statementexports import (
    call_screen,
    call,
    execute_default_statement,
    imagemap,
    jump,
    pause,
    return_statement,
    with_statement,
)

globals()["with"] = with_statement

if sys.maxsize > (2 << 32):
    bits = 64
else:
    bits = 32

@renpy_pure
def version(tuple=False):
    if tuple:
        return renpy.version_tuple
    return renpy.version

version_string = renpy.version
version_only = renpy.version_only
version_name = renpy.version_name
version_tuple = renpy.version_tuple
license = ""

try:
    import platform as _platform
    platform = "-".join(_platform.platform().split("-")[:2])
except Exception:
    if renpy.android:
        platform = "Android"
    elif renpy.ios:
        platform = "iOS"
    else:
        platform = "Unknown"

################################################################################ GL, SL

renpy.update_path()

if 1 == 0:
    from . import gldraw
    from . import glenviron_shader
    from . import glfunctions
    from . import glrtt_copy
    from . import glrtt_fbo
    from . import gltexture

    from . import gl2debug
    from . import gl2draw
    from . import gl2functions
    from . import gl2mesh
    from . import gl2mesh2
    from . import gl2mesh3
    from . import gl2model
    from . import gl2polygon
    from . import gl2shader
    from . import gl2shadercache
    from . import gl2texture
    from . import live2d
    from . import live2dmodel
    from . import live2dmotion

    from . import slast
    from . import sldisplayables
    from . import slparser
    from . import slproperties

################################################################################ Style data

def import_style_functions():
    import renpy.styledata.stylesets
    import renpy.styledata.style_functions
    import renpy.styledata.style_activate_functions
    import renpy.styledata.style_hover_functions
    import renpy.styledata.style_idle_functions
    import renpy.styledata.style_insensitive_functions
    import renpy.styledata.style_selected_functions
    import renpy.styledata.style_selected_activate_functions
    import renpy.styledata.style_selected_hover_functions
    import renpy.styledata.style_selected_idle_functions
    import renpy.styledata.style_selected_insensitive_functions
    import renpy.styledata.styleclass
    renpy.style.Style = renpy.styledata.styleclass.Style

if 1 == 0:
    from . import style_activate_functions
    from . import style_functions
    from . import style_hover_functions
    from . import style_idle_functions
    from . import style_insensitive_functions
    from . import style_selected_activate_functions
    from . import style_selected_functions
    from . import style_selected_hover_functions
    from . import style_selected_idle_functions
    from . import style_selected_insensitive_functions
    from . import styleclass
    from . import stylesets
    from . import styleutil

################################################################################ Test, Text, Uguu, Update

from renpy.uguu.uguu import *

if 1 == 0:
    from . import testast
    from . import testexecution
    from . import testfocus
    from . import testkey
    from . import testmouse
    from . import testparser

    from . import emoji_trie
    from . import extras
    from . import font
    from . import ftfont
    from . import hbfont
    from . import shader
    from . import text
    from . import textsupport
    from . import texwrap

    from . import uguu
    from . import common
    from . import download
    from . import generate
    from . import update
