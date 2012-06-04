# -*- coding: utf-8 -*-
#  gcompris - piano_player.py
#
# Copyright (C) 2003, 2008 Bruno Coudoin
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
    - investigate why two notes appear on canvas when you click, perhaps double
        click. Also investigate why two notes dissapear on canvas when erasing (sometimes)
    - clean up GUI, make more intuitive
    - add 'help' page
    - possibly add more notes (second level with flats & sharps?)
    - allow students to save & load their work
    
DONE:
    - color notes on playback
    - add timer for sound playback
    - make objects out of notes
    
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

class Staff():
    '''
    object to track staff and staff contents, such as notes, clefs, and stafflines
    contains a goocanvas.Group of all components
    '''

    def __init__(self, canvasRoot):
      self.x = 300        #master X position
      self.y = 150        #master Y position

      # ALL LOCATIONS BELOW ARE RELATIVE TO self.x and self.y
      self.endx = 450     #rightend location of staff lines
      self.startx = -250  #leftend location of staff lines
      self.lineNum = 1    #the line number (1,2,3) we're currently writing notes to
      self.line1Y = 0     #starting Y position of first lines of staff
      self.line2Y = 120   #startying Y position of second lines of staff
      self.line3Y = 230   #starting Y position of third lines
      self.currentNoteXCoordinate = self.initialX = 30 #starting X position of first note
      self.noteSpacingX = 25 #distance between each note when appended to staff
      self.staffLineSpacing = 13 #vertical distance between lines in staff
      self.staffLineThickness = 2 # thickness of staff lines

      self.currentNoteType = 'quarterNote' #could be quarter, half, whole (not eight for now)

      self.rootitem = goocanvas.Group(parent=canvasRoot, x=self.x, y=self.y)

      self._drawStaffLines() #draw staff lines

      self.noteList = [] #list of note items written to staff
      self.playingNote = False

      self.timers = []

    def _drawStaffLines(self):
        '''
        draw three sets of staff lines
        '''
        self._drawLines(x=0, y=0, length=self.endx)
        self._drawLines(x=self.startx, y=self.line2Y, length=self.endx + abs(self.startx))
        self._drawLines(x=self.startx, y=self.line3Y, length=self.endx + abs(self.startx))
        self._drawDoubleBar() #two lines at end of third staff line

    def _drawLines(self, x, y, length):
        '''
        draw one set of five staff lines
        '''
        x1 = x
        lineLength = length
        x2 = x1 + lineLength
        y = y

        yWidth = self.staffLineSpacing
        t = self.staffLineThickness
        goocanvas.polyline_new_line(self.rootitem, x1, y, x2, y,
                                    stroke_color="black", line_width=t)
        y += yWidth
        goocanvas.polyline_new_line(self.rootitem, x1, y, x2, y,
                                    stroke_color="black", line_width=t)
        y += yWidth
        goocanvas.polyline_new_line(self.rootitem, x1, y, x2, y,
                                    stroke_color="black", line_width=t)
        y += yWidth
        goocanvas.polyline_new_line(self.rootitem, x1, y, x2, y,
                                    stroke_color="black", line_width=t)
        y += yWidth
        goocanvas.polyline_new_line(self.rootitem, x1, y, x2, y,
                                    stroke_color="black", line_width=t)
        self.bottomYLine = y

    def _drawDoubleBar(self):
        goocanvas.polyline_new_line(self.rootitem, self.endx, self.line3Y - 1, self.endx, self.line3Y + 53,
                                     stroke_color="black", line_width=4.0)
        goocanvas.polyline_new_line(self.rootitem, self.endx - 7, self.line3Y - 1, self.endx - 7, self.line3Y + 53,
                                     stroke_color="black", line_width=3.0)

    def drawNote(self, note):
        '''
        determines the correct x & y coordinate for the next note, and writes
        this note as an image to the canvas. An alert is triggered if no more
        room is left on the screen
        '''
        x = self.getNoteXCoordinate() #returns next x coordinate for note, 
        if x == False:
            try:
                self.alert.remove()
            except:
                pass
            self.alert = goocanvas.Text(
              parent=self.rootitem,
              x=340,
              y=320,
              width=100,
              text=_("The staff is full. Please erase some notes"),
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )
            return
        y = self.getNoteYCoordinate(note) #returns the y coordinate based on note name
        self.lineNum = self.getLineNum(y) #updates self.lineNum
        note.draw(x, y) #draws note image on canvas
        self.noteList.append(note) #adds note object to staff list

    def getNoteXCoordinate(self):
        '''
        determines note's x coordinate, with consideration for the maximum
        staff line length. increments self.lineNum and sets self.currentNoteXCoordinate
        '''
        self.currentNoteXCoordinate += self.noteSpacingX
        if self.currentNoteXCoordinate >= (self.endx - 20):
            if self.lineNum == 3:
                #NO MORE STAFF LEFT!
                return False
            else:
                self.currentNoteXCoordinate = self.startx + 40
                self.lineNum += 1

        return self.currentNoteXCoordinate

    def eraseOneNote(self, widget=None, target=None, event=None):
        '''
        removes the last note in the staff's noteList, updates self.lineNum if
        necessary, and updates self.currentNoteXCoordinate
        '''
        if len(self.noteList) > 1:
          self.currentNoteXCoordinate = self.noteList[-2].x
          remainingNoteY = self.noteList[-2].y
          self.lineNum = self.getLineNum(remainingNoteY)
          self.noteList[-1].remove()
          self.noteList.pop()
        else:
            self.eraseAllNotes()

    def getLineNum(self, Ycoordinate):
        '''
        given the Ycoordinate, returns the correct lineNum (1,2, or 3)
        '''
        if Ycoordinate <= 65:
            return 1
        elif Ycoordinate <= 185:
            return 2
        else:
            return 3

    def eraseAllNotes(self, widget=None, target=None, event=None):
        '''
        remove all notes from staff, deleting them from self.noteList, and 
        restores self.lineNum to 1 and self.currentNoteXCoordinate to the 
        starting position 
        '''
        for n in self.noteList:
          n.remove()
        self.currentNoteXCoordinate = self.initialX
        self.noteList = []
        self.lineNum = 1

    def clear(self):
        '''
        removes and erases all notes and clefs on staff (in preparation for
        a clef change)
        '''
        self.eraseAllNotes()
        self.staffImage1.remove()
        self.staffImage2.remove()
        self.staffImage3.remove()

    def play_it(self):
        '''
        called to play one note. Checks to see if all notes have been played
        if not, establishes a timer for the next note depending on that note's
        duraiton (quarter, half, whole)
        colors the note red that it is currently sounding
        '''
        if self._playedAll():
            self.noteList[self.currentNoteIndex - 1].color('black')
            return False

        self.noteList[self.currentNoteIndex].play()
        self.noteList[self.currentNoteIndex].color('red')
        if not self._playedAll():
            if self.currentNoteIndex != 0:
                self.noteList[self.currentNoteIndex - 1].color('black')
            self.timers.append(gobject.timeout_add(self.noteList[self.currentNoteIndex].toMillisecs(), self.play_it))
        self.currentNoteIndex += 1

    def _playedAll(self):
        '''
        determine if all notes have been played in staff
        '''
        return self.currentNoteIndex == len(self.noteList)

    def playComposition(self, widget=None, target=None, event=None):
        '''
        plays entire composition. establish timers, one per note, called after 
        different durations according to noteType
        '''
        self.timers = []
        self.numNotesPlayed = 0
        self.currentNoteIndex = 0
        self.timers.append(gobject.timeout_add(\
                self.noteList[self.currentNoteIndex].toMillisecs(), self.play_it))

    def sound_played(self, file):
        pass #mandatory method

    #update current note type based on button clicks
    def updateToQuarter(self, widget=None, target=None, event=None):
        self.currentNoteType = 'quarterNote'
    def updateToHalf(self, widget=None, target=None, event=None):
        self.currentNoteType = 'halfNote'
    def updateToWhole(self, widget=None, target=None, event=None):
        self.currentNoteType = 'wholeNote'

