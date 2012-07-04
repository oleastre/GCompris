# -*- coding: utf-8 -*-
#  gcompris - piano_player.py
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
# piano_player activity.


'''
TODO:
    - add level allowing changes in tempo?...but it's already pretty complex...
    - write more explanatory help xml

DONE:
    - added more notes (additional levels with flats & sharps)
    - added saving capability (still todo: make implementation cleaner)
    - colored notes on playback
    - added timer for sound playback
    - made objects out of notes
    - fixed issue with double click (see utility function in gcompris music)
    - seperated activity into levels and added text instructions
    - clean up GUI, make more intuitive
    - add 'help' page
    - add color-coding of notes, according to color theory (thanks to
    Olivier Samyn's comment on my blog
    - reset text box on piano player when all erase (hackish - consider fixing implementation)
    - highlight note type selected
    - click on note to listen to it enabled

'''
import gobject
import gtk
import gtk.gdk
import gcompris
import gcompris.utils
import gcompris.skin
import goocanvas
import pango
import gcompris.sound
from gcompris import gcompris_gettext as _
#import sys
#sys.path.append('/home/bhadley/Desktop/')
from gcomprismusic import *

class Gcompris_piano_player:

    def __init__(self, gcomprisBoard):

        # Save the gcomprisBoard, it defines everything we need
        # to know from the core
        self.gcomprisBoard = gcomprisBoard

        self.gcomprisBoard.level = 1
        self.gcomprisBoard.maxlevel = 6

        # Needed to get key_press
        gcomprisBoard.disable_im_context = True

    def start(self):

        # write the navigation bar to bottom left corner
        gcompris.bar_set(gcompris.BAR_LEVEL)
        gcompris.bar_set_level(self.gcomprisBoard)
        gcompris.bar_location(20, -1, 0.6)

        self.saved_policy = gcompris.sound.policy_get()
        gcompris.sound.policy_set(gcompris.sound.PLAY_AND_INTERRUPT)
        gcompris.sound.pause()

        # Set a background image
        gcompris.set_default_background(self.gcomprisBoard.canvas.get_root_item())

        # Create our rootitem. We put each canvas item in it so at the end we
        # only have to kill it. The canvas deletes all the items it contains
        # automaticaly.
        self.rootitem = goocanvas.Group(parent=
                                       self.gcomprisBoard.canvas.get_root_item())


        self.display_level(self.gcomprisBoard.level)

    def display_level(self, level):
        '''
        displays level contents.
        All levels: keyboard, staff, write & erase notes, play composition
        1. treble clef only
        2. bass clef only
        3. note duration choice, treble or bass choice
        4. sharp notes, note duration choice, treble or bass choice
        5. flat notes, note duration choice, treble or bass choice
        6. load and save, only sharp notes, note duration choice, treble or bass choice
        '''
        if self.rootitem:
            self.rootitem.remove()

        self.rootitem = goocanvas.Group(parent=
                                       self.gcomprisBoard.canvas.get_root_item())

        clefDescription = keyboardDescription = True
        if level == 1:
            clefText = _("This is the Treble clef staff, for high pitched notes")
            keyboardText = _("These are the 8 \"white\" keys in an octave")
        elif level == 2:
            clefText = _("This is the Bass clef staff, for low pitched notes")
            keyboardText = _("These keys form the C Major scale")
        elif level == 3:
            clefText = _("Click on the note symbols to write different length notes")
            keyboardText = _("Notes can be many types, such as quarter notes, half notes, and whole notes")
        elif level == 4:
            clefText = _("Sharp notes have a # sign")
            keyboardText = _("The black keys are sharp and flat keys")
        elif level == 5:
            clefText = _("Flat notes have a b sign")
            keyboardText = _("Each black key has two names, one with a flat and one with a sharp")
        elif level == 6:
            keyboardText = _("Now you can compose music! Click to load or save your work")
            clefDescription = False

        # CLEF DESCRIPTION
        if clefDescription:
            goocanvas.Rect(parent=self.rootitem, x=380, y=90, width=240,
                           height=50,
                stroke_color="purple", line_width=3.0)

            self.clefDesciption = goocanvas.Text(
                parent=self.rootitem, x=500, y=115, width=250,
                text=clefText, anchor=gtk.ANCHOR_CENTER,
                alignment=pango.ALIGN_CENTER
                )

        # OUTLINE FOR NOTE NAME TEXT
        goocanvas.Rect(parent=self.rootitem, x=60, y=40, width=120,
                       height=80,
            stroke_color="purple", line_width=3.0)


        # KEYBOARD DESCRIPTION
        if keyboardDescription:
            goocanvas.Rect(parent=self.rootitem, x=87, y=385, width=230,
                           height=65,
                stroke_color="purple", line_width=3.0)

            self.KeyboardDescription = goocanvas.Text(
                parent=self.rootitem, x=200, y=415, width=225,
                text=keyboardText,
                fill_color="black", anchor=gtk.ANCHOR_CENTER,
                alignment=pango.ALIGN_CENTER
                )

