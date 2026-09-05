from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode
from typing import Tuple, List, Dict, Set, Optional, Iterable, Any
import os
import sys
import time
import zipfile
import gc
import linecache
import json
import renpy
import renpy.game as game

last_clock = time.time()

def log_clock(s):
    global last_clock
    now = time.time()
    s = "{} took {:.2f}s".format(s, now - last_clock)
    renpy.display.log.write(s)
    if renpy.android and not renpy.config.log_to_stdout:
        print(s)
    renpy.display.presplash.pump_window()
    last_clock = now

def reset_clock():
    global last_clock
    last_clock = time.time()

def run(restart):
    reset_clock()
    renpy.python.clean_stores()
    log_clock("Cleaning stores")
    renpy.translation.init_translation()
    log_clock("Init translation")
    renpy.style.build_styles()
    log_clock("Build styles")
    renpy.sl2.slast.load_cache()
    log_clock("Load screen analysis")
    renpy.display.screen.analyze_screens()
    log_clock("Analyze screens")
    
    if not restart:
        renpy.sl2.slast.save_cache()
        log_clock("Save screen analysis")
    renpy.display.screen.prepare_screens()
    log_clock("Prepare screens")
    if not restart:
        renpy.pyanalysis.save_cache()
        log_clock("Save pyanalysis.")
        renpy.game.script.save_bytecode()
        log_clock("Save bytecode.")
    if not renpy.arguments.post_init():
        raise renpy.game.QuitException()
      
    renpy.display.im.ImageBase.obsolete_list = [ ]
    
    if renpy.config.clear_lines:
        renpy.scriptedit.lines.clear()
    renpy.display.presplash.sleep()
    game.log = renpy.python.RollbackLog()
    game.contexts = [ renpy.execution.Context(True) ]
    
    if game.script.has_label("_start"):
        start_label = '_start'
    else:
        start_label = 'start'
    game.context().goto_label(start_label)

    try:
        renpy.exports.log("--- " + time.ctime())
        renpy.exports.log("")
    except Exception:
        pass
    renpy.store._restart = restart

    renpy.display.interface.enter_context()
    log_clock("Running {}".format(start_label))
    renpy.execution.run_context(True)


def load_rpe(fn):
    with zipfile.ZipFile(fn) as zfn:
        autorun = zfn.read("autorun.py")
    if fn in sys.path:
        sys.path.remove(fn)
    sys.path.insert(0, fn)
    exec(autorun, {'__file__': os.path.join(fn, "autorun.py")})

def load_rpe_py(fn):
    with open(fn) as f:
        autorun = f.read()
    exec(autorun, {'__file__': fn})

def choose_variants():
    if "RENPY_VARIANT" in os.environ:
        renpy.config.variants = list(os.environ["RENPY_VARIANT"].split()) + [ None ]
        renpy.display.emulator.early_init_emulator()
        return
    renpy.config.variants = [ None ]

    if renpy.android:
        renpy.config.variants.insert(0, 'mobile')
        renpy.config.variants.insert(0, 'android')
        import android
        import math
        import pygame_sdl2 as pygame
        from jnius import autoclass
        try:
            Build = autoclass("android.os.Build")
            manufacturer = Build.MANUFACTURER
            model = Build.MODEL
            print("Manufacturer", manufacturer, "model", model)
            if manufacturer == "Amazon" and model.startswith("AFT"):
                print("Running on a Fire TV.")
                renpy.config.variants.insert(0, "firetv")
        except Exception:
            pass
        package_manager = android.activity.getPackageManager()

        if package_manager.hasSystemFeature("android.hardware.type.television"):
            print("Running on a television.")
            renpy.config.variants.insert(0, "tv")
            renpy.config.variants.insert(0, "small")
            return
        try:
            PythonSDLActivity = autoclass("org.renpy.android.PythonSDLActivity")
            if PythonSDLActivity.isChromebook():
                print("Running on ChromeOS.")
                renpy.config.variants.insert(0, 'chromeos')
        except Exception:
            pass
            
        renpy.config.variants.insert(0, 'touch')
        pygame.display.init()
        info = renpy.display.get_info()
        diag = math.hypot(info.current_w, info.current_h) / android.get_dpi()
        print("Screen diagonal is", diag, "inches.")
        if diag >= 6:
            renpy.config.variants.insert(0, 'tablet')
            renpy.config.variants.insert(0, 'medium')
        else:
            renpy.config.variants.insert(0, 'phone')
            renpy.config.variants.insert(0, 'small')

    elif renpy.ios:
        renpy.config.variants.insert(0, 'mobile')
        renpy.config.variants.insert(0, 'ios')
        renpy.config.variants.insert(0, 'touch')
        from pyobjus import autoclass
        UIDevice = autoclass("UIDevice")
        idiom = UIDevice.currentDevice().userInterfaceIdiom
        print("iOS device idiom", idiom)
        if idiom >= 1:
            renpy.config.variants.insert(0, 'tablet')
            renpy.config.variants.insert(0, 'medium')
        else:
            renpy.config.variants.insert(0, 'phone')
            renpy.config.variants.insert(0, 'small')

    elif renpy.emscripten:
        import emscripten
        import re
        renpy.config.variants.insert(0, 'web')

        mobile = emscripten.run_script_int(
            r'''/Mobile|Android|iPad|iPhone/.test(navigator.userAgent)
            || (navigator.userAgent.indexOf("Mac") != -1 && navigator.maxTouchPoints > 1)''')
        if mobile:
            renpy.config.variants.insert(0, 'mobile')
            
        touch = emscripten.run_script_int(r'''
          ('ontouchstart' in window) ||
            (navigator.maxTouchPoints > 0) ||
            (navigator.msMaxTouchPoints > 0)''')
        if touch == 1:
            if mobile:
                renpy.config.variants.insert(0, 'touch')

        ref_width = emscripten.run_script_int(r'''screen.width''')
        ref_height = emscripten.run_script_int(r'''screen.height''')
        if mobile:
            if (ref_width < 768 or ref_height < 768):
                renpy.config.variants.insert(0, 'small')
                renpy.config.variants.insert(0, 'phone')
            else:
                renpy.config.variants.insert(0, 'medium')
                renpy.config.variants.insert(0, 'tablet')
        else:
            renpy.config.variants.insert(0, 'large')
    else:
        renpy.config.variants.insert(0, 'pc')
        renpy.config.variants.insert(0, 'large')