class TrebleStaff(Staff):
    '''
    unique type of Staff with clef type specified and certain dimensional
    conventions maintained for certain notes
    '''
    def __init__(self, canvasRoot):
        Staff.__init__(self, canvasRoot)
        self._drawClefs()
        self.name = 'trebleClef'

    def _drawClefs(self):
        '''
        draw all three clefs on canvas
        '''
        self.staffImage1 = goocanvas.Image(
            parent=self.rootitem,
            x=10,
            y= -3,
            height=65,
            width=30,
            pixbuf=gcompris.utils.load_pixmap('trebleClef.png')
            )
        self.staffImage2 = goocanvas.Image(
            parent=self.rootitem,
            x=self.startx,
            y=self.line2Y,
            height=65,
            width=30,
            pixbuf=gcompris.utils.load_pixmap('trebleClef.png')
            )
        self.staffImage3 = goocanvas.Image(
            parent=self.rootitem,
            x=self.startx,
            y=self.line3Y,
            height=65,
            width=30,
            pixbuf=gcompris.utils.load_pixmap('trebleClef.png')
            )

    def getNoteYCoordinate(self, note):
        '''
        return a note's vertical coordinate based on the note's name. This is 
        unique to each type of clef (different for bass and treble)
        '''
        if self.lineNum == 1:
            yoffset = 0
        elif self.lineNum == 2:
            yoffset = self.line2Y
        else:
            yoffset = self.line3Y
        positionDict = {'C':26, 'D':22, 'E':16, 'F':9, 'G':3,
                        'A':-4, 'B':-10, 'C2':-17}
        return  positionDict[note.noteName] + yoffset + 36