#        self.colorCodeNotesButton = goocanvas.Text(
#          parent=self.rootitem,
#          x=345,
#          y=120,
#          width=75,
#          text=_("Color code notes?"),
#          fill_color="black",
#          anchor=gtk.ANCHOR_CENTER,
#          alignment=pango.ALIGN_CENTER
#          )

        self.eraseAllButton = goocanvas.Text(
          parent=self.rootitem,
          x=325.0,
          y=50,
          width=100,
          text=_("Erase All Notes"),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )

        self.eraseNotesButton = goocanvas.Text(
          parent=self.rootitem,
          x=425.0,
          y=50,
          width=100,
          text=_("Erase Last Note"),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )

        self.playCompositionButton = goocanvas.Text(
          parent=self.rootitem,
          x=550,
          y=50,
          width=100,
          text=_("Play Composition"),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )


        if (level > 2):

            self.changeClefButton = goocanvas.Text(
              parent=self.rootitem,
              x=230,
              y=56,
              width=100,
              text=_("Change Staff\nClef"),
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )

        if (level >= 3):
            goocanvas.Text(
              parent=self.rootitem,
              x=680,
              y=50,
              width=100,
              text=_("Change Note Type"),
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )


            self.quarterNoteSelectedButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_player/quarterNote.png'),
                x=630,
                y=80,
                height=45,
                width=20
                )

            self.halfNoteSelected = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_player/halfNote.png'),
                x=660,
                y=80,
                height=45,
                width=20
                )

            self.wholeNoteSelected = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_player/wholeNote.png'),
                x=690,
                y=80,
                height=45,
                width=20
                )

        if (level == 6):
            self.loadButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_player/load.png'),
                x=200,
                y=100,
                height=40,
                width=40
                )

            self.saveButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_player/save.png'),
                x=260,
                y=100,
                height=40,
                width=40
                )

        '''
        create staff instance to manage music data
        treble clef image loaded by default; click button to switch to bass clef
        '''

        if level == 2:
            self.staff = BassStaff(380, 170, self.rootitem)
            self.staff.drawStaff(text='Click a colored box on the keyboard')
        else:
            self.staff = TrebleStaff(380, 170, self.rootitem)
            self.staff.drawStaff(text='Click a colored box on the keyboard')


        '''
        synchronize buttons with events
        '''
        if level > 2:
            self.changeClefButton.connect("button_press_event", self.change_clef_event)
            gcompris.utils.item_focus_init(self.changeClefButton, None)

