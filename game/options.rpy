define config.name = _("Merchnopoly")
define gui.show_name = False
define config.version = ""
define gui.about = _p("""
""")
define build.name = "Merchnopoly"

## Sounds and music ############################################################

define config.has_sound = True
define config.has_music = True
define config.has_voice = True
# define config.sample_sound = "sample-sound.ogg"
# define config.sample_voice = "sample-voice.ogg"
define config.main_menu_music = "talking.mp3"
define config.main_menu_music_fadein = 1.0

## Transitions #################################################################

define config.enter_transition = dissolve
define config.exit_transition = dissolve
define config.end_splash_transition = dissolve
define config.intra_transition = dissolve
define config.after_load_transition = dissolve
define config.end_game_transition = dissolve

## Window management ###########################################################

define config.window = "auto"
define config.window_show_transition = Dissolve(.2)
define config.window_hide_transition = Dissolve(.2)

## Preference defaults #########################################################

default preferences.text_cps = 50
default preferences.afm_time = 15



define config.save_directory = "Merchnopoly-1737802564"
define config.window_icon = "gui/window_icon.png"
init python:
    build.classify('**~', None)
    build.classify('**.bak', None)
    build.classify('**/.**', None)
    build.classify('**/#**', None)
    build.classify('**/thumbs.db', None)
    # build.classify('game/**.png', 'archive')
    # build.classify('game/**.jpg', 'archive')
    build.documentation('*.html')
    build.documentation('*.txt')


# define build.google_play_key = "..."
define build.itch_project = "quokka-studio/merchnopoly"
