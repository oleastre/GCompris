# -*- coding: utf-8 -*-
#  gcompris - piano_composition.py
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
# piano_composition activity.


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

from gcomprismusic import *

class Gcompris_piano_composition:

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

        self.first = True # random variable used for key clicks

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
        (7. invisible, loads melodies)
        '''
        if self.rootitem:
            self.rootitem.remove()

        self.rootitem = goocanvas.Group(parent=
                                       self.gcomprisBoard.canvas.get_root_item())
        if level == 7:
            self.displayMelodySelection()
            return

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
            clefText = _("Compose music now! Click to load or save your work")
            keyboardDescription = False

        # CLEF DESCRIPTION
        if clefDescription:
            textBox(clefText, 550, 67, self, 240, stroke_color='purple')

        # KEYBOARD DESCRIPTION
        if keyboardDescription:
            textBox(keyboardText, 200, 430, self, 225, stroke_color='purple')

        # ADD BUTTONS    

        self.eraseAllButton = textButton(100, 70, _("Erase All Notes"), self, 'purple', 80)

        self.eraseNotesButton = textButton(220, 70, _("Erase Last Note"), self, 'teal', 100)

        self.playCompositionButton = textButton(350, 70, _("Play Composition"), self, 'green', 100)

        if (level > 2):

            self.changeClefButton = textButton(100, 140, _("Change Staff Clef"), self, 'gray', 100)

        if (level >= 3):
            self.textbox = goocanvas.Text(
                parent=self.rootitem,
                x=210, y=140,
                width=100,
                text=_("Change Note Type:"),
                fill_color="black", anchor=gtk.ANCHOR_CENTER,
                alignment=pango.ALIGN_CENTER
                )

            x = 260
            y = 115

            # WRITE NOTE BUTTONS TO SELECT NOTE DURATION
            self.eighthNoteSelectedButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/quarterNote.png'),
                x=x,
                y=y,
                height=45,
                width=20
                )

            goocanvas.Image(
              parent=self.rootitem,
              pixbuf=gcompris.utils.load_pixmap("piano_composition/flag.png"),
              x=x + 17,
              y=y + 5 ,
              height=33,
              width=10
              )

            self.quarterNoteSelectedButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/quarterNote.png'),
                x=x + 30,
                y=y,
                height=45,
                width=20
                )

            self.halfNoteSelected = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/halfNote.png'),
                x=x + 55,
                y=y,
                height=45,
                width=20
                )

            self.wholeNoteSelected = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/wholeNote.png'),
                x=x + 80,
                y=y,
                height=45,
                width=20
                )

        if (level == 6):
            self.loadButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/load.png'),
                x=680,
                y=45,
                height=40,
                width=40
                )

            self.saveButton = goocanvas.Image(
                parent=self.rootitem,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/save.png'),
                x=735,
                y=45,
                height=40,
                width=40
                )
            self.loadSongsButton = textButton(200, 430, _("Load Music"), self, 'red', 100)

        '''
        create staff instance to manage music data
        treble clef image loaded by default; click button to switch to bass clef
        '''

        if level == 2:
            self.staff = BassStaff(370, 185, self.rootitem, 3)
            self.staff.drawStaff()
            self.staff.dynamicNoteSpacing = True
        else:
            self.staff = TrebleStaff(370, 185, self.rootitem, 3)
            self.staff.drawStaff()
            self.staff.dynamicNoteSpacing = True

        '''
        synchronize buttons with events
        '''
        if level > 2:
            self.changeClefButton.connect("button_press_event", self.change_clef_event)
            gcompris.utils.item_focus_init(self.changeClefButton, None)

        self.eraseNotesButton.connect("button_press_event", self.staff.eraseOneNote)
        gcompris.utils.item_focus_init(self.eraseNotesButton, None)

        self.eraseAllButton.connect("button_press_event", self.staff.eraseAllNotes)
        gcompris.utils.item_focus_init(self.eraseAllButton, None)

        self.playCompositionButton.connect("button_press_event", self.staff.playComposition)
        gcompris.utils.item_focus_init(self.playCompositionButton, None)

        if level >= 3:
            self.eighthNoteSelectedButton.connect("button_press_event", self.staff.updateToEighth)
            gcompris.utils.item_focus_init(self.eighthNoteSelectedButton, None)

            self.quarterNoteSelectedButton.connect("button_press_event", self.staff.updateToQuarter)
            gcompris.utils.item_focus_init(self.quarterNoteSelectedButton, None)

            self.halfNoteSelected.connect("button_press_event", self.staff.updateToHalf)
            gcompris.utils.item_focus_init(self.halfNoteSelected, None)

            self.wholeNoteSelected.connect("button_press_event", self.staff.updateToWhole)
            gcompris.utils.item_focus_init(self.wholeNoteSelected, None)

            # draw focus rectangle around quarter note duration, the default
            self.staff.drawFocusRect(-82, -70)

        if level == 6:
            self.saveButton.connect("button_press_event", self.save_file_event)
            gcompris.utils.item_focus_init(self.saveButton, None)

            self.loadButton.connect("button_press_event", self.load_file_event)
            gcompris.utils.item_focus_init(self.loadButton, None)

            self.loadSongsButton.connect("button_press_event", self.load_songs_event)
            gcompris.utils.item_focus_init(self.loadSongsButton, None)
        '''
        create piano keyboard for use on every level
        optionally specify to display the "black keys"
        '''
        self.keyboard = PianoKeyboard(50, 180, self.rootitem)
        if level == 5:
            self.keyboard.sharpNotation = False
            self.keyboard.blackKeys = True
        elif level == 4 or level == 6:
            self.keyboard.blackKeys = True
            self.keyboard.sharpNotation = True

        self.keyboard.draw(300, 200, self.keyboard_click)

        Prop = gcompris.get_properties()
        if not (Prop.fx):
            gcompris.utils.dialog(_("Error: This activity cannot be \
played with the\nsound effects disabled.\nGo to the configuration \
dialogue to\nenable the sound."), stop_board)

    def displayMelodySelection(self):
        '''
        parse the text file melodies.txt and display the melodies for selection
        '''
        goocanvas.Text(parent=self.rootitem,
         x=290,
         y=30,
         text='<span font_family="Arial" size="15000" \
         weight="bold">' + _('Select A Melody to Load') + '</span>',
         fill_color="black",
         use_markup=True,
         pointer_events="GOO_CANVAS_EVENTS_NONE"
         )

        file = open(gcompris.DATA_DIR + '/piano_composition/melodies.txt' , 'r')
        songList = []
        lineCnt = 1
        newSong = {}
        for line in file:
            if line == '\n':
                newSong = {}
                lineCnt = 1
                continue
            if lineCnt == 1:
                newSong['title'] = line.strip()
                lineCnt += 1
            elif lineCnt == 2:
                newSong['origin'] = line.strip()
                lineCnt += 1
            elif lineCnt == 3:
                newSong['lyrics'] = line.strip()
                lineCnt += 1
            else:
                newSong['melody'] = line.strip()
                songList.append(newSong)
        self.songList = songList

        def displayTitle(song, x, y):
            self.text = goocanvas.Text(
                parent=self.rootitem,
                x=x, y=y,
                text=song['title'], # not to be translated
                fill_color="black"
                )

            goocanvas.Text(parent=self.rootitem,
                 x=x + 30,
                 y=y + 23,
                 width=175,
                 text='<span font_family="URW Gothic L" size="7000" \
                 weight="bold">' + _(song['origin']) + '</span>',
                 fill_color="black",
                 use_markup=True,
                 pointer_events="GOO_CANVAS_EVENTS_NONE"
                 )

            self.text.connect("button_press_event", self.melodySelected, song)
            gcompris.utils.item_focus_init(self.text, None)


        x = 75
        y = 75
        for song in self.songList:
            displayTitle(song, x, y)
            if y > 400:
                y = 75
                x += 300
            else:
                y += 50


    def melodySelected(self, widget, target, event, song):
        '''
        called once a melody has been selected
        writes the melody to the staff, and displayes the title and lyrics
        '''
        self.display_level(6)
        self.staff.stringToNotation(song['melody'])
        self.staff.texts = []
        self.staff.texts.append(goocanvas.Text(parent=self.rootitem,
         x=420,
         y=100,
         width=300,
         text='<span font_family="URW Gothic L" size="11000" weight="bold" >' + _(song['title']) + '</span>',
         fill_color="black",
         use_markup=True,
         alignment=pango.ALIGN_CENTER,
         pointer_events="GOO_CANVAS_EVENTS_NONE"
         ))

        self.staff.texts.append(goocanvas.Text(parent=self.rootitem,
         x=370,
         y=117,
         width=400,
         text='<span font_family="URW Gothic L" size="11000" >' + _(song['lyrics']) + '</span>',
         fill_color="black",
         use_markup=True,
         alignment=pango.ALIGN_CENTER,
         pointer_events="GOO_CANVAS_EVENTS_NONE"
         ))

    def load_songs_event(self, widget, target, event):
        self.set_level(7)

    def save_file_event(self, widget, target, event):
        '''
        method called when 'save' button is pressed
        opens the gcompris file selector to save the music
        calls the general_save function, passes self.staff
        '''
        gcompris.file_selector_save(self.gcomprisBoard,
                                   'comp', '.txt',
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
        if hasattr(self.staff, 'newClef'):
            self.staff.newClef.clear()
        if self.staff.staffName == "trebleClef":
            self.staff = BassStaff(370, 185, self.rootitem, 3)
            self.staff.drawStaff()
            self.staff.dynamicNoteSpacing = True
        else:
            self.staff = TrebleStaff(370, 185, self.rootitem, 3)
            self.staff.drawStaff()
            self.staff.dynamicNoteSpacing = True

        #re-establish link to root
        self.eraseNotesButton.connect("button_press_event", self.staff.eraseOneNote)
        gcompris.utils.item_focus_init(self.eraseNotesButton, None)

        self.eraseAllButton.connect("button_press_event", self.staff.eraseAllNotes)
        gcompris.utils.item_focus_init(self.eraseAllButton, None)

        self.playCompositionButton.connect("button_press_event", self.staff.playComposition)
        gcompris.utils.item_focus_init(self.playCompositionButton, None)

        self.eighthNoteSelectedButton.connect("button_press_event", self.staff.updateToEighth)
        gcompris.utils.item_focus_init(self.eighthNoteSelectedButton, None)

        self.quarterNoteSelectedButton.connect("button_press_event", self.staff.updateToQuarter)
        gcompris.utils.item_focus_init(self.quarterNoteSelectedButton, None)

        self.halfNoteSelected.connect("button_press_event", self.staff.updateToHalf)
        gcompris.utils.item_focus_init(self.halfNoteSelected, None)

        self.wholeNoteSelected.connect("button_press_event", self.staff.updateToWhole)
        gcompris.utils.item_focus_init(self.wholeNoteSelected, None)

    def keyboard_click(self, widget, target, event, numID=None):
        '''
        called whenever a key rectangle is pressed; a note object is created
        with a note name, text is output to canvas, the note sound is generated,
        and the note is drawn on the staff
        '''
        if not ready(self):
            return False

        if not numID:
            numID = target.numID
        if numID < 0 and self.gcomprisBoard.level < 4:
            return
        if self.staff.currentNoteType == 4:
            n = QuarterNote(numID, self.staff.staffName, self.staff.rootitem, self.keyboard.sharpNotation)
        elif self.staff.currentNoteType == 2:
            n = HalfNote(numID, self.staff.staffName, self.staff.rootitem, self.keyboard.sharpNotation)
        elif self.staff.currentNoteType == 1:
            n = WholeNote(numID, self.staff.staffName, self.staff.rootitem, self.keyboard.sharpNotation)
        elif self.staff.currentNoteType == 8:
            n = EighthNote(numID, self.staff.staffName, self.staff.rootitem, self.keyboard.sharpNotation)

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
        #if not ready(self, timeouttime=100): return False
        if keyval == gtk.keysyms.BackSpace:
            if not ready(self, timeouttime=100): return False
            self.staff.eraseOneNote()
        elif keyval == gtk.keysyms.Delete:
            if not ready(self, timeouttime=100): return False
            self.staff.eraseAllNotes()
        elif keyval == gtk.keysyms.space:
            if not ready(self, timeouttime=100): return False
            self.staff.playComposition()
        else:
            if not self.first:
                pianokeyBindings(keyval, self)
            else:
                self.first = False
    def pause(self, x):
        pass

    def set_level(self, level):
        '''
        updates the level for the game when child clicks on bottom
        left navigation bar to increment level
        '''

        self.staff.eraseAllNotes()
        self.gcomprisBoard.level = level
        gcompris.bar_set_level(self.gcomprisBoard)
        self.display_level(self.gcomprisBoard.level)


def general_save(filename, filetype, staffInstance):
    '''
    called after file selection to save
    '''
    staffInstance.staff_to_file(filename)

def general_load(filename, filetype, staffInstance):
    '''
    called after file selection to load
    '''
    staffInstance.file_to_staff(filename)

def stop_board():
  pass