class BassStaff(Staff):
    '''
    unique type of Staff with clef type specified and certain dimensional
    conventions maintained for certain notes
    '''
    def __init__(self, canvasRoot):
        Staff.__init__(self, canvasRoot)
        self._drawClefs()
        self.name = 'bassClef'


    def _drawClefs(self):
        '''
        draw all three clefs on canvas
        '''
        self.staffImage1 = goocanvas.Image(
            parent=self.rootitem,
            x=10,
            y=0,
            height=40,
            width=30,
            pixbuf=gcompris.utils.load_pixmap('bassClef.png')
            )
        self.staffImage2 = goocanvas.Image(
            parent=self.rootitem,
            x=self.startx,
            y=self.line2Y,
            height=40,
            width=30,
            pixbuf=gcompris.utils.load_pixmap('bassClef.png')
            )
        self.staffImage3 = goocanvas.Image(
            parent=self.rootitem,
            x=self.startx,
            y=self.line3Y,
            height=40,
            width=30,
            pixbuf=gcompris.utils.load_pixmap('bassClef.png')
            )

    def getNoteYCoordinate(self, note):
        '''
        return a note's vertical coordinate based on the note's name. This is 
        unique to each type of clef (different for bass and treble)
        '''
        if self.lineNum == 1:
            yoffset = 0
        elif self.lineNum == 2:
            yoffset = self.line2Y
        else:
            yoffset = self.line3Y
        positionDict = {'C':-4, 'D':-11, 'E':-17, 'F':-24, 'G':-30,
                        'A':-37, 'B':-42, 'C2':-48}
        return positionDict[note.noteName] + yoffset + 36


