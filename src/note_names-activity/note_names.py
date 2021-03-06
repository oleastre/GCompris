#  gcompris - note_names.py
#
# Copyright (C) 2003, 2008 Beth Hadley
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
# note_names activity.


'''
TODO:
    - bring green and red pop-up notes to front with sort order, but I don't
    know how to do this yet....

'''

import gtk
import gtk.gdk
import gcompris
import gcompris.utils
import gcompris.skin
import goocanvas
import pango
from random import randint
import random

from gcompris import gcompris_gettext as _
#import sys
#sys.path.append('/home/bhadley/Desktop/')
from gcomprismusic import *


class Gcompris_note_names:

    def __init__(self, gcomprisBoard):

        # Save the gcomprisBoard, it defines everything we need
        # to know from the core
        self.gcomprisBoard = gcomprisBoard

        # Needed to get key_press
        gcomprisBoard.disable_im_context = True

        self.gcomprisBoard.level = 1
        self.gcomprisBoard.maxlevel = 8

        self.timers = []

        self.colorButtons = True # toggle to choose whether or not to make the text
        # note name buttons colored
        self.pitchSoundEnabled = True # toggle to choose whether or not to 
        # play the pitch sounds
        self.master_is_not_ready = False # boolean to prepare sound timing

        self._okayToRepeat = False

    def start(self):
        # Set the buttons we want in the bar
        gcompris.bar_set(gcompris.BAR_LEVEL)
        gcompris.bar_set_level(self.gcomprisBoard)
        gcompris.bar_location(275, -1, 1)

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
        display appropriate game level based on number. Game levels are:
        1. treble clef staff
        2. note-identification: white key treble notes
        3. note-identification: sharp notes
        4. note-identificaiton: flat notes
        5. bass clef staff
        6. note-identification: white key bass notes
        7. note-identification: sharp notes
        8. note-identification: flat notes
        '''


        if self.rootitem:
            self.rootitem.remove()
        if hasattr(self, 'noteButtonsRootItem'):
            self.noteButtonsRootItem.remove()

        self.rootitem = goocanvas.Group(parent=
                                       self.gcomprisBoard.canvas.get_root_item())

        if level == 1:
            if hasattr(self, 'staff'):
                self.staff.clear()
            self.staff = TrebleStaff(380, 170, self.rootitem, numStaves=1)
            self.staff.noteSpacingX = 36
            self.staff.drawStaff()
            self.staff.rootitem.scale(2.0, 2.0)
            self.staff.rootitem.translate(-350, -75)
            self.staff.drawScale('C Major')

            staffText = _("These are the eight basic notes in treble clef. They form the C Major Scale.")
        elif level == 5:
            if hasattr(self, 'staff'):
                self.staff.clear()
            self.staff = BassStaff(380, 170, self.rootitem, numStaves=1)
            self.staff.noteSpacingX = 36
            self.staff.drawStaff()
            self.staff.rootitem.scale(2.0, 2.0)
            self.staff.rootitem.translate(-350, -75)
            self.staff.drawScale('C Major')
            staffText = _("These are the eight basic notes in bass clef. \
They also form the C Major Scale. Notice that the note positions are different than in treble clef.")
        if level == 1 or level == 5:
            goocanvas.Text(
              parent=self.rootitem,
              x=400.0,
              y=65,
              width=350,
              text=staffText,
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )

            goocanvas.Rect(parent=self.rootitem, x=350, y=117, width=100,
                            height=40, stroke_color="purple", line_width=3.0)

            self.playScaleButton = goocanvas.Text(
              parent=self.rootitem,
              x=400,
              y=136,
              width=100,
              text=_("Play Scale"),
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )

            self.playScaleButton.connect("button_press_event", self.staff.playComposition)
            gcompris.utils.item_focus_init(self.playScaleButton, None)

            if level == 1:
                text = _("Play Treble Clef Game!")
            elif level == 5:
                text = _("Play Bass Clef Game!")
            if level in [1, 5]:
                goocanvas.Rect(parent=self.rootitem, x=350, y=400, width=100,
                                height=40, stroke_color="purple", line_width=3.0)


                self.playScaleGameButton = goocanvas.Text(
                  parent=self.rootitem,
                  x=400,
                  y=420,
                  width=100,
                  text=text,
                  fill_color="black",
                  anchor=gtk.ANCHOR_CENTER,
                  alignment=pango.ALIGN_CENTER
                  )

                self.playScaleGameButton.connect("button_press_event", self.play_scale_game)
                gcompris.utils.item_focus_init(self.playScaleGameButton, None)

        if level in [2, 3, 4, 6, 7, 8]:
            self.updateGameLevel(level)

            self.colorButtons = True
            self.pitchSoundEnabled = True

            self.colorTextToggle = goocanvas.Text(
              parent=self.rootitem,
              x=227,
              y=390,
              width=120,
              text=_("Ready for a challenge? Color all buttons black!"),
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )
            self.colorTextToggle.connect("button_press_event", self.color_button_toggle)
            gcompris.utils.item_focus_init(self.colorTextToggle, None)

            self.soundToggle = goocanvas.Text(
              parent=self.rootitem,
              x=100,
              y=390,
              width=100,
              text=_("Ready for a challenge? Turn off pitch sound"),
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )
            self.soundToggle.connect("button_press_event", self.turn_off_pitch_sound)
            gcompris.utils.item_focus_init(self.soundToggle, None)

        if level == 2 or level == 6:
            instructionText = _("Click on the note name that matches the displayed note.")
        elif level == 3 or level == 7:
            instructionText = _("Now there are sharp notes. These pitches are raised a half step.")
        elif level == 4 or level == 8:
            instructionText = _("Now there are flat notes. These pitches are lowered a half step.")

        if level in [2, 3, 4, 6, 7, 8]:
            goocanvas.Rect(parent=self.rootitem, x=550, y=140, width=240,
                            height=180, stroke_color="purple", line_width=3.0)

            self.instructions = goocanvas.Text(
              parent=self.rootitem,
              x=600,
              y=100,
              width=140,
              text=instructionText,
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )


            self.instructions.scale(1.6, 1.6)
            self.instructions.translate(-180, 40)

        self.replayRandomNote = goocanvas.Text(
          parent=self.rootitem,
          x=120,
          y=100,
          width=150,
          text=_("Mouseover the notes and note names to hear them played"),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )

    def prepareGame(self):
        self.clearPic()
        self.staff.eraseAllNotes()
        self.drawRandomNote(self.staff.name)

    def updateGameLevel(self, levelNum):
        '''
        update the level by updating pitchPossibilities and displaying the correct staff
        '''

        self.rootitem.remove()
        self.rootitem = goocanvas.Group(parent=
                                        self.gcomprisBoard.canvas.get_root_item())

        if self.gcomprisBoard.level <= 4:
            self.staff = TrebleStaff(380, 160, self.rootitem, numStaves=1)
            self.staff.endx = 150
            self.staff.noteSpacingX = 36
            self.staff.drawStaff()
            self.staff.rootitem.scale(2.0, 2.0)
            self.staff.rootitem.translate(-350, -75)
        else:
            self.staff = BassStaff(380, 160, self.rootitem, numStaves=1)
            self.staff.endx = 150
            self.staff.noteSpacingX = 36
            self.staff.drawStaff()
            self.staff.rootitem.scale(2.0, 2.0)
            self.staff.rootitem.translate(-350, -75)

        self.pitchPossibilities = ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C2']
        if levelNum == 3 or levelNum == 7:
            self.pitchPossibilities.extend(['C sharp', 'D sharp', 'F sharp', 'G sharp', 'A sharp'])
        if levelNum == 4 or levelNum == 8:
            self.pitchPossibilities.extend(['D flat', 'E flat', 'G flat', 'A flat', 'B flat'])

        self.drawRandomNote(self.staff.name)
        self.drawNoteButtons()


    def color_button_toggle(self, widget=None, target=None, event=None):
        '''
        update text color of note buttons
        '''
        if self.colorButtons:
            self.colorButtons = False
            self.colorTextToggle.props.text = _("Need a hint? Click here for color-coded note names.")
        else:
            self.colorButtons = True
            self.colorTextToggle.props.text = _("Ready for a challenge? Color all buttons black!")
        self.drawNoteButtons()

    def turn_off_pitch_sound(self, widget=None, target=None, event=None):
        '''
        turn on or off pitch sounds on mouse-over
        '''
        if self.pitchSoundEnabled:
            self.pitchSoundEnabled = False
            self.soundToggle.props.text = _("Click here to hear the pitches.")
        else:
            self.pitchSoundEnabled = True
            self.soundToggle.props.text = _("Ready for a challenge? Turn off pitch sound")


    def drawRandomNote(self, staffType):
        '''
        draw a random note, selected from the pitchPossibilities, and save as self.currentNote
        '''
        if not self._okayToRepeat:
            if not ready(self):
                return
        noteName = self.pitchPossibilities[randint(0, len(self.pitchPossibilities) - 1)]
        noteNametemp = noteName.replace(' sharp', '#')
        noteNametemp = noteNametemp.replace(' flat', 'b')

        if hasattr(self, 'currentNote') and self.currentNote == noteNametemp: #don't repeat the same note twice
            self._okayToRepeat = True
            self.drawRandomNote(staffType)
            return
        self._okayToRepeat = False
        note = QuarterNote(noteName, staffType, self.staff.rootitem)
        self.staff.drawNote(note)
        if self.pitchSoundEnabled:
            note.play()
            note.enablePlayOnMouseover('white')


        self.currentNote = noteNametemp

    def play_scale_game(self, widget=None, target=None, event=None):
        '''
        button to move to the next level and have kids play the game. Also
        possible to just click the level arros at bottom of screen
        '''
        if self.gcomprisBoard.level == 1:
            self.gcomprisBoard.level = 2
        else:
            self.gcomprisBoard.level = 6
        gcompris.bar_set_level(self.gcomprisBoard)
        self.display_level(self.gcomprisBoard.level)


    def drawNoteButtons(self):
        '''
        draw the note buttons seen on the screen, optionally make them color-coded or black
        '''
        if hasattr(self, 'noteButtonsRootItem'):
            self.noteButtonsRootItem.remove()

        self.noteButtonsRootItem = goocanvas.Group(parent=
                                        self.gcomprisBoard.canvas.get_root_item(), x=0, y=0)


        NOTE_COLOR_SCHEME = {"C":'#FF0000',
                       "1":'#FF6347',
                       "D":'#FF7F00',
                       "2":'#FFD700',
                       "E":'#FFFF00',
                       "F":'#32CD32',
                       "3":'#20B2AA',
                       "G":'#6495ED',
                       "4":'#8A2BE2',
                       "A":'#D02090',
                       "5":'#FF00FF',
                       "B":'#FF1493'
                       }

        def drawNoteButton(x, y, pitchName, key_callback, play_sound_on_mouseover):
            '''
            local method to draw one button
            '''
            if self.colorButtons:
                if pitchName in ["C sharp", "D flat"]: color = NOTE_COLOR_SCHEME["1"]
                elif pitchName in ["D sharp", "E flat"]: color = NOTE_COLOR_SCHEME["2"]
                elif pitchName in ["F sharp", "G flat"]: color = NOTE_COLOR_SCHEME["3"]
                elif pitchName in ["G sharp", "A flat"]: color = NOTE_COLOR_SCHEME["4"]
                elif pitchName in ["A sharp", "B flat"]: color = NOTE_COLOR_SCHEME["5"]
                else:
                    color = NOTE_COLOR_SCHEME[pitchName[0]]
            else:
                color = 'black'
            text = pitchName.replace(' sharp', '#')
            text = text.replace(' flat', 'b')
            vars(self)[pitchName] = goocanvas.Text(
              parent=self.noteButtonsRootItem,
              x=x,
              y=y,
              text=text,
              fill_color=color,
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER,
              )
            vars(self)[pitchName].scale(2.0, 2.0)
            vars(self)[pitchName].translate(-250, -150)
            vars(self)[pitchName].connect("button_press_event", key_callback)
            vars(self)[pitchName].connect("motion_notify_event", play_sound_on_mouseover)
            gcompris.utils.item_focus_init(vars(self)[pitchName], None)

        x = 450
        y = 200
        random.shuffle(self.pitchPossibilities)
        for name in self.pitchPossibilities:
            if name != 'C2':
                drawNoteButton(x, y, name, self.key_callback, self.play_sound_on_mouseover)
                y += 20
            if y > 330:
                y = 200
                x = x + 50

    def play_sound_on_mouseover(self, widget=None, target=None, event=None):
        '''
        plays the note sound when the mouse moves over the note name
        '''
        if self.pitchSoundEnabled:
            if not ready(self, 900) or self.master_is_not_ready:
                return
            noteName = widget.props.text.replace('#', ' sharp')
            noteName = noteName.replace('b', ' flat')
            if self.currentNote == 'C2' and noteName == 'C':
                noteName = 'C2'
            HalfNote(noteName, self.staff.name, self.staff.rootitem).play()

    def readyToSoundAgain(self):
        self.master_is_not_ready = False


    def key_callback(self, widget=None, target=None, event=None):
        '''
        called when the kid presses a notename. Checks to see if this is the correct
        note name. displays the appropriate (happy or sad) note picture, and
        resets the board if appropriate
        '''
        self.master_is_not_ready = True
        self.timers.append(gobject.timeout_add(2000, self.readyToSoundAgain))
        if widget.props.text == self.currentNote.replace('2', ''):
            self.displayYouWin()
        else:
            self.displayIncorrectAnswer()


    def displayYouWin(self):
        '''
        displays the happy note for 800 milliseconds
        '''
        if hasattr(self, 'responsePic'):
            self.responsePic.remove()

        self.responsePic = goocanvas.Image(
        parent=self.rootitem,
        pixbuf=gcompris.utils.load_pixmap('note_names/happyNote.png'),
        x=300,
        y=100,
        height=300,
        width=150
        )
        self.timers.append(gobject.timeout_add(800, self.prepareGame))

    def displayIncorrectAnswer(self):
        '''
        displays the sad note for 800 milliseconds
        '''
        if hasattr(self, 'responsePic'):
            self.responsePic.remove()

        self.responsePic = goocanvas.Image(
        parent=self.rootitem,
        pixbuf=gcompris.utils.load_pixmap('note_names/sadNote.png'),
        x=300,
        y=100,
        height=300,
        width=150
        )
        self.timers.append(gobject.timeout_add(800, self.clearPic))

    def clearPic(self):
        if hasattr(self, 'responsePic'):
            self.responsePic.remove()

    def end(self):
        # Remove the root item removes all the others inside it
        self.rootitem.remove()
        gcompris.sound.policy_set(self.saved_policy)
        gcompris.sound.resume()

    def set_level(self, level):
        '''
        updates the level for the game when child clicks on bottom
        left navigation bar to increment level
        '''
        self.gcomprisBoard.level = level
        gcompris.bar_set_level(self.gcomprisBoard)
        self.display_level(level)

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

def stop_board():
  pass
