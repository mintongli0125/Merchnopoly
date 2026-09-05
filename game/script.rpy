image background = im.FactorScale("background.png", 0.45)
image foreground = im.FactorScale("foreground.png", 0.45)
image white = "#fff"
image eden = Transform(im.FactorScale("eden.png", 0.45), xpos = 0.53)
image edenwalk = im.FactorScale("edenwalk.png", 0.45)
image edenyay = Transform(im.FactorScale("edenyay.png", 0.45), xpos = 0.53)
image edennay = Transform(im.FactorScale("edennay.png", 0.45), xpos = 0.53)
image edenbuy = Transform(im.FactorScale("edenbuy.png", 0.45), xpos = 0.53)
image diva = Transform(im.FactorScale("diva.png", 0.45), xpos = 0.54)
image divawalk = im.FactorScale("divawalk.png", 0.45)
image divayay = Transform(im.FactorScale("divayay.png", 0.45), xpos = 0.54)
image divanay = Transform(im.FactorScale("divanay.png", 0.45), xpos = 0.54)
image divatalk = Transform(im.FactorScale("divatalk.png", 0.45), xpos = 0.54)
image moot = Transform(im.FactorScale("moot.png", 0.45), xpos = 0.53)
image mootwalk = im.FactorScale("mootwalk.png", 0.45)
image mootyay = Transform(im.FactorScale("mootyay.png", 0.45), xpos = 0.53)
image mootnay = Transform(im.FactorScale("mootnay.png", 0.45), xpos = 0.53)
image mootbuy = Transform(im.FactorScale("mootbuy.png", 0.45), xpos = 0.53)
image goth = Transform(im.FactorScale("goth.png", 0.45), xpos = 0.53)
image gothwalk = im.FactorScale("gothwalk.png", 0.45)
image gothyay = Transform(im.FactorScale("gothyay.png", 0.45), xpos = 0.53)
image gothnay = Transform(im.FactorScale("gothnay.png", 0.45), xpos = 0.53)
image gothbuy = Transform(im.FactorScale("gothbuy.png", 0.45), xpos = 0.53)
image anime = Transform(im.FactorScale("anime.png", 0.45), xpos = 0.52)
image animewalk = im.FactorScale("animewalk.png", 0.45)
image animeyay = Transform(im.FactorScale("animeyay.png", 0.45), xpos = 0.52)
image animenay = Transform(im.FactorScale("animenay.png", 0.45), xpos = 0.52)
image animebuy = Transform(im.FactorScale("animebuy.png", 0.45), xpos = 0.52)

default preferences.volume.music = 0.8
default preferences.volume.sfx = 0.8
default preferences.volume.voice = 0.8
default persistent.highscore = 0
default persistent.edentop = False
default persistent.divatop = False
default persistent.animetop = False
default persistent.moottop = False
default persistent.gothtop = False
default last = 0
default money = 0

### nochange / charisma / stay / endshift / surprise
default stay = 4
default charisma = 4
default nochange = 4
default surprise = 4
default moneycolor = "#6699CC"
default currentcolor = "#6699CC"
default moneybackcolor = "#6699CC99"

init:
    $ usehints = False
    $ hint = ""
    $ endshift = False
    $ endgame = False
    $ choiceend = False
    $ renpy.music.register_channel("ambient","sfx",True,tight=True)
    $ _skipping = False
    $ time = 0
    $ timer_jump = 0
    $ bigtime = 0
    $ bigtimer_range = 0

style closestyle_button_text:
    hover_color "#FFA500"
    size 50

screen closestall:
    style_prefix "closestyle"
    frame:
        background "#ffffffCC"
        align (0.95, 0.06)
        textbutton "Close Stall" action Jump("endgame")

screen hintbox:
    frame:
        background "#ffffffCC"
        padding (30, 30)
        align (0.9, 0.1)
        text "[hint]" size 30

screen money:
    frame:
        background moneybackcolor
        padding (130, 50)
        align (0.07, 0.03)
        text "$[money]" size 50 color moneycolor outlines [(4, "#fff", 0, 0), (2, "#000", 0, 0)]

screen summary:
    frame:
        background "#ffffff99"
        padding (100, 100)
        align (0.5, 0.5)
        text "{size=*2}TOTAL: $[money]{/size} [highscorenotif] \nTop customer: [topcus] \nTop patron: [toppat] \nLeast impressed: [worcus] \nStingiest buyer: [worpat]"

screen bigtimer:
    timer 0.01 repeat True action If(bigtime > 0, true=SetVariable('bigtime', bigtime - 0.01), false=[Hide('bigtimer')])
    bar value bigtime range bigtimer_range xalign 0.7 yalign 0.03 xysize(1000,20) left_bar "barleft.png" right_bar "barright.png"

screen countdown:
    if usehints:
        style_prefix "hintstyle"
        frame:
            background "#ffffffCC"
            padding (30, 30)
            align (0.9, 0.1)
            text "[hint]" size 30
    timer 0.01 repeat True action If(time > 0, true=SetVariable('time', time - 0.01), false=[Hide('countdown', transition = Dissolve(0.5)), Jump(timer_jump)])

