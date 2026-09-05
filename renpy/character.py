from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode # *
from typing import Any, Literal
import renpy
import re
import os
import collections

TAG_RE = re.compile(r'(\{\{)|(\{(p|w|nw|fast|done)(?:\=([^}]*))?\})', re.S)
less_pauses = ("RENPY_LESS_PAUSES" in os.environ)

class Callbacks(object):
    def __init__(self, callbacks, interact, type, cb_args, multiple):
        self.callbacks = callbacks
        self.interact = interact
        self.type = type
        self.cb_args = cb_args
        self.multiple = multiple
        self.what = None
        self.start = None
        self.end = None
        self.delay = None
        self.last_segment = None

    def __call__(self, *args, **kwargs):
        if not self.callbacks:
            return
        kwargs["type"] = self.type
        kwargs["interact"] = self.interact
        if renpy.config.character_callback_compat is None:
            if self.what is not None:
                kwargs["what"] = self.what
            if self.start is not None:
                kwargs["start"] = self.start
            if self.end is not None:
                kwargs["end"] = self.end
            if self.delay is not None:
                kwargs["delay"] = self.delay
            if self.last_segment is not None:
                kwargs["last_segment"] = self.last_segment
            if  self.multiple is not None:
                kwargs["multiple"] = self.multiple
            kwargs["please_ignore_unknown_keyword_arguments"] = None
        kwargs.update(self.cb_args)
        for c in self.callbacks:
            c(*args, **kwargs)

    def copy(self):
        rv = Callbacks(self.callbacks, self.interact, self.type, self.cb_args, self.multiple)
        rv.__dict__.update(self.__dict__)
        return rv

class DialogueTextTags(object):

    def __init__(self, s):
        self.text = ""
        self.pause_start = [ 0 ]
        self.pause_end = [ ]
        self.pause_delay = [ ]
        self.no_wait = False
        self.has_done = False
        self.fast = False
        i = iter(TAG_RE.split(s))

        while True:
            try:
                self.text += next(i)
                quoted = next(i)
                full_tag = next(i)
                tag = next(i)
                value = next(i)
                if value is not None:
                    value = float(value)
                if quoted is not None:
                    self.text += quoted
                    continue
                if tag == "p" or tag == "w":
                    if not less_pauses:
                        self.pause_start.append(len(self.text))
                        self.pause_end.append(len(self.text))
                        self.pause_delay.append(value)
                elif tag == "nw":
                    self.no_wait = True
                    if value is not None and not less_pauses:
                        self.pause_start.append(len(self.text))
                        self.pause_end.append(len(self.text))
                        self.pause_delay.append(value)
                elif tag == "fast":
                    self.pause_start = [ len(self.text) ]
                    self.pause_end = [ ]
                    self.pause_delay = [ ]
                    self.no_wait = False
                    self.fast = True
                elif tag == "done":
                    self.has_done = True
                    self.text += full_tag
                    break
                self.text += full_tag
            except StopIteration:
                break
        self.pause_end.append(len(self.text))

        while True:
            try:
                self.text += next(i)
                quoted = next(i)
                full_tag = next(i)
                tag = next(i)
                value = next(i)
                if quoted is not None:
                    self.text += quoted
                    continue
                self.text += full_tag
            except StopIteration:
                break

        if self.no_wait:
            self.pause_delay.append(0)
        else:
            self.pause_delay.append(None)


def predict_show_display_say(who, what, who_args, what_args, window_args, image=False, two_window=False, side_image=None, screen=None, properties=None, **kwargs):
    if side_image:
        renpy.easy.predict(side_image)
    if renpy.store._side_image_attributes:
        renpy.easy.predict(renpy.display.image.ImageReference(("side",) + renpy.store._side_image_attributes))
    if image:
        if image != "<Dynamic>":
            renpy.easy.predict(who)
        kwargs["image"] = image
    if screen:
        props = compute_widget_properties(who_args, what_args, window_args, properties)
        renpy.display.predict.screen(
            screen,
            _widget_properties=props,
            who=who,
            what=what,
            two_window=two_window,
            side_image=side_image,
            **kwargs)
        return

