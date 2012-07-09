#  gcompris - play_rhythm.py
#
# Copyright (C) 2012 Beth Hadley
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# play_rhythm activity.

import gtk
import gtk.gdk
import gcompris
import gcompris.utils
import gcompris.skin
import goocanvas
import pango
import time
from gcompris import gcompris_gettext as _
from gcomprismusic import *
from random import randint
import random


'''
TODO:
    - write more levels:
        - with eighth notes
        - with rests
    - add metronome to record activity
DONE:
    - more levels:
        - with melodies, and click the piano keyboard
    - write xml documentation

2 & 3.
I know music 21 a little bit, but I'm more a lilypond user. As you are not writing complex music, a simple format based on some text syntax should be enough ( and easily exportable to other programs if needed ). ABC, lilypond and music21 tiny stream notation use a similar syntax (see below for some references):
- a note name (A to G) and r for rests
- some sign to lower or raise a note (flat and sharp)
- eventually, some sign to set the octave (either a number or signs to raise and lower)
- a number to indicate the tempo (2 half note, 4 quarter note and so on)

If you implement such a text based parser, you will be able to re-use the current gettext localization framework to simply "translate" the songs.

'''



class Gcompris_play_rhythm:

    def __init__(self, gcomprisBoard):
        # Save the gcomprisBoard, it defines everything we need
        # to know from the core
        self.gcomprisBoard = gcomprisBoard

        # Needed to get key_press
        gcomprisBoard.disable_im_context = True

        self.gcomprisBoard.level = 1
        self.gcomprisBoard.maxlevel = 6

        self.metronomePlaying = False

        self.timers = []
    def start(self):

        self.recordedHits = []
        self.saved_policy = gcompris.sound.policy_get()
        gcompris.sound.policy_set(gcompris.sound.PLAY_AND_INTERRUPT)
        gcompris.sound.pause()


        # Set the buttons we want in the bar
        gcompris.bar_set(gcompris.BAR_LEVEL)

        # Set a background image
        gcompris.set_default_background(self.gcomprisBoard.canvas.get_root_item())

        # Create our rootitem. We put each canvas item in it so at the end we
        # only have to kill it. The canvas deletes all the items it contains
        # automaticaly.
        self.rootitem = goocanvas.Group(parent=
                                       self.gcomprisBoard.canvas.get_root_item())


        self.display_level(self.gcomprisBoard.level)

    def display_level(self, level):
        drawBasicPlayHomePagePart1(self)
        goocanvas.Rect(parent=self.rootitem,
            x=200, y=160, width=400, height=30,
            stroke_color="black", fill_color='white',
            line_width=3.0)
        writeText(self, _("Beat Count:"), 260, 175)
        gcompris.bar_set(gcompris.BAR_LEVEL)
        gcompris.bar_set_level(self.gcomprisBoard)
        gcompris.bar_location(20, -1, 0.6)

        self.staff = TrebleStaff(450, 175, self.rootitem, numStaves=1)

        self.staff.donotwritenotetext = True
        self.staff.drawPlayingLine = True
        self.staff.noteSpacingX = 36
        self.staff.endx = 200
        self.staff.labelBeatNumbers = True
        self.staff.drawStaff()
        self.staff.rootitem.scale(2.0, 2.0)
        self.staff.rootitem.translate(-350, -75)

        self.givenRhythm = []
        self.show_rhythm()

        drawFillRect(self, 60, 350, 180, 100)
        writeText(self, _("1. Click the play button to hear the rhythm."), 150, 400)
        drawFillRect(self, 300, 350, 200, 100)
        writeText(self, _("2. Beat the drum to the rhythm you heard."), 400, 400)
        drawFillRect(self, 550, 350, 200, 100)
        writeText(self, _("3. Click the okay button when you are done to see if you got it right!"), 650, 400)

        drawFillRect(self, 340, 15, 90, 30)
        writeText(self, _('Drum'), 390, 30)

        # RECORD BUTTON
        self.recordButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('play_rhythm/drumhead.png'),
                x=300,
                y=60,
                )
        self.recordButton.connect("button_press_event", self.record_click)
        gcompris.utils.item_focus_init(self.recordButton, None)

        drawFillRect(self, 15, 60, 150, 80)
        writeText(self, _('Click the Metronome to hear the tempo'), 90, 100)
        # METRONOME BUTTON
        self.metornomeButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('play_rhythm/metronome.png'),
                x=40,
                y=150,
                )
        self.metornomeButton.connect("button_press_event", self.play_metronome)
        gcompris.utils.item_focus_init(self.metornomeButton, None)
        drawBasicPlayHomePagePart2(self)
        self.metronomePlaying = False
        self.timers.append(gobject.timeout_add(500, self.staff.playComposition))
        self.playButton.connect("button_press_event", self.stopMetronome)
        self.okButton.connect("button_press_event", self.stopMetronome)

    def stopMetronome(self, widget=None, target=None, event=None):
        self.metronomePlaying = False

    def play_metronome(self, widget=None, target=None, event=None):
        if not self.metronomePlaying:
            self.timers.append(gobject.timeout_add(500, self.playClick))
            self.metronomePlaying = True
        else:
            self.timers = []
            self.metronomePlaying = False
            gcompris.sound.play_ogg('//boards/sounds/silence1s.ogg')

    def playClick(self):
        if self.metronomePlaying:
            gcompris.sound.play_ogg('play_rhythm/click.wav')
            self.timers.append(gobject.timeout_add(500, self.playClick))

    def keyboard_click(self, widget, target, event):

        if not ready(self):
            return False
        n = QuarterNote(target.name, 'trebleClef', self.staff.rootitem)
        n.play()
        self.kidsNoteList.append(target.name)

    def generateRhythm(self):
        level = self.gcomprisBoard.level
        if level == 1:
            options = [['q', 'q', 'q'], ['h', 'h', 'h'], ['w', 'w', 'w'] ]
        elif level == 2:
            options = [ ['q', 'h'], ['h', 'q'], ['q', 'w'], ['w', 'q'], ['h', 'w'], ['w', 'h']]
        elif level == 3:
            options = [ ['q', 'h', 'q'], ['q', 'w', 'q'], ['h', 'q', 'h'], ['w', 'q', 'w'], ['w', 'h', 'w'], ['h', 'w', 'h']]
        elif level == 4:
            options = [ ['q', 'h', 'q', 'h'], ['h', 'q', 'q', 'q'], ['q', 'h', 'h', 'q'], ['q', 'h', 'q'], ['h', 'h', 'h'] ]
        elif level == 5:
            options = [ ['e', 'e', 'e', 'e'], ['q', 'q', 'q', 'q'], ['h', 'h', 'h', 'h'], ['w', 'w', 'w', 'w'] ]
        elif level == 6:
            options = [ ['q', 'e', 'e', 'q'], ['e', 'e', 'w', 'q'], ['q', 'w', 'e', 'q'], ['w', 'e', 'w', 'e']]

        newrhythm = options[randint(0, len(options) - 1)]
        if newrhythm == self.givenRhythm:

            return self.generateRhythm()
        else:
            return newrhythm

    def show_rhythm(self):
        self.givenRhythm = self.generateRhythm()
        for item in self.givenRhythm:
            if item == 'e':
                note = EighthNote('C', 'trebleClef', self.staff.rootitem)
            elif item == 'q':
                note = QuarterNote('C', 'trebleClef', self.staff.rootitem)
            elif item == 'h':
                note = HalfNote('C', 'trebleClef', self.staff.rootitem)
            elif item == 'w':
                note = WholeNote('C', 'trebleClef', self.staff.rootitem)
            self.staff.drawNote(note)

    def ok_event(self, widget, target, event):
        '''
        DOCS HERE
        '''
        if not ready(self, 1000):
            return False

        # quarter notes = 0.5 seconds
        # half notes = 1 second
        # whole notes = a little less than 2 seconds
        def nearlyEqual(inputNum, correctNum, amountOfError):
            return abs(inputNum - correctNum) <= amountOfError

        self.netOffsets = [0]
        for index, x in enumerate(self.recordedHits[1:]):
            self.netOffsets.append(x - self.recordedHits[index])
        correctedList = []
        if len(self.netOffsets) != len(self.givenRhythm):
            displayIncorrectAnswer(self, self.tryagain)
            return
        for rhythmItem, recordedHit in zip(self.givenRhythm[:-1], self.netOffsets[1:]):
            if rhythmItem == 'e':
                if not nearlyEqual(recordedHit, 0.25, 0.1):
                    displayIncorrectAnswer(self, self.tryagain)
                    return
            if rhythmItem == 'q':
                if not nearlyEqual(recordedHit, 0.5, 0.1):
                    displayIncorrectAnswer(self, self.tryagain)
                    return
            if rhythmItem == 'h':
                if not nearlyEqual(recordedHit, 1.0, 0.2):
                    displayIncorrectAnswer(self, self.tryagain)
                    return
            if rhythmItem == 'w':
                if not nearlyEqual(recordedHit, 2.0, 0.3):
                    displayIncorrectAnswer(self, self.tryagain)
                    return

        displayYouWin(self, self.nextChallenge)
        self.metronomePlaying = False
        self.timers.append(gobject.timeout_add(800, self.staff.playComposition))

    def tryagain(self):
        self.recordedHits = []

    def nextChallenge(self):

        self.recordedHits = []
        self.staff.eraseAllNotes()
        self.show_rhythm()

    def erase_entry(self, widget, target, event):
       # self.startTime = time.time()
        self.recordedHits = []

    def record_click(self, x, y, z):
        if not ready(self):
            return
        if self.recordedHits == []:
            self.startTime = time.time()
            self.recordedHits.append(0.0)
        else:
            netTime = time.time() - self.startTime
            self.recordedHits.append(time.time() - self.startTime)


    def end(self):

        # Remove the root item removes all the others inside it
        self.rootitem.remove()


    def ok(self):
        pass

    def repeat(self):
        pass

    #mandatory but unused yet
    def config_stop(self):
        pass

    # Configuration function.
    def config_start(self, profile):
        pass

    def key_press(self, keyval, commit_str, preedit_str):
        utf8char = gtk.gdk.keyval_to_unicode(keyval)
        strn = u'%c' % utf8char

    def pause(self, pause):
        pass

    def set_level(self, level):
        '''
        updates the level for the game when child clicks on bottom
        left navigation bar to increment level
        '''
        self.gcomprisBoard.level = level
        gcompris.bar_set_level(self.gcomprisBoard)
        self.display_level(self.gcomprisBoard.level)