transform chacharight:
    xcenter -0.05
    linear 6.0 xcenter 1.1
transform chachaleft:
    xzoom -1.0
    xcenter 1.0
    linear 6.0 xcenter -0.1

init python:
    prompts = ["Play House merch spotted?", "OMG Digital Diva Mika?!!", "Gardenia Classroom used to be so peak...", "FREE COMMISSION. FREE COMMISSION", "Fire outfit bro"]
    cutprompts = [prompts[:i] + prompts[i+1:] for i in range(len(prompts))]
    eprompts, dprompts, aprompts, mprompts, gprompts = cutprompts

    class ClearHighscore(Action):
        def __call__(self):
            persistent.highscore = 0
            renpy.restart_interaction()

    highscorenotif = ""
    customers = [0,0,0,0,0]
    patrons = [0,0,0,0,0]
    names = ["Keychain Guy","Harp Diva","Gardenia Fan","Moot?","Bypasser"]

    def charvoice(event, interact = True, voicefile = "edenvoice.mp3", **kwargs):
        if not interact:
            return
        if event == "show_done":
            renpy.sound.play(voicefile)
        elif event == "slow_done":
            renpy.sound.stop()

    def earning(sum,char):
        global money, moneybackcolor, currentcolor, customers, patrons
        customers[char] += 1
        patrons[char] += sum
        money += sum
        if money >= 100:
            moneybackcolor = "#FF8C0099"
            currentcolor = "#FF8C00"
        elif money >= 50:
            moneybackcolor = "#964B0099"
            currentcolor = "#964B00"
        elif money >= 10:
            moneybackcolor = "#AA270499"
            currentcolor = "#AA2704"
        elif money >= 5:
            moneybackcolor = "#02302099"
            currentcolor = "#023020"
        renpy.sound.play("<from 0.4>cashin.mp3")
        renpy.call("blinkmoney")


define e = Character("", what_color="#1F3B4D", window_background=im.MatrixColor("gui/textbox.png", im.matrix.tint(0.8, 0.9, 1.0)), callback = charvoice)
define d = Character("", what_color="#702963", window_background=im.MatrixColor("gui/textbox.png", im.matrix.tint(0.9, 0.7, 1.0)), callback = charvoice, cb_voicefile = "divavoice.mp3")
define a = Character("", what_color="#AA336A", window_background=im.MatrixColor("gui/textbox.png", im.matrix.tint(1.0, 0.8, 1.0)), callback = charvoice, cb_voicefile = "animevoice.mp3")
define m = Character("", what_color="#36454F", window_background=im.MatrixColor("gui/textbox.png", im.matrix.tint(0.6, 0.8, 0.9)), callback = charvoice, cb_voicefile = "mootvoice.mp3")
define g = Character("", what_color="#410200", window_background=im.MatrixColor("gui/textbox.png", im.matrix.tint(1.0, 0.6, 0.6)), callback = charvoice, cb_voicefile = "gothvoice.mp3")

label blinkmoney:
    $ moneycolor = "#00FF00"
    pause 0.2
    $ moneycolor = currentcolor
    pause 0.2
    $ moneycolor = "#00FF00"
    pause 0.2
    $ moneycolor = currentcolor
    pause 0.2
    return

#############################################################################

label splashscreen:
    scene white
    with Pause(1)
    show text "Quokka Studio presents" with dissolve
    with Pause(2)
    hide text with dissolve
    with Pause(0.5)
    return

label start:
    stop music fadeout 3.0
    python:
        _preferences.set_volume('music', 0.3)
        _preferences.set_volume('sound', 0.02)
        renpy.restart_interaction()
    play ambient "talking.mp3"

    define playlist = ["song1.mp3", "song2.mp3", "song3.mp3", "song4.mp3", "song5.mp3"]
    $ renpy.random.shuffle(playlist)
    $ renpy.music.queue(playlist)

    show black onlayer overlay
    scene background
    scene foreground onlayer foreground
    hide black with dissolve

    "Here we are... monthly convention again. I wonder how many people'll show up this time."
    "Seems like there's more stalls than last month... oh boy. Competition."
    "Alright, let's try to earn as much money as we can!!"
    "{i}(Equip a booster:){/i}"
    jump booster

