#  gcompris - play_piano.py
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
# play_piano activity.

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


class Gcompris_play_piano:

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
        self.first = True
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

        gcompris.bar_set(gcompris.BAR_LEVEL)
        gcompris.bar_set_level(self.gcomprisBoard)
        gcompris.bar_location(20, -1, 0.6)

        self.staff = TrebleStaff(100, 80, self.rootitem, numStaves=1)
        self.staff.noteSpacingX = 36
        self.staff.endx = 200

        if level <= 5:
            self.colorCodeNotesButton = textButton(100, 215, _("Color code notes?"), self, 'green')

            self.colorCodeNotesButton.connect("button_press_event", self.color_code_notes)
            gcompris.utils.item_focus_init(self.colorCodeNotesButton, None)
        else:
            self.staff.colorCodeNotes = False

        self.staff.drawStaff()
        self.staff.rootitem.scale(2.0, 2.0)

        self.givenMelody = []
        self.show_melody()
        self.kidsNoteList = []
        self.piano = PianoKeyboard(250, 300, self.rootitem)
        if level >= 4:
            self.piano.blackKeys = True

        self.piano.draw(300, 175, self.keyboard_click)

        textBox(_("Click the piano keys that match the written notes."), 388, 80, self, fill_color='gray', width=200)

        drawBasicPlayHomePagePart2(self)

        self.timers.append(gobject.timeout_add(500, self.staff.playComposition))

    def keyboard_click(self, widget=None, target=None, event=None, numID=None):

        if not numID:
            numID = target.numID

        n = QuarterNote(numID, 'trebleClef', self.staff.rootitem)
        n.play()
        self.kidsNoteList.append(numID)

    def generateMelody(self):
        level = self.gcomprisBoard.level
        if level >= 1:
            options = [1, 2, 3]
            notenum = 3
        if level >= 2:
            options.extend([4, 5, 6])
            notenum = 3
        if level >= 3:
            options.extend([7, 8])
            notenum = 4
        if level >= 4:
            options.extend([-1, -2])
        if level >= 5:
            options.extend([-3, -4, -5])

        newmelody = []
        for ind in range(0, notenum):
            newmelody.append(options[randint(0, len(options) - 1)])
        if newmelody == self.givenMelody:

            return self.generateMelody()
        else:
            return newmelody

    def show_melody(self):
        self.givenMelody = self.generateMelody()

        for item in self.givenMelody:
            note = QuarterNote(item, 'trebleClef', self.staff.rootitem)
            self.staff.drawNote(note)

    def ok_event(self, widget=None, target=None, event=None):
        if not ready(self, 1000):
            return False

        if self.kidsNoteList == self.givenMelody:
            displayHappyNote(self, self.nextChallenge)
        else:
            displaySadNote(self, self.tryagain)

        self.timers.append(gobject.timeout_add(800, self.staff.playComposition))

    def tryagain(self):
        self.kidsNoteList = []

    def nextChallenge(self):
        self.kidsNoteList = []
        self.staff.eraseAllNotes()
        self.show_melody()

    def erase_entry(self, widget, target, event):
        self.kidsNoteList = []

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

        if keyval == gtk.keysyms.BackSpace:

            self.erase_entry()
        elif keyval == gtk.keysyms.Delete:
            if not ready(self, timeouttime=100): return False
            self.erase_entry()
        elif keyval == gtk.keysyms.Return:
            self.ok_event()
        elif keyval == gtk.keysyms.space:
            if not ready(self, timeouttime=50): return False
            self.staff.playComposition()
        else:
            if not ready(self, timeouttime=50): return False
            if not self.first:
                pianokeyBindings(keyval, self)
            else:
                self.first = False
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


    def color_code_notes(self, widget, target, event):
        if not ready(self):
            return False
        if self.staff.colorCodeNotes:
            self.staff.colorCodeNotes = False
            self.staff.colorAllNotes('black')
        else:
            self.staff.colorCodeNotes = True
            self.staff.colorCodeAllNotes()