def compute_widget_properties(who_args, what_args, window_args, properties, variant=None, multiple=None):
    def style_args(d, name):
        style = d.get("style", None)
        if style is None:
            if multiple is None:
                return d
            else:
                style = name
        in_rollback = renpy.exports.in_rollback()
        if (not in_rollback) and (not variant) and (not multiple):
            return d
        d = d.copy()
        if isinstance(style, basestring):
            if multiple is not None:
                style = "block{}_multiple{}_{}".format(multiple[0], multiple[1], style)
            style = getattr(renpy.store.style, style)
            if variant is not None:
                style = style[variant]
            if in_rollback:
                style = style["rollback"]
        d["style"] = style
        return d

    who_args = style_args(who_args, "who")
    what_args = style_args(what_args, "what")
    window_args = style_args(window_args, "window")
    rv = dict(properties)
    for prefix in renpy.config.character_id_prefixes:
        rv[prefix] = style_args(properties.get(prefix, {}), prefix)
    rv["window"] = window_args
    rv["what"] = what_args
    rv["who"] = who_args
    return rv

def show_display_say(who, what, who_args={}, what_args={}, window_args={},
                     image=False, side_image=None, two_window=False,
                     two_window_vbox_properties={},
                     who_window_properties={},
                     say_vbox_properties={},
                     transform=None,
                     variant=None,
                     screen=None,
                     layer=None,
                     properties={},
                     multiple=None,
                     retain=None,
                     **kwargs):
    props = compute_widget_properties(who_args, what_args, window_args, properties, variant=variant, multiple=multiple)
                       
    def handle_who():
        if who:
            if image:
                renpy.ui.add(renpy.display.im.image(who, loose=True, **props["who"])) #type: ignore
            else:
                renpy.ui.text(who, **who_args)
              
    def merge_style(style, properties):
        if isinstance(style, basestring):
            style = getattr(renpy.store.style, style)
        if variant is not None:
            style = style[variant]
        if renpy.exports.in_rollback():
            style = style["rollback"]
        rv = dict(style=style)
        rv.update(properties)
        return rv

    if screen and renpy.display.screen.has_screen(screen):
        if layer is None:
            layer = renpy.config.say_layer
        tag = screen
        if retain:
            tag = retain
        elif multiple:
            if renpy.display.screen.has_screen("multiple_" + screen):
                screen = "multiple_" + screen
                kwargs["multiple"] = multiple
            tag = "block{}_multiple{}_{}".format(multiple[0], multiple[1], tag)
        if image:
            kwargs["image"] = image
        if (side_image is not None) or renpy.config.old_say_args:
            kwargs["side_image"] = side_image
        if two_window or renpy.config.old_say_args:
            kwargs["two_window"] = two_window
        renpy.display.screen.show_screen(
            screen,
            _widget_properties=props,
            _transient=not retain,
            _tag=tag,
            who=who,
            what=what,
            _layer=layer,
            **kwargs)
        renpy.exports.shown_window()
        return (tag, "what", layer)

    if transform:
        renpy.ui.at(transform)
      
    if two_window:
        renpy.ui.vbox(**merge_style('say_two_window_vbox', two_window_vbox_properties))
        renpy.ui.window(**merge_style('say_who_window', who_window_properties))
        handle_who()

    renpy.ui.window(**props["window"])
    renpy.ui.vbox(**merge_style('say_vbox', say_vbox_properties))

    if not two_window:
        handle_who()
      
    rv = renpy.ui.text(what, **props["what"])
    renpy.ui.close()

    if two_window:
        renpy.ui.close()
    if side_image:
        renpy.ui.image(side_image)
    renpy.exports.shown_window()
    return rv

class SlowDone(object):
    delay = None
    ctc_kwargs = { }
    last_pause = True
    no_wait=False
  
    def __init__(self, ctc, ctc_position, callback, interact, type, cb_args, delay, ctc_kwargs, last_pause, no_wait):
        self.ctc = ctc
        self.ctc_position = ctc_position
        self.callback = callback
        self.interact = interact
        self.type = type
        self.cb_args = cb_args
        self.delay = delay
        self.ctc_kwargs = ctc_kwargs
        self.last_pause = last_pause
        self.no_wait = no_wait

    def __call__(self):
        if self.interact and self.delay != 0:
            if renpy.display.screen.has_screen("ctc"):
                if self.ctc:
                    args = [ self.ctc ]
                else:
                    args = [ ]
                renpy.display.screen.show_screen("ctc", *args, _transient=True, _ignore_extra_kwargs=True, **self.ctc_kwargs)
                renpy.exports.restart_interaction()
            elif self.ctc and self.ctc_position == "fixed":
                renpy.display.screen.show_screen("_ctc", _transient=True, ctc=self.ctc)
                renpy.exports.restart_interaction()
        if self.delay is not None:
            renpy.ui.pausebehavior(self.delay, True, voice=self.last_pause and not self.no_wait, self_voicing=self.last_pause)
            renpy.exports.restart_interaction()
        self.callback("slow_done")