label booster:
    menu:
        "{i}{b}Hints{/b} (recommended for first time players){/i}":
            "{i}{b}Hints{/b} may pop up when navigating dialogue options. (Unlocked by default){/i}"
            menu:
                "Select":
                    $ usehints = True
                "Go back":
                    jump booster

        "Keep the Change: {i}tips++{/i}":
            "{i}Customers likelier to have the right amount of money, or let you keep the change. (Unlocked when {b}Keychain Guy{/b} is top customer / patron){/i}"
            menu:
                "Select" if persistent.edentop:
                    $ nochange = 7
                "Go back":
                    jump booster

        "Pop Sensation: {i}charisma++{/i}":
            "{i}Customers more willing to converse & less easily upset. (Unlocked when {b}Harp Diva{/b} is top customer / patron){/i}"
            menu:
                "Select" if persistent.divatop:
                    $ charisma = 8
                "Go back":
                    jump booster

        "Convo Starter: {i}intrigue++{/i}":
            "{i}When passing by, customers likelier to stay if spoken to. (Unlocked when {b}Gardenia Fan{/b} is top customer / patron){/i}"
            menu:
                "Select" if persistent.animetop:
                    $ stay = 7
                "Go back":
                    jump booster

        "Sleep Catch-Up: {i}close stall early{/i}":
            "{i}Shuts down the stall & ends the game early, for whatever reason. (Unlocked when {b}Moot?{/b} is top customer / patron){/i}"
            menu:
                "Select" if persistent.moottop:
                    $ endshift = True
                "Go back":
                    jump booster

        "Unexpected Treasure: {i}surprise find++{/i}":
            "{i}Customers likelier to consider products they didn't intend to buy. (Unlocked when {b}Bypasser{/b} is top customer / patron){/i}"
            menu:
                "Select" if persistent.gothtop:
                    $ surprise = 7
                "Go back":
                    jump booster

        "None":
            menu:
                "Select":
                    jump cont
                "Go back":
                    jump booster
    jump cont

label cont:
    show screen money with dissolve
    if endshift:
        show screen closestall with dissolve

    $ bigtime = 300
    $ bigtimer_range = 300
    show screen bigtimer with dissolve
    jump choice

label choice:
    window hide
    if bigtime > 2 and not endgame:
        $ renpy.pause(4.0, hard = True)
        $ time = 6
        $ timer_jump = "tooslow"
        $ chara = renpy.random.randint(1,5)
        while chara == last:
            $ chara = renpy.random.randint(1,5)
        if chara == 1:
            jump eden
        elif chara == 2:
            jump diva
        elif chara == 3:
            jump anime
        elif chara == 4:
            jump moot
        elif chara == 5:
            jump goth
    else:
        $ choiceend = True
        play sound "timeup.mp3"
        "Time's up!!"
        jump endgame

############################################################################# EDEN

label eden:
    $ last = 1
    if renpy.random.randint(1,10) <= stay:
        show eden with dissolve
        jump eden1

    if renpy.random.randint(1,2) == 1:
        show edenwalk at chacharight
    else:
        show edenwalk at chachaleft
    if usehints:
        $ hint = "What media might the \ncustomer be interested in?"
    show screen countdown with moveinright
    $ randmenu = renpy.random.randint(1,2)
    $ randprompt = renpy.random.choice(eprompts)
    menu:
        "Play House merch spotted?" if randmenu == 1:
            hide edenwalk with dissolve
            show eden with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump eden1
        "[randprompt]":
            hide edenwalk with dissolve
            show eden with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            if renpy.random.randint(1,10) <= stay:
                jump eden1
        "Play House merch spotted?" if randmenu == 2:
            hide edenwalk with dissolve
            show eden with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump eden1
    window show
    hide screen countdown with moveoutright
    "Wanna check out my merch?"
    e "...?"
    hide eden with dissolve
    "(...He just left.)"

    jump choice

label eden1:
    window show
    "That Atlas keychain is so cute."
    hide eden
    show edenyay
    e "Thanks. I made it myself."
    if usehints:
        $ hint = "Try to say what the \ncustomer likes to hear."
        show screen hintbox with moveinright

    menu:
        "No wonder it's so bad":
            "Damn. I see why it's in such sad shape now."
            hide edenyay
            if renpy.random.randint(1,10) <= charisma:
                show eden
                e "..."
                hide eden
                show edenyay
                e "Well, I'm trying to get better at it. I'm quite content with what progress I've made so far."
                jump eden2
        "Such a dedicated fan":
            "Wow, you're so dedicated!! You've gotta be one of the OG fans."
            jump eden2
    show edennay
    hide screen hintbox with moveoutright
    e "...Wow. This took me a whole weekend and that's all you have to say??"
    e "You're unbelievable. I'm leaving."
    hide edennay with dissolve

    jump choice

label eden2:
    hide edenyay
    show edenbuy
    hide screen hintbox with moveoutright
    e "Play House is a special game to me. Atlas is my favorite character, although he's pretty stupid at times."

    if usehints:
        $ hint = "Maybe don't relate the \ncustomer to someone they \njust called stupid."
        show screen hintbox with moveinright
    menu:
        "You're just like him for real":
            "Well. You quite remind me of that guy yourself."
            if renpy.random.randint(1,10) <= charisma:
                hide edenbuy
                show edenyay
                e "Hah, you think so?"
                e "I'll take that as a compliment."
                "(... ...)"
                jump eden3
        "Atlas art book":
            hide edenbuy
            show edenyay
            jump eden3
    hide screen hintbox with moveoutright
    hide edenbuy
    show edennay
    e "...Wait. What's that supposed to mean."
    e "Are you calling me stupid?"
    "Not necessarily –"
    e "I'm leaving."
    hide edennay with dissolve
    "(...Damn.)"

    jump choice