def load_build_info():
    try:
        f = renpy.exports.open_file("cache/build_info.json", "utf-8")
        renpy.game.build_info = json.load(f)
    except Exception:
        renpy.game.build_info = { "info" : { } }

def main():
    gc.set_threshold(*renpy.config.gc_thresholds)
    renpy.game.exception_info = 'Before loading the script.'
    linecache.clearcache()
    renpy.arguments.pre_init()
    renpy.sl2.slparser.init()
    renpy.config.init()
    try:
        renpy.gl2.live2d.reset()
    except Exception:
        pass
    choose_variants()
    renpy.display.touch = "touch" in renpy.config.variants
    if (renpy.android or renpy.ios) and not renpy.config.log_to_stdout:
        print("Version:", renpy.version)

    game.basepath = renpy.config.gamedir
    renpy.config.commondir = renpy.__main__.path_to_common(renpy.config.renpy_base)
    renpy.config.searchpath = renpy.__main__.predefined_searchpath(renpy.config.commondir)

    for dir in [ renpy.config.renpy_base ] + renpy.config.searchpath:
        if not os.path.isdir(dir):
            continue
        for fn in sorted(os.listdir(dir)):
            if fn.lower().endswith(".rpe"):
                load_rpe(dir + "/" + fn)
            if fn.lower().endswith(".rpe.py"):
                load_rpe_py(dir + "/" + fn)

    archive_extensions = [ ]
    for handler in renpy.loader.archive_handlers:
        for ext in handler.get_supported_extensions():
            if not (ext in archive_extensions):
                archive_extensions.append(ext)

    for dn in renpy.config.searchpath:
        if not os.path.isdir(dn):
            continue
        for i in sorted(os.listdir(dn)):
            base, ext = os.path.splitext(i)
            if not (ext in archive_extensions):
                continue
            renpy.config.archives.append(base)
    
    renpy.config.archives.reverse()
    renpy.loader.index_archives()
    renpy.loader.auto_init()
    load_build_info()

    log_clock("Early init")
    game.log = renpy.python.RollbackLog()
    renpy.store.store = sys.modules['store']
    game.style = renpy.style.StyleManager()
    renpy.store.style = game.style
    game.contexts = [ renpy.execution.Context(False) ]
    game.contexts[0].init_phase = True
    renpy.execution.not_infinite_loop(60)

    renpy.game.exception_info = 'While loading the script.'
    renpy.game.script = renpy.script.Script()
    if renpy.session.get("compile", False):
        renpy.game.args.compile = True

    renpy.exports.load_module("_errorhandling")
    if renpy.exports.loadable("tl/None/common.rpym") or renpy.exports.loadable("tl/None/common.rpymc"):
        renpy.exports.load_module("tl/None/common")

    renpy.config.init_system_styles()
    renpy.style.build_styles()
    log_clock("Loading error handling")
    
    if (renpy.game.args.command == 'compile') and not (renpy.game.args.keep_orphan_rpyc):
        for (fn, dn) in renpy.game.script.script_files:
            if dn is None:
                continue
            if not os.path.isfile(os.path.join(dn, fn + ".rpy")) and not os.path.isfile(os.path.join(dn, fn + "_ren.py")):
                try:
                    name = os.path.join(dn, fn + ".rpyc")
                    os.rename(name, name + ".bak")
                except OSError:
                    pass
        renpy.loader.cleardirfiles()
        renpy.game.script.scan_script_files()

    renpy.game.script.load_script()
    log_clock("Loading script")
    if renpy.game.args.command == 'load-test':
        start = time.time()
        for i in range(5):
            print(i)
            renpy.game.script = renpy.script.Script()
            renpy.game.script.load_script()
        print(time.time() - start)
        sys.exit(0)
    renpy.game.exception_info = 'After loading the script.'

    if renpy.config.savedir is None:
        renpy.config.savedir = renpy.__main__.path_to_saves(renpy.config.gamedir)
    if renpy.game.args.savedir:
        renpy.config.savedir = renpy.game.args.savedir
    renpy.savetoken.init()

    game.persistent = renpy.persistent.init()
    game.preferences = game.persistent._preferences
    for i in renpy.game.persistent._seen_translates:
        if i in renpy.game.script.translator.default_translates:
            renpy.game.seen_translates_count += 1
    if game.persistent._virtual_size:
        renpy.config.screen_width, renpy.config.screen_height = game.persistent._virtual_size

    renpy.savelocation.init()
    try:
        renpy.loadsave.init()
        renpy.savetoken.upgrade_all_savefiles()
        log_clock("Loading save slot metadata")
        renpy.persistent.update()
        game.preferences = game.persistent._preferences
        log_clock("Loading persistent")
        game.seen_session = { }
        renpy.store.persistent = game.persistent
        renpy.store._preferences = game.preferences
        renpy.store._test = renpy.test.testast._test

        if renpy.parser.report_parse_errors():
            raise renpy.game.ParseErrorException()
        renpy.game.exception_info = 'While executing init code:'

        for id_, (_prio, node) in enumerate(game.script.initcode):
            renpy.game.initcode_ast_id = id_
            if isinstance(node, renpy.ast.Node):
                node_start = time.time()
                renpy.game.context().run(node)
                node_duration = time.time() - node_start
                if node_duration > renpy.config.profile_init:
                    renpy.display.log.write(" - Init at %s:%d took %.5f s.", node.filename, node.linenumber, node_duration)
            else:
                node()

        renpy.game.exception_info = 'After initialization, but before game start.'
        renpy.android = renpy.android or renpy.config.simulate_android
        renpy.log.post_init()
        for i in renpy.game.post_init:
            i()
        renpy.config.post_init()
        renpy.game.script.report_duplicate_labels()

        renpy.display.image.image_names.sort()
        game.persistent._virtual_size = renpy.config.screen_width, renpy.config.screen_height
        log_clock("Running init code")
        renpy.pyanalysis.load_cache()
        log_clock("Loading analysis data")
        renpy.game.script.analyze()
        renpy.atl.compile_all()
        log_clock("Analyze and compile ATL")
        renpy.savelocation.init()
        renpy.loadsave.init()
        log_clock("Reloading save slot metadata")

        renpy.loader.index_archives()
        log_clock("Index archives")
        
        renpy.game.less_memory = "RENPY_LESS_MEMORY" in os.environ
        renpy.game.less_mouse = "RENPY_LESS_MOUSE" in os.environ
        renpy.game.less_updates = "RENPY_LESS_UPDATES" in os.environ
        renpy.dump.dump(False)
        renpy.game.script.make_backups()
        log_clock("Dump and make backups")

        renpy.display.im.cache.init()
        log_clock("Cleaning cache")
        renpy.python.make_clean_stores()
        log_clock("Making clean stores")
        renpy.display.behavior.init_keymap()
        gc.collect(2)
        if gc.garbage:
            del gc.garbage[:]
        if renpy.config.manage_gc:
            gc.set_threshold(*renpy.config.gc_thresholds)
            gc_debug = int(os.environ.get("RENPY_GC_DEBUG", 0))
            if renpy.config.gc_print_unreachable:
                gc_debug |= gc.DEBUG_SAVEALL
            gc.set_debug(gc_debug)
        else:
            gc.set_threshold(700, 10, 10)
        log_clock("Initial gc")
        renpy.debug.init_main_thread_open()

        if not game.interface:
            renpy.display.core.Interface()
            log_clock("Creating interface object")

        restart = None
        while True:
            if restart:
                renpy.display.screen.before_restart()
            try:
                try:
                    run(restart)
                finally:
                    restart = (renpy.config.end_game_transition, "_invoke_main_menu", "_main_menu")
            except renpy.game.QuitException:
                renpy.audio.audio.fadeout_all()
                raise
            except game.FullRestartException as e:
                restart = e.reason
            finally:
                renpy.persistent.update(True)
                renpy.persistent.save_on_quit_MP()
                try:
                    renpy.gl2.live2d.reset_states()
                except Exception:
                    pass
                renpy.display.interface.finish_pending()
                renpy.loadsave.autosave_not_running.wait(3.0)
                for cb in renpy.config.at_exit_callbacks:
                    cb()

    finally:
        gc.set_debug(0)
        for i in renpy.config.quit_callbacks:
            i()
        renpy.loader.auto_quit()
        renpy.savelocation.quit()
        renpy.translation.write_updated_strings()

    if not renpy.display.error.error_handled:
        renpy.display.render.check_at_shutdown()