afm_text_queue = [ ]

def display_say(
        who,
        what,
        show_function,
        interact,
        slow,
        afm,
        ctc,
        ctc_pause,
        ctc_position,
        all_at_once,
        cb_args,
        with_none,
        callback,
        type, # @ReservedAssignment
        checkpoint=True,
        ctc_timedpause=None,
        ctc_force=False,
        advance=True,
        multiple=None,
        dtt=None,
        retain=False):

    global afm_text_queue

    if multiple is None:
        final = interact
        afm_text_queue = [ ]
    else:
        step, total = multiple
        if step == 1:
            afm_text_queue = [ ]
        if step == total:
            final = interact
        else:
            final = False
            interact = False

    if not final:
        advance = False
    if final and (not renpy.game.preferences.skip_unseen) and (not renpy.game.context().seen_current(True)) and renpy.config.skipping == "fast": # type: ignore
        renpy.config.skipping = None
    if advance and renpy.config.skipping == "fast":
        for i in renpy.config.fast_skipping_callbacks:
            i()
        renpy.exports.with_statement(None)
        renpy.exports.checkpoint(True, hard=checkpoint)
        return

    if interact is False:
        for i in renpy.config.nointeract_callbacks:
            i()
    if callback is None:
        if renpy.config.character_callback:
            callback = [ renpy.config.character_callback ]
        else:
            callback = [ ]
    if not isinstance(callback, list):
        callback = [ callback ]
    callback = renpy.config.all_character_callbacks + callback
    callback = Callbacks(callback, interact, type, cb_args, multiple)

    roll_forward = renpy.exports.roll_forward_info()
    if roll_forward is True:
        roll_forward = False
    after_rollback = renpy.game.after_rollback
    if after_rollback:
        slow = False
        all_at_once = True

    elif (renpy.config.skipping and
          advance and
          (renpy.game.preferences.skip_unseen or
           renpy.game.context().seen_current(True))):
        slow = False
        all_at_once = True

    if not interact or renpy.game.preferences.self_voicing:
        all_at_once = True
    if dtt is None:
        dtt = DialogueTextTags(what)
    if all_at_once:
        pause_start = [ dtt.pause_start[0] ]
        pause_end = [ dtt.pause_end[-1] ]
        pause_delay = [ dtt.pause_delay[-1] ]
    else:
        pause_start = dtt.pause_start
        pause_end = dtt.pause_end
        pause_delay = dtt.pause_delay

    exception = None
    retain_tag = "_retain_0"
    retain_count = -1

    if retain:
        while True:
            retain_count += 1
            retain_tag = "_retain_{}".format(retain_count)
            if not renpy.exports.get_screen(retain_tag):
                break
    callback.what = dtt.text
    callback("begin")
    if dtt.fast:
        for i in renpy.config.say_sustain_callbacks:
            i()

    try:
        for i, (start, end, delay) in enumerate(zip(pause_start, pause_end, pause_delay)):
            last_pause = (i == len(pause_start) - 1)
            pause_callback = callback.copy()
            pause_callback.start = start
            pause_callback.end = end
            pause_callback.delay = delay
            pause_callback.last_segment = last_pause
            if advance:
                behavior = renpy.ui.saybehavior(allow_dismiss=renpy.config.say_allow_dismiss, dialogue_pause=delay)
            else:
                behavior = None
            what_string = dtt.text
            if last_pause:
                what_ctc = ctc
                ctc_kind = "last"
            else:
                if delay is not None:
                    what_ctc = ctc_timedpause or ctc_pause
                    ctc_kind = "timedpause"
                else:
                    what_ctc = ctc_pause
                    ctc_kind = "pause"
            ctc_kwargs = {
                "ctc_kind" : ctc_kind,
                "ctc_last" : ctc,
                "ctc_pause" : ctc_pause,
                "ctc_timedpause" : ctc_timedpause,
            }
            if not (interact or ctc_force):
                what_ctc = None
            what_ctc = renpy.easy.displayable_or_none(what_ctc)
            if (what_ctc is not None) and what_ctc._duplicatable:
                what_ctc = what_ctc._duplicate(None)
                what_ctc._unique()
            if ctc is not what_ctc:
                if (ctc is not None) and ctc._duplicatable:
                    ctc = ctc._duplicate(None)
                    ctc._unique()
            if delay == 0:
                what_ctc = None
                ctc = None
            pause_callback("show")
            slow_done = SlowDone(what_ctc, ctc_position, pause_callback, interact, type, cb_args, delay, ctc_kwargs, last_pause, dtt.no_wait)
            extend_text = ""
            if renpy.config.scry_extend:
                scry = renpy.exports.scry()
                if scry is not None:
                    scry = scry.next()
                scry_count = 0
                while scry and scry_count < 64:
                    if scry.extend_text is renpy.ast.DoesNotExtend:
                        break
                    elif scry.extend_text is not None:
                        extend_text += scry.extend_text
                    scry = scry.next()
                    scry_count += 1
                if extend_text:
                    extend_text = "{done}" + extend_text

            show_args = { }
            if multiple:
                show_args["multiple"] = multiple
            if retain:
                show_args["retain"] = retain_tag

            what_text = show_function(who, what_string, **show_args)
            if isinstance(what_text, tuple):
                if i != 0 and renpy.config.say_replace_event:
                    screen_displayable = renpy.display.screen.get_screen(what_text[0], what_text[2])
                    if screen_displayable is not None:
                        screen_displayable.set_transform_event("replace")
                        if not retain and not last_pause:
                            sls = renpy.game.context().scene_lists
                            sls.set_transient_prefix(what_text[2], what_text[0], "replaced")
                what_text = renpy.display.screen.get_widget(what_text[0], what_text[1], what_text[2])

            if not multiple:
                afm_text_queue = [ what_text ]
            else:
                afm_text_queue.append(what_text)

            if interact or what_string or (what_ctc is not None) or (behavior and afm):
                if not isinstance(what_text, renpy.text.text.Text): # @UndefinedVariable
                    raise Exception("The say screen (or show_function) must return a Text object.")
                if what_ctc:
                    if ctc_position == "nestled":
                        what_text.set_ctc(what_ctc)
                    elif ctc_position == "nestled-close":
                        what_text.set_ctc([ u"\ufeff", what_ctc, ])
                if (not last_pause) and ctc:
                    if ctc_position == "nestled":
                        what_text.set_last_ctc(ctc)
                    elif ctc_position == "nestled-close":
                        what_text.set_last_ctc([ u"\ufeff", ctc, ])
                if what_text.text[0] == what_string:
                    if extend_text:
                        what_text.text[0] += extend_text
                    what_text.start = start
                    what_text.end = end
                    what_text.slow = slow
                    what_text.slow_done = slow_done
                    what_text.update()
                elif renpy.config.developer:
                    raise Exception("The displayable with id 'what' was not given the exact contents of the what variable given to the say screen.")
                if behavior and afm:
                    behavior.set_text(*afm_text_queue)
            else:
                slow = False
            pause_callback("show_done")

            if not slow:
                slow_done()

            if final:
                rv = renpy.ui.interact(mouse='say', type=type, roll_forward=roll_forward)
                if rv is False:
                    break
                if isinstance(rv, (renpy.game.JumpException, renpy.game.CallException)):
                    raise rv
                if not last_pause:
                    for i in renpy.config.say_sustain_callbacks:
                        i()
    except (renpy.game.JumpException, renpy.game.CallException) as e:
        exception = e

    if final:
        if not dtt.no_wait:
            if exception is None:
                renpy.exports.checkpoint(True, hard=checkpoint)
            else:
                renpy.exports.checkpoint(exception)
        else:
            renpy.game.after_rollback = after_rollback
        if with_none is None:
            with_none = renpy.config.implicit_with_none
        renpy.plog(1, "before with none")
        if with_none:
            renpy.game.interface.do_with(None, None)
        renpy.plog(1, "after with none")
    callback("end")
    if exception is not None:
        raise exception