label eden3:
    hide screen hintbox with moveoutright
    "Well, in that case, you should totally check out my Atlas art book!"
    hide edenyay
    show eden
    e "Ah, right. How much is it?"
    "$25."
    if renpy.random.randint(1,10) > nochange:
        e "Hm... I do have $30."
        $ change = 0
        $ tries = 0
        while change != "5" and tries < 3:
            $ change = renpy.input("{i}Change calculation: 30 - 25 = {/i}").strip()
            $ tries += 1
        if change == "5":
            "Here's your $5 change."
            $ earning(25,0)
            hide eden
        else:
            if renpy.random.randint(1,10) > nochange:
                hide eden
                show edennay
                e "Are you trying to scam me??"
                e "Forget it, I'm leaving."
                hide edennay with dissolve
                "(...Dammit.)"

                jump choice
            else:
                hide eden
                show edenyay
                e "Oh, forget it. You can keep the change."
                $ earning(30,0)
                hide edenyay
    else:
        hide eden
        show edenyay
        $ earning(25,0)
        e "Sure, here's $25."
        hide edenyay
    show edenbuy
    e "Thanks for the art book."
    hide edenbuy with dissolve

    jump choice

############################################################################# DIVA

label diva:
    $ last = 2
    if renpy.random.randint(1,10) <= stay:
        show diva with dissolve
        jump diva1

    if renpy.random.randint(1,2) == 1:
        show divawalk at chacharight
    else:
        show divawalk at chachaleft
    if usehints:
        $ hint = "Twintails... reminds me of \na singing robot popstar."
    show screen countdown with moveinright

    $ randmenu = renpy.random.randint(1,2)
    $ randprompt = renpy.random.choice(dprompts)
    menu:
        "OMG Digital Diva Mika?!!" if randmenu == 1:
            hide divawalk with dissolve
            show diva with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump diva1
        "[randprompt]":
            hide divawalk with dissolve
            show diva with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            if renpy.random.randint(1,10) <= stay:
                jump diva1
        "OMG Digital Diva Mika?!!" if randmenu == 2:
            hide divawalk with dissolve
            show diva with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump diva1
    window show
    hide screen countdown with moveoutright
    "New keychain for your backpack?"
    d "!!"
    hide diva
    show divanay
    d "Sorry..."
    hide divanay with dissolve

    jump choice

label diva1:
    window show
    "Your hairstyle is just like Mika's! Do you like Digital Divas?"
    hide diva
    show divayay
    d "Of course! I'm a Digital Diva producer, actually. I play the harp, and I incorporate a lot of chordophone into my music."
    if usehints:
        $ hint = "Whatever chordophone is, \nmaybe don't question it..."
        show screen hintbox with moveinright

    menu:
        "I've never heard of you":
            "Well... I'm a pretty big fan of the genre. But I've literally never seen anything of that sort on my FYP."
            hide divayay
            show divanay
            d "Tch, so it's true I'm being shadowbanned... the Digital Diva monopoly is worse than I thought..."
            "...??"
            hide divanay
            jump diva2
        "Chordo-what??":
            "What on earth is a chordophone?"
            hide divayay
            if renpy.random.randint(1,10) <= charisma:
                show divatalk
                d "Wow, you don't know what a {i}chordophone{/i} is?"
                hide divatalk
                show divayay
                d "Then it seems like I can teach you a thing or two about music!!"
                hide divayay
                jump diva2
    show diva
    hide screen hintbox with moveoutright
    d "... Huh..."
    hide diva
    show divanay
    d "...My bad for thinking you were a fellow music enthusiast. Goodbye."
    "Huh?? Wait –"
    hide divanay with dissolve
    "(But I like music...)"

    jump choice

label diva2:
    show divayay
    hide screen hintbox with moveoutright
    d "Anyway, let's make a deal. I'll buy all your Mika pins, if you follow me on my 14 streaming platforms."
    hide divayay
    show divatalk
    d "And I {i}am{/i} going to check. You can be sure of that."
    if usehints:
        $ hint = "30 pins are worth quite \na bit. Not a bad bargain."
        show screen hintbox with moveinright

    menu:
        "That is crazy work":
            "14 platforms?? What makes you think I have the time?? Even I'm not that unemployed!"
            if renpy.random.randint(1,10) <= surprise:
                hide divatalk
                show divanay
                hide screen hintbox with moveoutright
                d "..."
                hide divanay
                show diva
                d "{i}(Sigh){/i} Whatever. I'll take one Mika pin."
                d "How much?"
                if usehints:
                    $ hint = "How much is a merch \npin? $3?"
                    show screen hintbox with moveinright
                menu:
                    "$9":
                        hide diva
                        show divanay
                        d "...How many karats is that? I don't want it anymore."
                        hide divanay with dissolve
                        "(Wait... did she say {i}one{/i} or {i}three{/i} pins...?)"
                    "...$4?":
                        d "It better be official merch."
                        "... ... ...Yeah... yeah, of course it is. Uh huh."
                        d "I have $5. Keep the change. And it's @DDivineHarpist on all 14 platforms."
                        $ earning(5,1)
                        hide diva with dissolve
                        "... Thank you?"
            else:
                hide divatalk
                show divanay
                d "Ugh."
                hide divanay with dissolve
                "(She rolled her eyes and left.)"
        "ALL my Mika pins?":
            "Wait, really? All 30 of them?"
            hide divatalk
            show divayay
            hide screen hintbox with moveoutright
            d "What? Those are rookie numbers."
            hide divayay
            show diva
            d "The real question is: will you follow me on all my streaming platforms?"
            if usehints:
                $ hint = "Say yes. 14 times...?"
                show screen hintbox with moveinright
            $ consent = 1
            $ yesorno = renpy.input("{i}Will I?{/i}").strip().lower()
            while consent < 14 and (('y' in yesorno and 'e' in yesorno) or 'ok' in yesorno or 'sure' in yesorno):
                $ consent += 1
                $ yesorno = renpy.input("{i}Will I?{/i}").strip().lower()
            if consent == 14 and (('y' in yesorno and 'e' in yesorno) or 'ok' in yesorno or 'sure' in yesorno):
                hide diva
                show divayay
                d "That's what I like to hear! How much are your pins?"
                "$3 each."
                d "I'll give you $100 if you recommend me to your friends."
                $ earning(100,1)
                "Thank you so much."
                hide divayay with dissolve
                "(...Did she ever mention her username??)"
            else:
                hide diva
                show divanay
                d "Ugh."
                hide divanay with dissolve
                "(She rolled her eyes and left.)"
    hide screen hintbox with moveoutright
    jump choice