#        self.colorCodeNotesButton.connect("button_press_event", self.color_code_notes)
#        gcompris.utils.item_focus_init(self.colorCodeNotesButton, None)

        self.eraseNotesButton.connect("button_press_event", self.staff.eraseOneNote)
        gcompris.utils.item_focus_init(self.eraseNotesButton, None)

        self.eraseAllButton.connect("button_press_event", self.staff.eraseAllNotes)
        gcompris.utils.item_focus_init(self.eraseAllButton, None)

        self.playCompositionButton.connect("button_press_event", self.staff.playComposition)
        gcompris.utils.item_focus_init(self.playCompositionButton, None)

        if level >= 3:
            self.quarterNoteSelectedButton.connect("button_press_event", self.staff.updateToQuarter)
            gcompris.utils.item_focus_init(self.quarterNoteSelectedButton, None)

            self.halfNoteSelected.connect("button_press_event", self.staff.updateToHalf)
            gcompris.utils.item_focus_init(self.halfNoteSelected, None)

            self.wholeNoteSelected.connect("button_press_event", self.staff.updateToWhole)
            gcompris.utils.item_focus_init(self.wholeNoteSelected, None)

        if level == 6:
            self.saveButton.connect("button_press_event", self.save_file_event)
            gcompris.utils.item_focus_init(self.saveButton, None)

            self.loadButton.connect("button_press_event", self.load_file_event)
            gcompris.utils.item_focus_init(self.loadButton, None)

        '''
        create piano keyboard for use on every level
        optionally specify to display the "black keys"
        '''
        k = PianoKeyboard(50, 160, self.rootitem)
        if level == 5:
            k.sharpNotation = False
            k.blackKeys = True
        elif level == 4 or level == 6:
            k.blackKeys = True
            k.sharpNotation = True

        k.draw(300, 200, self.keyboard_click)

        Prop = gcompris.get_properties()
        if not (Prop.fx):
            gcompris.utils.dialog(_("Error: This activity cannot be \
played with the\nsound effects disabled.\nGo to the configuration \
dialogue to\nenable the sound."), stop_board)

    def color_code_notes(self, widget, target, event):
        if not ready(self):
            return False
        if self.staff.colorCodeNotes:
            self.staff.colorCodeNotes = False
            self.staff.colorAllNotes('black')
        else:
            self.staff.colorCodeNotes = True
            self.staff.colorCodeAllNotes()

    def save_file_event(self, widget, target, event):
        '''
        method called when 'save' button is pressed
        opens the gcompris file selector to save the music
        calls the general_save function, passes self.staff
        '''
        gcompris.file_selector_save(self.gcomprisBoard,
                                   'comp', '.gcmusic',
                                   general_save, self.staff)
    def load_file_event(self, widget, target, event):
        '''
        method called when 'load' button is pressed
        opens the gcompris file selector to load the music
        calls the general_load function
        '''
        gcompris.file_selector_load(self.gcomprisBoard,
                                           'comp', '.gcmusic',
                                           general_load, self.staff)


    def change_clef_event(self, widget, target, event):
        '''
        method called when button to change clef is pressed
        load in the appropriate new staff image
        re-synchronize all buttons because rootitem changes
        all notes in staff are removed...this can be changed later
        if desired, but could confuse children if more than one clef
        exists in the piece
        '''
        self.staff.clear()
        if self.staff.name == "trebleClef":
            self.staff = BassStaff(380, 170, self.rootitem)
            self.staff.drawStaff(text='Click a colored box on the keyboard')
        else:
            self.staff = TrebleStaff(380, 170, self.rootitem,)
            self.staff.drawStaff(text='Click a colored box on the keyboard')

        #re-establish link to root
        self.eraseNotesButton.connect("button_press_event", self.staff.eraseOneNote)
        gcompris.utils.item_focus_init(self.eraseNotesButton, None)

        self.eraseAllButton.connect("button_press_event", self.staff.eraseAllNotes)
        gcompris.utils.item_focus_init(self.eraseAllButton, None)

        self.playCompositionButton.connect("button_press_event", self.staff.playComposition)
        gcompris.utils.item_focus_init(self.playCompositionButton, None)

        self.quarterNoteSelectedButton.connect("button_press_event", self.staff.updateToQuarter)
        gcompris.utils.item_focus_init(self.quarterNoteSelectedButton, None)

        self.halfNoteSelected.connect("button_press_event", self.staff.updateToHalf)
        gcompris.utils.item_focus_init(self.halfNoteSelected, None)

        self.wholeNoteSelected.connect("button_press_event", self.staff.updateToWhole)
        gcompris.utils.item_focus_init(self.wholeNoteSelected, None)

    def keyboard_click(self, widget, target, event):
        '''
        called whenever a key rectangle is pressed; a note object is created
        with a note name, text is output to canvas, the note sound is generated,
        and the note is drawn on the staff
        '''
        if not ready(self):
            return False

        if self.staff.currentNoteType == 'quarterNote':
            n = QuarterNote(target.name, self.staff.name, self.staff.rootitem)
        elif self.staff.currentNoteType == 'halfNote':
            n = HalfNote(target.name, self.staff.name, self.staff.rootitem)
        elif self.staff.currentNoteType == 'wholeNote':
            n = WholeNote(target.name, self.staff.name, self.staff.rootitem)

        self.staff.writeText('This is the ' + n.niceName + ' key')
        self.staff.drawNote(n)
        n.play()
        n.enablePlayOnClick()
        return False

    def end(self):
        # Remove the root item removes all the others inside it
        self.rootitem.remove()
        gcompris.sound.policy_set(self.saved_policy)
        gcompris.sound.resume()

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

    def pause(self, x):
        pass

    def set_level(self, level):
        '''
        updates the level for the game when child clicks on bottom
        left navigation bar to increment level
        '''
        self.gcomprisBoard.level = level
        gcompris.bar_set_level(self.gcomprisBoard)
        self.display_level(self.gcomprisBoard.level)


def general_save(filename, filetype, staffInstance):
    '''
    called after file selection to save
    '''
    print "filename=%s filetype=%s" % (filename, filetype)
    staffInstance.staff_to_file(filename)

def general_load(filename, filetype, staffInstance):
    '''
    called after file selection to load
    '''
    print "general_load : ", filename, " type ", filetype
    staffInstance.file_to_staff(filename)

def stop_board():
  pass