class HistoryEntry(renpy.object.Object):
    multiple = None
    who = None
    what = None

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        return "<History {!r} {!r}>".format(self.who, self.what)

NotSet = renpy.object.Sentinel("NotSet")
multiple_count = 0

class ADVCharacter(object):
    special_properties = [
        'what_prefix',
        'what_suffix',
        'who_prefix',
        'who_suffix',
        'show_function',
        ]

    voice_tag = None
    properties = { }
    _statement_name = None

    def __init__(
            self,
            name=NotSet,
            kind=None,
            **properties):
        if kind is None:
            kind = renpy.store.adv
        if name is not NotSet:
            properties["name"] = name
        
        def v(n):
            if n in properties:
                return properties.pop(n)
            else:
                return getattr(kind, n)

        def d(n):
            if n in properties:
                return properties.pop(n)
            else:
                return kind.display_args[n]

        self.name = v('name')
        self.who_prefix = v('who_prefix')
        self.who_suffix = v('who_suffix')
        self.what_prefix = v('what_prefix')
        self.what_suffix = v('what_suffix')

        self.show_function = v('show_function')
        self.predict_function = v('predict_function')

        self.condition = v('condition')
        self.dynamic = v('dynamic')
        self.screen = v('screen')
        self.mode = v('mode')

        self.voice_tag = v('voice_tag')

        if renpy.config.new_character_image_argument:
            if "image" in properties:
                self.image_tag = properties.pop("image")
            else:
                self.image_tag = kind.image_tag
        else:
            self.image_tag = None

        self.display_args = dict(
            interact=d('interact'),
            slow=d('slow'),
            afm=d('afm'),
            ctc=renpy.easy.displayable_or_none(d('ctc')),
            ctc_pause=renpy.easy.displayable_or_none(d('ctc_pause')),
            ctc_timedpause=renpy.easy.displayable_or_none(d('ctc_timedpause')),
            ctc_position=d('ctc_position'),
            all_at_once=d('all_at_once'),
            with_none=d('with_none'),
            callback=d('callback'),
            type=d('type'),
            advance=d('advance'),
            retain=d('retain'),
            )

        self._statement_name = properties.pop("statement_name", None)
        self.properties = collections.defaultdict(dict)

        if kind:
            self.who_args = kind.who_args.copy()
            self.what_args = kind.what_args.copy()
            self.window_args = kind.window_args.copy()
            self.show_args = kind.show_args.copy()
            self.cb_args = kind.cb_args.copy()
            for k, val in kind.properties.items():
                self.properties[k] = dict(val)
        else:
            self.who_args = { "substitute" : False }
            self.what_args = { "substitute" : False }
            self.window_args = { }
            self.show_args = { }
            self.cb_args = { }
        if not renpy.config.new_character_image_argument:
            if "image" in properties:
                self.show_args["image"] = properties.pop("image")
        if "slow_abortable" in properties:
            self.what_args["slow_abortable"] = properties.pop("slow_abortable")

        prefixes = [ "show", "cb", "what", "window", "who"] + renpy.config.character_id_prefixes
        split_args = [ i + "_" for i in prefixes ] + [ "" ]
        split = renpy.easy.split_properties(properties, *split_args)

        for prefix, dictionary in zip(prefixes, split):
            self.properties[prefix].update(dictionary)

        self.properties["who"].update(split[-1])
        self.show_args.update(self.properties.pop("show"))
        self.cb_args.update(self.properties.pop("cb"))
        self.what_args.update(self.properties.pop("what"))
        self.window_args.update(self.properties.pop("window"))
        self.who_args.update(self.properties.pop("who"))

    def copy(self, name=NotSet, **properties):
        return type(self)(name, kind=self, **properties)

    def do_add(self, who, what, multiple=None):
        return

    def get_show_properties(self, extra_properties):
        screen = self.screen
        show_args = self.show_args
        who_args = self.who_args
        what_args = self.what_args
        window_args = self.window_args
        properties = self.properties

        if extra_properties:
            screen = extra_properties.pop("screen", screen)
            show_args = show_args.copy()
            who_args = who_args.copy()
            what_args = what_args.copy()
            window_args = window_args.copy()
            properties = collections.defaultdict(dict)
            for k, v in self.properties.items():
                properties[k] = v.copy()
            prefixes = [ "show", "cb", "what", "window", "who"] + renpy.config.character_id_prefixes
            split_args = [ i + "_" for i in prefixes ] + [ "" ]
            split = renpy.easy.split_properties(extra_properties, *split_args)
            for prefix, dictionary in zip(prefixes, split):
                properties[prefix].update(dictionary)
            properties["who"].update(split[-1])
            show_args.update(properties.pop("show"))
            who_args.update(properties.pop("who"))
            what_args.update(properties.pop("what"))
            window_args.update(properties.pop("window"))
        return screen, show_args, who_args, what_args, window_args, properties

    def do_show(self, who, what, multiple=None, extra_properties=None, retain=None):
        screen, show_args, who_args, what_args, window_args, properties = self.get_show_properties(extra_properties)
        show_args = dict(show_args)
        if multiple is not None:
            show_args["multiple"] = multiple
        if retain:
            show_args["retain"] = retain
        return self.show_function(
            who,
            what,
            who_args=who_args,
            what_args=what_args,
            window_args=window_args,
            screen=screen,
            properties=properties,
            **show_args)


    def do_done(self, who, what, multiple=None):
        self.add_history("adv", who, what, multiple=multiple)

    def do_extend(self):
        self.pop_history()

    def do_display(self, who, what, **display_args):
        display_say(who,
                    what,
                    self.do_show,
                    **display_args)
      
    def do_predict(self, who, what, extra_properties=None):
        screen, show_args, who_args, what_args, window_args, properties = self.get_show_properties(extra_properties)
        return self.predict_function(
            who,
            what,
            who_args=who_args,
            what_args=what_args,
            window_args=window_args,
            screen=screen,
            properties=properties,
            **show_args)

    def resolve_say_attributes(self, predict, attrs):
        if not attrs:
            return
        if not self.image_tag:
            if attrs and not predict:
                raise Exception("Say has image attributes %r, but there's no image tag associated with the speaking character." % (attrs,))
            else:
                return
        if attrs is None:
            attrs = ()
        else:
            attrs = tuple(attrs)
        tagged_attrs = (self.image_tag,) + attrs
        images = renpy.game.context().images
        layer = renpy.exports.default_layer(None, self.image_tag)
        if images.showing(layer, (self.image_tag,)):
            new_image = images.apply_attributes(layer, self.image_tag, tagged_attrs)
            if new_image is None:
                new_image = tagged_attrs
            if images.showing(layer, new_image, exact=True):
                return
            show_image = (self.image_tag,) + attrs
            if predict:
                renpy.exports.predict_show(new_image)
            else:
                renpy.exports.show(show_image)
                return True

        else:
            if renpy.config.say_attributes_use_side_image:
                tagged_attrs = (renpy.config.side_image_prefix_tag,) + tagged_attrs
                new_image = images.apply_attributes(layer, self.image_tag, tagged_attrs)
                if new_image is None:
                    new_image = tagged_attrs
                images.predict_show(layer, new_image[1:], show=False)
            else:
                images.predict_show(layer, tagged_attrs, show=False)

    def handle_say_attributes(self, predicting, interact):
        attrs = renpy.game.context().say_attributes
        renpy.game.context().say_attributes = None
        temporary_attrs = renpy.game.context().temporary_attributes
        renpy.game.context().temporary_attributes = None
        if interact:
            if temporary_attrs:
                temporary_attrs = list(temporary_attrs)
            else:
                temporary_attrs = [ ]
            if renpy.config.speaking_attribute is not None:
                temporary_attrs.insert(0, renpy.config.speaking_attribute)

        images = renpy.game.context().images
        before = images.get_attributes(None, self.image_tag)
        mode = None
        if self.resolve_say_attributes(predicting, attrs):
            mode = 'permanent'
        if not self.image_tag:
            return None
        if temporary_attrs:
            attrs = images.get_attributes(None, self.image_tag)
            if self.resolve_say_attributes(predicting, temporary_attrs):
                mode = 'both' if mode else 'temporary'
        if mode:
            after = images.get_attributes(None, self.image_tag)
            self.handle_say_transition(mode, before, after)
        if temporary_attrs:
            return (attrs, images)

    def handle_say_transition(self, mode, before, after):
        before = set(before)
        after = set(after)
        if before == after:
            return
        if renpy.config.say_attribute_transition_callback_attrs:
            delta = (before, after)
        else:
            delta = ()
        trans, layer = renpy.config.say_attribute_transition_callback(
            self.image_tag, mode, *delta)
        if trans is not None:
            if layer is None:
                renpy.exports.with_statement(trans)
            else:
                renpy.exports.transition(trans, layer=layer)

    def restore_say_attributes(self, predicting, state, interact):
        if state is None:
            return
        attrs, images = state
        if not self.image_tag:
            return
        if images is not renpy.game.context().images:
            return
        current_attrs = images.get_attributes(None, self.image_tag)
        if attrs == current_attrs:
            return
        image_with_attrs = (self.image_tag,) + attrs + tuple("-" + i for i in current_attrs if i not in attrs)
        if images.showing(None, (self.image_tag,)):
            if not predicting:
                renpy.exports.show(image_with_attrs)
                return True
            else:
                renpy.exports.predict_show(image_with_attrs)

        else:
            images.predict_show(None, image_with_attrs, show=False)

    def __str__(self):
        who = self.name
        if self.dynamic:
            if callable(who):
                who = who()
            else:
                who = renpy.python.py_eval(who)
        rv = renpy.substitutions.substitute(who)[0]
        if PY2:
            rv = rv.encode("utf-8")
        return rv

    def __format__(self, spec):
        return format(str(self), spec)

    def __repr__(self):
        return "<Character: {!r}>".format(self.name)

    def empty_window(self):
        if renpy.config.fast_empty_window and (self.name is None) and not (self.what_prefix or self.what_suffix):
            self.do_show(None, "")
            return
        self("", interact=False, _call_done=False)

    def has_character_arguments(self, **kwargs):
        safe_kwargs_keys = { "interact", "_mode", "_call_done", "multiple", "_with_none" }
        for i in kwargs:
            if i not in safe_kwargs_keys:
                return False
        return True

    def prefix_suffix(self, thing, prefix, body, suffix):
        def sub(s, scope=None, force=False, translate=True):
            return renpy.substitutions.substitute(s, scope=scope, force=force, translate=translate)[0]
        thingvar_quoted = "[[" + thing + "]"
        thingvar = "[" + thing + "]"
        if not renpy.config.new_substitutions:
            return prefix + body + suffix
        elif renpy.config.who_what_sub_compat == 0:
            pattern = sub(prefix + thingvar_quoted + suffix)
            return pattern.replace(thingvar, sub(body))
        elif renpy.config.who_what_sub_compat == 1:
            pattern = sub(sub(prefix) + thingvar_quoted + sub(suffix))
            return pattern.replace(thingvar, sub(body))
        else:
            return (sub(prefix) + sub(body) + sub(suffix))

    def __call__(self, what, interact=True, _call_done=True, multiple=None, **kwargs):
        _mode = kwargs.pop("_mode", None)
        _with_none = kwargs.pop("_with_none", None)
        if kwargs:
            return Character(kind=self, **kwargs)(what, interact=interact, _call_done=_call_done, multiple=multiple, _mode=_mode, _with_none=_with_none)
        if not (self.condition is None or renpy.python.py_eval(self.condition)):
            return True
        if not isinstance(what, basestring):
            raise Exception("Character expects its what argument to be a string, got %r." % (what,))
        if renpy.store._side_image_attributes_reset:
            renpy.store._side_image_attributes = None
            renpy.store._side_image_attributes_reset = False

        global multiple_count
        if multiple is None:
            multiple_count = 0
        else:
            multiple_count += 1
            multiple = (multiple_count, multiple)
            if multiple_count == multiple[1]:
                multiple_count = 0
        if multiple is None:
            old_attr_state = self.handle_say_attributes(False, interact)
            old_side_image_attributes = renpy.store._side_image_attributes
            if self.image_tag:
                attrs = (self.image_tag,) + renpy.game.context().images.get_attributes(None, self.image_tag)
            else:
                attrs = None
            renpy.store._side_image_attributes = attrs
            if not interact:
                renpy.store._side_image_attributes_reset = True
        if renpy.config.voice_tag_callback is not None:
            renpy.config.voice_tag_callback(self.voice_tag)
        try:
            if interact:
                mode = _mode or self.mode
                renpy.exports.mode(mode)
            else:
                renpy.game.context().deferred_translate_identifier = renpy.game.context().translate_identifier
            display_args = self.display_args.copy()
            display_args["interact"] = display_args["interact"] and interact
            if multiple is not None:
                display_args["multiple"] = multiple
            if _with_none is not None:
                display_args["with_none"] = _with_none

            who = self.name
            if self.dynamic:
                if callable(who):
                    who = who()
                else:
                    who = renpy.python.py_eval(who)
            if who is not None:
                who = self.prefix_suffix("who", self.who_prefix, who, self.who_suffix)
            what = self.prefix_suffix("what", self.what_prefix, what, self.what_suffix)
            if multiple is not None:
                self.do_add(who, what, multiple=multiple)
            else:
                self.do_add(who, what)

            dtt = DialogueTextTags(what)
            if renpy.config.history_current_dialogue:
                self.add_history("current", who, what, multiple=multiple)
            self.do_display(who, what, cb_args=self.cb_args, dtt=dtt, **display_args)
            if renpy.config.history_current_dialogue:
                self.pop_history()
            if _call_done and not dtt.has_done:
                if multiple is not None:
                    self.do_done(who, what, multiple=multiple)
                else:
                    self.do_done(who, what)
                if who and isinstance(who, basestring):
                    renpy.exports.log(who)
                renpy.exports.log(what)
                renpy.exports.log("")

        finally:
            if (multiple is None) and interact:
                renpy.store._side_image_attributes = old_side_image_attributes
                if old_attr_state is not None:
                    _, images = old_attr_state
                    before = images.get_attributes(None, self.image_tag)
                if self.restore_say_attributes(False, old_attr_state, interact):
                    after = images.get_attributes(None, self.image_tag)
                    self.handle_say_transition('restore', before, after)

    def statement_name(self):
        if not (self.condition is None or renpy.python.py_eval(self.condition)):
            return "say-condition-false"
        elif self._statement_name is not None:
            return self._statement_name
        else:
            return "say"

    def predict(self, what):
        old_attr_state = self.handle_say_attributes(True, True)
        old_side_image_attributes = renpy.store._side_image_attributes
        if self.image_tag:
            attrs = (self.image_tag,) + renpy.game.context().images.get_attributes("master", self.image_tag)
        else:
            attrs = None
        renpy.store._side_image_attributes = attrs

        try:
            if self.dynamic:
                who = "<Dynamic>"
            else:
                who = self.name
            return self.do_predict(who, what)

        finally:
            renpy.store._side_image_attributes = old_side_image_attributes
            self.restore_say_attributes(True, old_attr_state, True)

    def will_interact(self):
        if not (self.condition is None or renpy.python.py_eval(self.condition)):
            return False
        return self.display_args['interact']

    def add_history(self, kind, who, what, multiple=None, **kwargs):
        history_length = renpy.config.history_length
        if history_length is None:
            return
        if not renpy.store._history:
            return
          
        history = renpy.store._history_list
        h = HistoryEntry()
        h.kind = kind
        h.who = who
        h.what = what
        h.who_args = self.who_args
        h.what_args = self.what_args
        h.window_args = self.window_args
        h.show_args = self.show_args
        h.image_tag = self.image_tag
        h.multiple = multiple

        if renpy.game.context().rollback:
            h.rollback_identifier = renpy.game.log.current.identifier
        else:
            h.rollback_identifier = None

        for k, v in kwargs.items():
            setattr(h, k, v)
        for i in renpy.config.history_callbacks:
            i(h)
        history.append(h)
        while len(history) > history_length:
            history.pop(0)

    def pop_history(self):
        history_length = renpy.config.history_length

        if history_length is None:
            return
        if not renpy.store._history:
            return
        if renpy.store._history_list:
            renpy.store._history_list.pop()


def Character(name=NotSet, kind=None, **properties):
    if kind is None:
        kind = renpy.store.adv
    kind = getattr(kind, "character", kind)
    return type(kind)(name, kind=kind, **properties)

def DynamicCharacter(name_expr, **properties):
    return Character(name_expr, dynamic=True, **properties)