############################################################################# ANIME

label anime:
    $ last = 3
    if renpy.random.randint(1,10) <= stay:
        show anime with dissolve
        jump anime1

    if renpy.random.randint(1,2) == 1:
        show animewalk at chacharight
    else:
        show animewalk at chachaleft
    if usehints:
        $ hint = "Maybe she enjoys old \nclassics..."
    show screen countdown with moveinright

    $ randmenu = renpy.random.randint(1,2)
    $ randprompt = renpy.random.choice(aprompts)
    menu:
        "Gardenia Classroom used to be so peak..." if randmenu == 1:
            hide animewalk with dissolve
            show anime with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump anime1
        "[randprompt]":
            hide animewalk with dissolve
            show anime with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            if renpy.random.randint(1,10) <= stay:
                jump anime1
        "Gardenia Classroom used to be so peak..." if randmenu == 2:
            hide animewalk with dissolve
            show anime with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump anime1
    window show
    hide screen countdown with moveoutright
    "50\% off on my OC art."
    hide anime
    show animeyay
    a "Oh wow... they look so cute!"
    hide animeyay
    show anime
    a "But it's not exactly what I'm looking for, sorry... I'll come back if I have any change."
    hide anime with dissolve
    "(Why does nobody ask about my OC's?)"

    jump choice

label anime1:
    window show
    "Everyone was binge-watching Gardenia in 2020. But nobody talks about it anymore."
    hide anime
    show animeyay
    a "Wow, are you a Gardenia Classroom fan? Rare catch."
    hide animeyay
    show anime
    a "What do you think of the new spin-off?"
    if usehints:
        $ hint = "Seems like she's fonder \nof the original series."
        show screen hintbox with moveinright

    menu:
        "It's good":
            if renpy.random.randint(1,10) <= charisma:
                "It's pretty good. Honestly, I think the animation quality's improved with this one."
                hide anime
                show animeyay
                a "Oh yes, I completely agree. Everything's upgraded from the background art to the music. It's got a quaint slice-of-life feel."
                hide animeyay
                show anime
                a "Wish we had this level of production with the original series..."
            else:
                "Well, I'm glad they focused on Zeta and Mabel this time, I'm sick of the original cast anyway."
                hide anime
                show animenay
                a "Huh... I mean, I do enjoy their characters, but it seemed like a pretty generic high-school romance to me."
                "Eh, I guess. But it made Gardenia popular again."
                a "Right."
                hide animenay
            jump anime2
            
        "Ehhh...":
            "Honestly? I think the original series was better. The spin-off's just some generic high-school romance."
            hide anime
            show animebuy
            a "Yeah, I know what you mean. There's a philosophy to the main series that got lost with this one."
            "(I mean, it's really just the power of friendship and whatnot, but...)"
            hide animebuy
            jump anime2