class Note():
    '''
    an object representation of a note object, containing the goocanvas image
    item as well as several instance variables to aid with identification
    '''
    def __init__(self, noteName, staffType, rootitem):
        self.noteName = noteName
        self.rootitem = rootitem #typically references the staff's group rootitem
        self.staffType = staffType #'trebleClef' or 'bassClef'

        self.x = 0
        self.y = 0
        self.rootitem = goocanvas.Group(parent=rootitem, x=self.x, y=self.y)

        self.pitchDir = self._getPitchDir()

    def _drawMidLine(self, x, y):
        if self.staffType == 'trebleClef' and self.noteName == 'C'  or \
           self.staffType == 'bassClef' and self.noteName == 'C2':
            self.midLine = goocanvas.polyline_new_line(self.rootitem, x - 12, y, x + 12, y ,
                                        stroke_color="black", line_width=2)

    def play(self):
        '''
        plays the note sound
        '''
        # I prefer to dynamically generate pitchDir when play method is called
        # because this allows modifications to the object after initialization
        # for example, (not in this piano_player activity but possibly for 
        # future activities), a Note() object could be created with 
        # noteType = 'quarterNote' but then changed to 'halfNote' and 
        # I want the correct sound to be played

        gcompris.sound.play_ogg_cb(self._getPitchDir(), self.sound_played) # I prefer this method
        # gcompris.sound.play_ogg_cb(self.pitchDir, self.sound_played) #this works, but I don't prefer it

        # is there any real advantage to generating pitchDir on initialization
        # other than computational time? I can see your point, but a tiny if
        # statements doesn't slow down processesing at all...

    def sound_played(self, file):
        pass

    def _getPitchDir(self):
        if self.staffType == 'trebleClef':
             pitchDir = 'treble_pitches/' + self.noteType + '/' + self.noteName + '.ogg'
        else:
             pitchDir = 'bass_pitches/' + self.noteType + '/' + self.noteName + '.ogg'
        return pitchDir

    def remove(self):
        '''
        removes the note from the canvas
        '''
        self.noteHead.remove()
        if hasattr(self, 'noteFlag'):
            self.noteFlag.remove()
        if hasattr(self, 'midLine'):
            self.midLine.remove()

class QuarterNote(Note):
    '''
    an object inherited from Note, of specific duration (quarter length)
    '''
    noteType = 'quarterNote'

    def toMillisecs(self):
        '''
        convert noteType to actual duration of sound, in milliseconds. for 
        use when playing whole composition
        Note: possibly implement 'tempo' and make this dynamic based on tempo of staff
        '''
        return 500


    def draw(self, x, y):
        '''
        places note image in canvas
        '''
        self._drawMidLine(x, y)


        self.noteHead = goocanvas.Ellipse(parent=self.rootitem,
                    center_x=x,
                    center_y=y,
                    radius_x=7,
                    radius_y=5,
                    fill_color='black',
                    stroke_color='black',
                    line_width=1.0)

        self.noteFlag = goocanvas.polyline_new_line(self.rootitem, x + 6.5, y, x + 6.5, y - 35,
                                    stroke_color="black", line_width=2)

        self.y = y
        self.x = x

    def color(self, color):
        '''
        change all components of the note to color specified
        '''
        self.noteHead.props.fill_color = color
        self.noteHead.props.stroke_color = color
        if hasattr(self, 'noteFlag'):
            self.noteFlag.props.fill_color = color
            self.noteFlag.props.stroke_color = color
        if hasattr(self, 'midLine'):
            self.midLine.props.fill_color = color
            self.midLine.props.stroke_color = color


class HalfNote(Note):
    '''
    an object inherited from Note, of specific duration (half length)
    '''
    noteType = 'halfNote'
    def toMillisecs(self):
        return 1000

    def draw(self, x, y):
        '''
        places note image in canvas
        '''
        self._drawMidLine(x, y)


        self.noteHead = goocanvas.Ellipse(parent=self.rootitem,
                    center_x=x,
                    center_y=y,
                    radius_x=7,
                    radius_y=5,
                    stroke_color='black',
                    line_width=2.5)
        self.noteFlag = goocanvas.polyline_new_line(self.rootitem, x + 6.5, y, x + 6.5, y - 35,
                                    stroke_color="black", line_width=2)
        self.y = y
        self.x = x

    def color(self, color):
        self.noteHead.props.stroke_color = color
        self.noteFlag.props.stroke_color = color
        if hasattr(self, 'midLine'):
            self.midLine.props.fill_color = color
            self.midLine.props.stroke_color = color


