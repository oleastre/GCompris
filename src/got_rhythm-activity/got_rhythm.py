#  gcompris - got_rhythm.py
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
# got_rhythm activity.
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
        - with melodies, and click the piano keyboard
    - write xml documentation
'''

'''
documentation of thid module is very poor..will be improved ASAP.
I just wanted to get the code up on github as a proof-of-concept rhythm activity
'''


class Gcompris_got_rhythm:

    def __init__(self, gcomprisBoard):
        # Save the gcomprisBoard, it defines everything we need
        # to know from the core
        self.gcomprisBoard = gcomprisBoard

        # Needed to get key_press
        gcomprisBoard.disable_im_context = True

        self.gcomprisBoard.level = 1
        self.gcomprisBoard.maxlevel = 3

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
        if self.rootitem:
            self.rootitem.remove()

        self.rootitem = goocanvas.Group(parent=
                                       self.gcomprisBoard.canvas.get_root_item())

        # set background
        goocanvas.Image(
            parent=self.rootitem,
            x=0, y=0,
            pixbuf=gcompris.utils.load_pixmap('got_rhythm/background/' + str(level) + '.jpg')
            )

        gcompris.bar_set(gcompris.BAR_LEVEL)
        gcompris.bar_set_level(self.gcomprisBoard)
        gcompris.bar_location(20, -1, 0.6)
        if hasattr(self, 'staff'):
            self.staff.clear()
        self.staff = TrebleStaff(450, 175, self.rootitem, numStaves=1)
        self.staff.donotwritenotetext = True
        self.staff.noteSpacingX = 36
        self.staff.endx = 200
        self.staff.drawStaff()
        self.staff.rootitem.scale(2.0, 2.0)
        self.staff.rootitem.translate(-350, -75)

        self.givenRhythm = []
        self.show_rhythm()


        def writeText(text, x, y):
            goocanvas.Text(
              parent=self.rootitem,
              x=x,
              y=y,
              width=200,
              text='<span font_family="URW Gothic L" size="large" \
              weight="bold">' + text + '</span>',
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER,
              use_markup=True
              )

        def drawfillRect(x, y, w, h):
            goocanvas.Rect(parent=self.rootitem,
                        x=x, y=y, width=w, height=h,
                        stroke_color="black", fill_color='gray',
                        line_width=3.0)
        drawfillRect(60, 350, 180, 100)
        writeText(_("1. Click the play button to hear the rhythm."), 150, 400)
        drawfillRect(300, 350, 200, 100)
        writeText(_("2. Click the record button to enter the rhythm you heard."), 400, 400)
        drawfillRect(550, 350, 200, 100)
        writeText(_("3. Click the okay button when you are done to see if you got it right!"), 650, 400)
        drawfillRect(176, 15, 90, 30)
        writeText('Play', 220, 30)
        drawfillRect(347, 15, 90, 30)
        writeText('Record', 390, 30)
        drawfillRect(506, 15, 90, 30)
        writeText('Okay', 550, 30)

        # PLAY BUTTON
        self.playButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('got_rhythm/playbutton.png'),
                x=170,
                y=50,
                )
        self.playButton.connect("button_press_event", self.staff.playComposition)
        gcompris.utils.item_focus_init(self.playButton, None)


        # RECORD BUTTON
        self.recordButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('got_rhythm/record.png'),
                x=340,
                y=50,
                )
        self.recordButton.connect("button_press_event", self.record_click)
        gcompris.utils.item_focus_init(self.recordButton, None)

        # OK BUTTON
        item = goocanvas.Svg(parent=self.rootitem,
                             svg_handle=gcompris.skin.svg_get(),
                             svg_id="#OK"
                             )
        item.scale(1.4, 1.4)
        item.translate(-170, -400)
        item.connect("button_press_event", self.ok_event)
        gcompris.utils.item_focus_init(item, None)


    def generateRhythm(self):
        level = self.gcomprisBoard.level
        if level == 1:
            options = [ ['q', 'h'], ['h', 'q'], ['q', 'w'], ['w', 'q'], ['h', 'w'], ['w', 'h'] ]
        elif level == 2:
            options = [ ['q', 'q', 'q'], ['q', 'h', 'q'], ['h', 'q', 'q'], ['q', 'q', 'h'], ['h', 'h', 'h'] ]
        elif level == 3:
            options = [ ['q', 'h', 'q', 'h'], ['h', 'q', 'q', 'q'], ['q', 'h', 'h', 'q'], ['q', 'h', 'q'], ['h', 'h', 'h'] ]

        newrhythm = options[randint(0, len(options) - 1)]
        if newrhythm == self.givenRhythm:

            return self.generateRhythm()
        else:
            return newrhythm
    def show_rhythm(self):

        self.givenRhythm = self.generateRhythm()

        for item in self.givenRhythm:
            if item == 'q':
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
        if not ready(self):
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

        displayYouWin(self, self.nextRhythm)



    def tryagain(self):
        self.startTime = time.time()
        self.recordedHits = []

    def nextRhythm(self):
        self.startTime = time.time()
        self.recordedHits = []
        self.staff.eraseAllNotes()
        self.show_rhythm()


    def record_click(self, x, y, z):
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