label anime2:
    show anime
    hide screen hintbox with moveoutright
    a "So, what Gardenia merch do you have?"
    if usehints:
        $ hint = "She's not super into the \nwhole \"Zebel\" ship, so..."
        show screen hintbox with moveinright

    menu:
        "Zebel poster":
            "Some Zebel posters. They're really popular."
            if renpy.random.randint(1,10) <= surprise:
                hide anime
                show animenay
                a "Ah... nothing from the original series?"
                "Sorry."
                hide animenay
                show anime
                a "It's okay. How much is one of these posters?"
                "$15."
                if renpy.random.randint(1,10) > nochange:
                    a "I have $20, if that's alright."
                    $ change = 0
                    $ tries = 0
                    while change != "5" and tries < 3:
                        $ change = renpy.input("{i}Change calculation: 20 - 15 = {/i}").strip()
                        $ tries += 1
                    if change == "5":
                        "Here's your $5 change."
                        $ earning(15,2)
                        hide anime
                        show animebuy
                        a "Thanks."
                        hide animebuy with dissolve
                    else:
                        if renpy.random.randint(1,10) > nochange:
                            hide anime
                            show animenay
                            a "...On second thought, it's okay, you can keep the poster."
                            hide animenay with dissolve
                            "(Am I sabotaging myself?)"
                        else:
                            hide anime
                            show animebuy
                            a "Never mind, keep the change. Thanks for the poster."
                            $ earning(20,2)
                            hide animebuy with dissolve                    
                else:
                    hide anime
                    show animebuy
                    a "Alright, let's see... $15."
                    $ earning(15,2)
                    a "Thanks for the poster."
                    hide animebuy with dissolve

            else:
                hide anime
                show animenay
                a "...Zebel?? What kind of a name..."
                a "Ah, I mean... the poster's cute, but I'm more interested in the original series."
                "Oh. Well. I'm not sure if you'll find anything like that here."
                a "{i}(Sigh){/i} I know. Thanks anyway."
                hide animenay with dissolve
        "...Or, commission?": 
            "I have some Zebel posters. But if you prefer the series you can commission me."
            hide anime
            show animeyay
            a "Oh, that'd be fantastic! How much would that be?"
            "$10 headshot, $20 bust-up, $45 full body. Half price for any extra characters."
            hide animeyay
            show anime
            a "Hm... how about the main trio, bust-up? $40?"
            "Yes."
            hide anime
            show animebuy
            if renpy.random.randint(1,10) <= surprise:
                a "Actually, I'll have a headshot of the protag too, since I have $50."
                $ earning(50,2)
            else:
                a "Let's see... $40! There we go."
                $ earning(40,2)
            hide animebuy
            show animeyay
            a "I don't see much Gardenia merch anymore that's not about the new spin-off. You're a lifesaver."
            a "I'll DM you for the finished art."
            hide animeyay with dissolve
            "(This'll show my parents.)"

    hide screen hintbox with moveoutright
    jump choice

############################################################################# MOOT

label moot:
    $ last = 4
    if renpy.random.randint(1,10) <= stay:
        show moot with dissolve
        jump moot1

    if renpy.random.randint(1,2) == 1:
        show mootwalk at chacharight
    else:
        show mootwalk at chachaleft
    if usehints:
        $ hint = "Looks like a fellow artist!"
    show screen countdown with moveinright

    $ randmenu = renpy.random.randint(1,2)
    $ randprompt = renpy.random.choice(mprompts)
    menu:
        "FREE COMMISSION. FREE COMMISSION" if randmenu == 1:
            hide mootwalk with dissolve
            show moot with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump moot1
        "[randprompt]":
            hide mootwalk with dissolve
            show moot with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            if renpy.random.randint(1,10) <= stay:
                jump moot1
        "FREE COMMISSION. FREE COMMISSION" if randmenu == 2:
            hide mootwalk with dissolve
            show moot with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump moot1
    window show
    hide screen countdown with moveoutright
    "Want a poster? It's the newest official art."
    m "Official...? Eh."
    hide moot with dissolve
    "(Wow, rude.)"

    jump choice

label moot1:
    window show
    "I'll draw you anything. First time's for free. Please."
    m "Wow, no commissions? ...You aren't seriously gonna draw for free, are ya?"
    if usehints:
        $ hint = "He's not too keen on \nfree commissions, is he?"
        show screen hintbox with moveinright

    menu:
        "I am.":
            "At this rate I might as well be paying people to commission me..."
            hide moot
            if renpy.random.randint(1,10) <= charisma:
                show mootbuy
                m "Hah. Don't be so pessimistic. I'm sure someone'll come around eventually."
                "Why would they? There's always better artists. And AI's free."
                hide mootbuy
                show mootnay
                m "You aren't serious. Don't give me that AI bullshit."
                hide mootnay
                show moot
                m "You put time and effort into your work. That's what people look for when they see art. Don't sell yourself so short."
                "Thanks. I guess."
                jump moot2
        "Obviously not":
            "Of course not. Nobody does things for free."
            m "Of course."
            "But I'll give you a 70\% discount since business isn't exactly booming right now."
            hide moot
            show mootbuy
            m "Well, aren't you generous."
            hide mootbuy
            show moot
            jump moot2
    show mootnay
    hide screen hintbox with moveoutright
    m "Damn, you're unambitious. What about the hours you spent honing your craft? What happened to having some {i}pride{/i} about your art??"
    m "There's no way we'll all go broke..."
    hide mootnay with dissolve
    "(Hard to say.)"

    jump choice

