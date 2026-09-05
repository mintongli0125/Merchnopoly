from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode # *
from typing import Optional, Any
import renpy

basepath = None
searchpath = [ ]
args = None
script = None
contexts = [ ]
interface = None
lint = False
log = None 
exception_info = ''
style = None
seen_session = { }
seen_translates_count = 0
new_translates_count = 0
after_rollback = False
post_init = [ ]
less_memory = False
less_updates = False
less_mouse = False
less_imagedissolve = False
persistent = None
preferences = None
initcode_ast_id = 0
build_info = { "info" : { } }

class ExceptionInfo(object):
    def __init__(self, s, args):
        self.s = s
        self.args = args
    def __enter__(self):
        return
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            renpy.game.exception_info = self.s % self.args
        return False

class RestartContext(Exception):
    #
class RestartTopContext(Exception):
    #
class FullRestartException(Exception):
    def __init__(self, reason="end_game"):
        self.reason = reason

class UtterRestartException(Exception):
    #
class QuitException(Exception):
    def __init__(self, relaunch=False, status=0):
        Exception.__init__(self)
        self.relaunch = relaunch
        self.status = status

class JumpException(Exception):
    #
class JumpOutException(Exception):
    #
class CallException(Exception):
    from_current = False
    def __init__(self, label, args, kwargs, from_current=False):
        Exception.__init__(self)
        self.label = label
        self.args = args
        self.kwargs = kwargs
        self.from_current = from_current
    def __reduce__(self):
        return (CallException, (self.label, self.args, self.kwargs, self.from_current))

class EndReplay(Exception):
    #
class ParseErrorException(Exception):
    #

CONTROL_EXCEPTIONS = (
    RestartContext,
    RestartTopContext,
    FullRestartException,
    UtterRestartException,
    QuitException,
    JumpException,
    JumpOutException,
    CallException,
    EndReplay,
    ParseErrorException,
    KeyboardInterrupt,
    )

def context(index=-1):
    return contexts[index]

def invoke_in_new_context(callable, *args, **kwargs):
    clear = kwargs.pop('_clear_layers', True)
    restart_context = False
    if renpy.game.log.current is not None:
        renpy.game.log.complete()
    renpy.display.focus.clear_focus()
    context = renpy.execution.Context(False, contexts[-1], clear=clear)
    contexts.append(context)
    if renpy.display.interface is not None:
        renpy.display.interface.enter_context()
    try:
        return callable(*args, **kwargs)
    except renpy.game.RestartContext:
        restart_context = True
        raise
    except renpy.game.RestartTopContext:
        restart_context = True
        raise
    except renpy.game.JumpOutException as e:
        contexts[-2].force_checkpoint = True
        contexts[-2].abnormal = True
        raise renpy.game.JumpException(e.args[0])
    finally:
        if not restart_context:
            context.pop_all_dynamic()
        contexts.pop()
        contexts[-1].do_deferred_rollback()
        if interface and interface.restart_interaction and contexts:
            contexts[-1].scene_lists.focused = None

def call_in_new_context(label, *args, **kwargs):
    clear = kwargs.pop('_clear_layers', True)
    if renpy.game.log.current is not None:
        renpy.game.log.complete()
    renpy.display.focus.clear_focus()
    context = renpy.execution.Context(False, contexts[-1], clear=clear)
    contexts.append(context)
    if renpy.display.interface is not None:
        renpy.display.interface.enter_context()
    if args:
        renpy.store._args = args
    else:
        renpy.store._args = None
    if kwargs:
        renpy.store._kwargs = renpy.revertable.RevertableDict(kwargs)
    else:
        renpy.store._kwargs = None
    try:
        context.goto_label(label)
        return renpy.execution.run_context(False)
    except renpy.game.JumpOutException as e:
        contexts[-2].force_checkpoint = True
        contexts[-2].abnormal = True
        raise renpy.game.JumpException(e.args[0])
    finally:
        contexts.pop()
        contexts[-1].do_deferred_rollback()
        if interface and interface.restart_interaction and contexts:
            contexts[-1].scene_lists.focused = None

def call_replay(label, scope={}):
    renpy.display.focus.clear_focus()
    renpy.game.log.complete()
    old_log = renpy.game.log
    renpy.game.log = renpy.python.RollbackLog()
    sb = renpy.python.StoreBackup()
    renpy.python.clean_stores()
    context = renpy.execution.Context(True)
    contexts.append(context)
  
    if renpy.display.interface is not None:
        renpy.display.interface.enter_context()
    renpy.exports.execute_default_statement()
    for k, v in renpy.config.replay_scope.items():
        setattr(renpy.store, k, v)
    for k, v in scope.items():
        setattr(renpy.store, k, v)
      
    renpy.store._in_replay = label
    try:
        context.goto_label("_start_replay")
        renpy.execution.run_context(False)
    except EndReplay:
        pass
    finally:
        context.pop_all_dynamic()
        contexts.pop()
        renpy.game.log = old_log
        sb.restore()
        if interface and interface.restart_interaction and contexts:
            contexts[-1].scene_lists.focused = None
        renpy.config.skipping = None
      
    if renpy.config.after_replay_callback:
        renpy.config.after_replay_callback()

if False:
    script = renpy.script.Script()
    interface = renpy.display.core.Interface()
    log = renpy.python.RollbackLog()
    preferences = renpy.preferences.Preferences()