class WholeNote(Note):
    '''
    an object inherited from Note, of specific duration (whole length)
    '''
    noteType = 'wholeNote'
    def toMillisecs(self):
        return 2000

    def draw(self, x, y):
        self._drawMidLine(x, y)
        self.noteHead = goocanvas.Ellipse(parent=self.rootitem,
                    center_x=x,
                    center_y=y,
                    radius_x=7,
                    radius_y=5,
                    stroke_color='black',
                    line_width=2.5)

    def color(self, color):
        self.noteHead.props.stroke_color = color
        if hasattr(self, 'midLine'):
            self.midLine.props.stroke_color = color

class Gcompris_piano_player:

    def __init__(self, gcomprisBoard):

        # Save the gcomprisBoard, it defines everything we need
        # to know from the core
        self.gcomprisBoard = gcomprisBoard

        # Needed to get key_press
        gcomprisBoard.disable_im_context = True

    def start(self):
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


        '''
        create text "buttons" to indicate options to students
        '''
        self.noteText = goocanvas.Text(
          parent=self.rootitem,
          x=90,
          y=50,
          width=100,
          text=_("Click on a note!"),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )


        self.changeClefButton = goocanvas.Text(
          parent=self.rootitem,
          x=220,
          y=50,
          text=_("Change Staff\nClef"),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )

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
            pixbuf=gcompris.utils.load_pixmap('quarterNote.png'),
            x=630,
            y=80,
            height=45,
            width=20
            )

        self.halfNoteSelected = goocanvas.Image(
            parent=self.rootitem,
            pixbuf=gcompris.utils.load_pixmap('halfNote.png'),
            x=660,
            y=80,
            height=45,
            width=20
            )

        self.wholeNoteSelected = goocanvas.Image(
            parent=self.rootitem,
            pixbuf=gcompris.utils.load_pixmap('wholeNote.png'),
            x=700,
            y=80,
            height=45,
            width=20
            )

        '''
        create staff instance to manage music data
        treble clef image loaded by default; click button to switch to bass clef
        '''
        self.staff = TrebleStaff(self.rootitem)

        '''
        synchronize buttons with events
        '''
        self.changeClefButton.connect("button_press_event", self.change_clef_event)
        gcompris.utils.item_focus_init(self.changeClefButton, None)

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


        '''
        create piano keyboard, with buttons for keys
        '''
        #piano keyboard image
        goocanvas.Image(
          parent=self.rootitem,
          pixbuf=gcompris.utils.load_pixmap("keyboard.png"),
          x=60,
          y=130,
          height=100,
          width=200
          )

        '''
        define colored rectangles to lay on top of piano keys for student to click on

        Translators: note that you must write the translated note name matching the given note name in the English notation
         For example, in French the correct translations would be:
        #A (la), B (si), C (do), D (ré), E (mi), F (fa) , G (sol)
        '''
        keyWidth = 15
        keyHeight = 15
        ypose = 212
        xpose = 64 #initial xpose
        seperationWidth = 25
        self.keyC = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                   width=keyWidth, height=keyHeight,
                                   stroke_color="black", fill_color="pink",
                                   line_width=1.0)
        self.keyC.name = _("C")
        xpose += seperationWidth
        self.keyD = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                   width=keyWidth, height=keyHeight,
                                   stroke_color="black", fill_color="red",
                                   line_width=1.0)
        self.keyD.name = _("D")
        xpose += seperationWidth
        self.keyE = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                   width=keyWidth, height=keyHeight,
                                   stroke_color="black", fill_color="orange",
                                   line_width=1.0)
        self.keyE.name = _("E")
        xpose += seperationWidth
        self.keyF = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                   width=keyWidth, height=keyHeight,
                                   stroke_color="black", fill_color="yellow",
                                   line_width=1.0)
        self.keyF.name = _("F")
        xpose += seperationWidth
        self.keyG = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                   width=keyWidth, height=keyHeight,
                                   stroke_color="black", fill_color="green",
                                   line_width=1.0)
        self.keyG.name = _("G")
        xpose += seperationWidth
        self.keyA = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                   width=keyWidth, height=keyHeight,
                                   stroke_color="black", fill_color="blue",
                                   line_width=1.0)
        self.keyA.name = _("A")
        xpose += seperationWidth
        self.keyB = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                   width=keyWidth, height=keyHeight,
                                   stroke_color="black", fill_color="purple",
                                   line_width=1.0)
        self.keyB.name = _("B")
        xpose += seperationWidth
        self.keyC2 = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                    width=keyWidth, height=keyHeight,
                                    stroke_color="black", fill_color="white",
                                    line_width=1.0)
        self.keyC2.name = _("C2")

        '''
        connect these rectangles to a button press event, the method
        keyboard_click
        '''

        self.keyC.connect("button_press_event", self.keyboard_click)
        gcompris.utils.item_focus_init(self.keyC, None)

        self.keyD.connect("button_press_event", self.keyboard_click)
        gcompris.utils.item_focus_init(self.keyD, None)

        self.keyE.connect("button_press_event", self.keyboard_click)
        gcompris.utils.item_focus_init(self.keyE, None)

        self.keyF.connect("button_press_event", self.keyboard_click)
        gcompris.utils.item_focus_init(self.keyF, None)

        self.keyG.connect("button_press_event", self.keyboard_click)
        gcompris.utils.item_focus_init(self.keyG, None)

        self.keyA.connect("button_press_event", self.keyboard_click)
        gcompris.utils.item_focus_init(self.keyA, None)

        self.keyB.connect("button_press_event", self.keyboard_click)
        gcompris.utils.item_focus_init(self.keyB, None)

        self.keyC2.connect("button_press_event", self.keyboard_click)
        gcompris.utils.item_focus_init(self.keyC2, None)

        Prop = gcompris.get_properties()
        if(not Prop.fx):
            gcompris.utils.dialog(_("Error: this activity cannot be played with the\nsound effects disabled.\nGo to the configuration dialogue to\nenable the sound"), stop_board)


    def change_clef_event(self, widget, target, event):
        '''
        method called when button to change clef is pressed
        load in the appropriate new staff image
        re-syncrhonize all buttons because rootitem changes
        all notes in staff are removed...this can be changed later
        if desired, but could confuse children if more than one clef
        exists in the piece
        '''
        self.staff.clear()
        if self.staff.name == "trebleClef":
            self.staff = BassStaff(self.rootitem)
        else:
            self.staff = TrebleStaff(self.rootitem)

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

        if self.staff.currentNoteType == 'quarterNote':
            n = QuarterNote(target.name, self.staff.name, self.staff.rootitem)
        elif self.staff.currentNoteType == 'halfNote':
            n = HalfNote(target.name, self.staff.name, self.staff.rootitem)
        elif self.staff.currentNoteType == 'wholeNote':
            n = WholeNote(target.name, self.staff.name, self.staff.rootitem)

        self.staff.drawNote(n)
        self.noteText.remove()
        self.noteText = goocanvas.Text(
          parent=self.rootitem,
          x=90,
          y=50,
          width=100,
          text=_("This is the " + (target.name)[0] + ' key'),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )
        n.play()

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

    def pause(self, pause):
        pass

    def set_level(self, level):
        pass