label moot2:
    hide screen hintbox with moveoutright
    m "Let me see your art."
    "(Great. He's checking out my prints.)"
    m "... ... ..."
    m "Hold up, aren't you one of my mutuals?? @nailclipper_draws, right?"
    if usehints:
        $ hint = "Play along. Play along"
        show screen hintbox with moveinright

    menu:
        "UHH maybe":
            "I mean... uh..."
            hide moot
            show mootyay
            m "Hah, yes! I can recognize that art style from a mile away. I mean, what are the chances we'd live in the same city?"
            "Ha... ha... yeah right...??"
            m "Actually, haven't I commissioned you before? Full body's $30, right?"
            "Well – it's – actually $45."
            hide mootyay
            show moot
            m "Ah, you've raised your prices? I didn't know that."
            hide moot
            show mootbuy
            m "Eh, but we're mutuals, right? You know I gotta support my moots. Can I commission a full body of my favorite Digital Diva?"
            "??? Who??"
            hide mootbuy
            show mootnay
            hide screen hintbox with moveoutright
            m "You should know if you've seen my newest posts."
            "Uhhh... right, it's..."
            if usehints:
                $ hint = "He'd probably go for \nthe niche option."
                show screen hintbox with moveinright

            menu:
                "Mika?":
                    "Mika, right?"
                    if renpy.random.randint(1,10) <= charisma:
                        m "... Her name's {i}Gimu{/i}."
                        "Right."
                        hide mootnay
                        show moot
                        jump moot3
                    else:
                        jump moot4
                "Gimu?":
                    "Gimu, right?"
                    hide mootnay
                    show mootyay
                    m "See, I knew you'd remember."
                    hide mootyay
                    show moot
                    jump moot3

        "Nail clipper?":
            "What kind of a dumbass username is that??"
            hide moot
            show mootnay
            hide screen hintbox with moveoutright
            m "Wait – not you? I swear I recognize that art style from somewhere."
            "..."
            m "..."
            m "Never mind. This is embarrassing. I'm gonna go."
            "... But are you sure you don't wanna consider –"
            hide mootnay with dissolve

            jump choice

label moot3:
    hide screen hintbox with moveoutright
    m "Anyway, Gimu's latest design if that's alright. $45?"
    "Yeah, just add me on this username right there."
    hide moot
    show mootnay
    m "...Wait. That's not @nailclipper_draws."
    if usehints:
        $ hint = "Tell a white lie."
        show screen hintbox with moveinright

    menu:
        "Umm...":
            jump moot4
        "It's my alt!!":
            "Yeah, uhh... it's my alt account."
            hide mootnay
            show mootbuy
            m "Ah, I see, I see. Didn't want followers recognizing you in public? Don't worry, I won't tell."
            if renpy.random.randint(1,10) <= nochange:
                $ earning(50,3)
                m "Keep the change, eh?"
            else:
                $ earning(45,3)
            hide mootbuy
            show mootyay
            m "Talk to you later."
            "...Yeah."
            hide mootyay with dissolve
            hide screen hintbox with moveoutright
            jump choice

label moot4:
    hide screen hintbox with moveoutright
    m "...No. You aren't my mutual. Who are you?"
    m "Damn, I almost let myself feel obliged to buy from you. Turns out you were just scamming me."
    if renpy.random.randint(1,10) <= surprise:
        hide mootnay
        show moot
        m "...Although I guess your art looks decent..."
        m "Whatever. I'll take a bust-up of Gimu's new design, if you don't mind."
        "That'll be $20."
        $ earning(20,3)
        m "Thanks."
        hide moot
        show mootnay
        m "I'll be keeping a {i}close{/i} eye on your account, though. So don't try scamming me again."
    else:
        m "Goodbye."

    hide mootnay with dissolve
    jump choice

############################################################################# GOTH

label goth:
    $ last = 5
    if renpy.random.randint(1,10) <= stay:
        show goth with dissolve
        jump goth1

    if renpy.random.randint(1,2) == 1:
        show gothwalk at chacharight
    else:
        show gothwalk at chachaleft
    if usehints:
        $ hint = "Not an anime fan. But \nshe's pretty fashionable..."
    show screen countdown with moveinright

    $ randmenu = renpy.random.randint(1,2)
    $ randprompt = renpy.random.choice(gprompts)
    menu:
        "Fire outfit bro" if randmenu == 1:
            hide gothwalk with dissolve
            show goth with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump goth1
        "[randprompt]":
            hide gothwalk with dissolve
            show goth with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            if renpy.random.randint(1,10) <= stay:
                jump goth1
        "Fire outfit bro" if randmenu == 2:
            hide gothwalk with dissolve
            show goth with dissolve
            hide screen countdown with moveoutright
            $ timer_jump = 0
            jump goth1
    window show
    "So who's your favorite Digital Diva?"
    hide goth
    show gothyay
    hide screen countdown with moveoutright
    g "Ah, I don't really listen to them. I'm more of a Drop Out Guys fan. Thanks though."
    hide gothyay with dissolve
    "(Damn, I should've asked where she got that jacket.)"

    jump choice

label goth1:
    window show
    "I love your outfit! Where'd you get that jacket?"
    hide goth
    show gothyay
    g "Oh, I bought it online. I could give you the link if you want."
    if usehints:
        $ hint = "Don't talk about anime."
        show screen hintbox with moveinright

    menu:
        "Do you cosplay?":
            "Do you cosplay? You'd look brilliant in a Mortal Diary costume."
            hide gothyay
            if renpy.random.randint(1,10) <= surprise:
                show goth
                g "Cosplay...? Why, I've never really tried it."
                hide goth
                show gothyay
                g "You think I have the looks for it, eh? Glad to hear."
                jump goth2
        "And that shirt...":
            "And is that a Drop Out Guys band shirt? I'm in love."
            g "Haha, are you a fan of them too? Their latest album is really something else."
            "You'd really like Mortal Diary, I think. The fanbase's full of pop-punk enthusiasts. You'd fit right in."
            jump goth2
    show goth
    hide screen hintbox with moveoutright
    g "Ah right, this is an anime convention, isn't it..."
    g "Not really my thing, sorry. Good luck with your business though."
    hide goth with dissolve
    "(Of all the places she could've picked to take a stroll...)"

    jump choice

label goth2:
    hide gothyay
    show goth
    hide screen hintbox with moveoutright
    g "I mean, I'm not too familiar with anime and all that. I've watched a bit with my friends, but I don't think it's for me."
    if usehints:
        $ hint = "Don't talk about anime."
        show screen hintbox with moveinright

    menu:
        "What about games?":
            "Hm. What about video games?"
            jump goth3
        "There's an anime for everyone":
            "What?? There's always an anime for everyone. There's so many different genres, you just gotta find the one you like."
            if renpy.random.randint(1,10) <= surprise:
                g "Hmm... maybe you're right. I'm more of a fan of 3D animation, though."
                "Maybe you'd like games, then? I've got a ton of indie game merch here."
                jump goth3
    g "I... guess can see why –"
    hide screen hintbox with moveoutright
    "No seriously, everyone watches anime nowadays. You have to try a couple more classics before you drop it altogether."
    hide goth
    show gothnay
    g "... I'm not too hung up on finding my genre of anime, honestly."
    "But it's so cool! You have to watch Mortal Diary, if nothing else. You'll be amazed!"
    g "Maybe if I have the time. Bye."
    "Wait, where are you –"
    hide gothnay with dissolve
    "(Ugh, I was gonna ask her to buy my prints.)"

    jump choice

label goth3:
    hide goth
    show gothbuy
    hide screen hintbox with moveoutright
    g "Games? Now that's something I can get behind."
    "Have you heard of this indie game called Play House? It's all the rage right now. I have plushies of the protag Atlas, and Eden, and..."
    hide gothbuy
    show goth
    g "Oh, what about that insane-looking one? Looks like a rotten strawberry."
    "Ah, well, that's basically what he is. He's this sort of humanoid lunatic strawberry... it's a long story."
    hide goth
    show gothyay
    g "Lunatic strawberry, huh? He's kind of cute. How much is it?"
    "$40."
    if renpy.random.randint(1,10) > nochange:
        hide gothyay
        show goth
        g "Aw, pricey... can't I have it for $30?"
        if renpy.random.randint(1,10) > charisma:
            "No. But I guess I can do $35."
            hide goth
            show gothyay
            g "Now we're talking. I do have $40... but I'll be wanting my change, yeah?"
            $ change = 0
            $ tries = 0
            while change != "5" and tries < 3:
                $ change = renpy.input("{i}Change calculation: 40 - 35 = {/i}").strip()
                $ tries += 1
            if change == "5":
                "There you go, $5."
                $ earning(35,4)
                hide gothyay
            else:
                if renpy.random.randint(1,10) > nochange:
                    hide gothyay
                    show goth
                    g "... Never mind. I'll have a think about the plushie."
                    hide goth with dissolve
                    "(Damn... I should've paid attention in maths...)"
                    jump choice
                else:
                    g "You know what, keep the change. Guess I can pay full price for this silly little berry."
                    $ earning(40,4)
                    hide gothyay
        else:
            "What on earth, I guess $30's fine."
            $ earning(30,4)
            hide goth
    else:
        $ earning(40,4)
        g "There you go, $40."
        hide gothyay
    show gothbuy
    g "Thanks for the plushie. What's the game called again? Play House? I'll check it out."
    hide gothbuy with dissolve
    "(Didn't think someone'd actually buy that plushie.)"
    "(Eh. I guess it is cute... in a mildly grotesque way.)"

    jump choice

#############################################################################

label tooslow:
    hide edenwalk
    hide divawalk
    hide animewalk
    hide mootwalk
    hide gothwalk
    jump choice

label endgame:

    $ endgame = True

    if not choiceend:
        play sound "timeup.mp3"
        "Time's up!!"

    hide screen bigtimer
    hide screen money
    stop music fadeout 5.0
    stop ambient fadeout 5.0

    if money > persistent.highscore:
        $ highscorenotif = "(New high score!)"
        $ persistent.highscore = money
    $ topcus = names[customers.index(max(customers))]
    $ toppat = names[patrons.index(max(patrons))]
    $ worcus = names[customers.index(min(customers))]
    $ worpat = names[patrons.index(min(patrons))]
    if topcus == "Keychain Guy" or toppat == "Keychain Guy":
        $ persistent.edentop = True
    if topcus == "Harp Diva" or toppat == "Harp Diva":
        $ persistent.divatop = True
    if topcus == "Gardenia Fan" or toppat == "Gardenia Fan":
        $ persistent.animetop = True
    if topcus == "Moot?" or toppat == "Moot?":
        $ persistent.moottop = True
    if topcus == "Bypasser" or toppat == "Bypasser":
        $ persistent.gothtop = True

    show screen summary with dissolve
    pause 5.5
    "{i}(Click to close stall){/i}"
    hide screen closestall with dissolve
    hide screen summary with dissolve
    show black onlayer foreground with dissolve
    pause 0.5
    hide black with dissolve

    return