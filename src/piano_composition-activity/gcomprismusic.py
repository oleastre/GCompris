# -*- coding: utf-8 -*-
#  gcompris - gcomprismusic.py
#
# Copyright (C) 2012 Beth Hadley
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty 00of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <http://www.gnu.org/licenses/>.
#
#

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
import cPickle as pickle
import copy
from random import randint
import random
'''
TODO:
    - write eighth note class
    - fix implementation of note text
'''

# Rainbow color scheme used throughout games,
# according to music research on best
# techniques to teach young children music

NOTE_COLOR_SCHEME = {1:'#FF0000',
                     - 1:'#FF6347',
                     2:'#FF7F00',
                     - 2:'#FFD700',
                     3:'#FFFF00',
                     4:'#32CD32',
                     - 3:'#20B2AA',
                     5:'#6495ED',
                     - 4:'#8A2BE2',
                     6:'#D02090',
                     - 5:'#FF00FF',
                     7:'#FF1493',
                     8:'#FF0000'
                     }
# this is unique to the English notation system
# translators must modify this dictionary for each language
WHITE_KEY_NOTATION = {1:_('C'), 2:_('D'), 3:_('E'), 4:_('F'), 5:_('G'), 6:_('A'), 7:_('B'), 8:_('C')}
SHARP_NOTATION = {-1:_('C#'), -2:_('D#'), -3:_('F#'), -4:_('G#'), -5:_('A#')}
FLAT_NOTATION = {-1:_('Db'), -2:_('Eb'), -3:_('Gb'), -4:_('Ab'), -5:_('Bb')}
'''
Translators: note that you must write the translated note name matching the
given note name in the English notation
 For example, in many European countries the correct translations would be:
 C C♯ D D♯ E F F♯ G G♯ A B H C
'''
def getKeyNameFromID(numID, sharpNotation=True):
    '''optionally sharpNotation = True for sharp notation, or
    sharpNotation = False for flat notation'''
    if numID > 0:
        return WHITE_KEY_NOTATION[numID]
    elif sharpNotation:
        return SHARP_NOTATION[numID]
    else:
        return FLAT_NOTATION[numID]



# ---------------------------------------------------------------------------
#
#  STAFF OBJECTS
#
# ---------------------------------------------------------------------------


class Staff():
    '''
    object to track staff and staff contents, such as notes, clefs, and stafflines
    contains a goocanvas.Group of all components
    '''

    def __init__(self, x, y, canvasRoot, numStaves):

      self.originalRoot = canvasRoot
      self.x = x        #master X position
      self.y = y        #master Y position

      # ALL LOCATIONS BELOW ARE RELATIVE TO self.x and self.y
      self.endx = 350     #rightend location of staff lines
      self.startx = 0     #leftend location of staff lines
      self.lineNum = 1    #the line number (1,2,3) we're currently writing notes to
      self.line1Y = 0     #starting Y position of first lines of staff
      self.line2Y = 115   #startying Y position of second lines of staff
      self.line3Y = 230   #starting Y position of third lines
      self.currentNoteXCoordinate = self.initialX = 30 #starting X position of first note
      self.noteSpacingX = 30 #distance between each note when appended to staff
      self.staffLineSpacing = 13 #vertical distance between lines in staff
      self.staffLineThickness = 2 # thickness of staff lines
      self.numStaves = numStaves # number of staves to draw (1,2, or 3)

      self.currentNoteType = 4 #could be quarter, half, whole (not eight for now)

      self.rootitem = goocanvas.Group(parent=canvasRoot, x=self.x, y=self.y)

      self.noteList = [] #list of note items written to staff
      self.playingNote = False

      self.timers = []

      self.colorCodeNotes = True # optionally set to False to mark all notes black

      self.notReadyToPlay = False

      self.donotwritenotetext = False

      self.labelBeatNumbers = False
      self.beatNumLabels = []
      self.drawPlayingLine = False

    def drawStaff(self):
        '''
        draw the staff, including staff lines and optional staff text
        '''
        self._drawStaffLines() #draw staff lines

    def textBox(self, text):
        '''
        change the staff text
        '''
        if hasattr(self, 'noteText'):
            self.noteText.props.text = text

    def _drawStaffLines(self):
        '''
        draw staff lines according to the number of staves
        '''
        if self.numStaves >= 1:
            self._drawLines(x=0, y=0, length=self.endx)
        if self.numStaves >= 2:
            self._drawLines(x=self.startx, y=self.line2Y, length=self.endx + abs(self.startx))
        if self.numStaves >= 3:
            self._drawLines(x=self.startx, y=self.line3Y, length=self.endx + abs(self.startx))
        self._drawEndBars() #two lines at end of third staff line

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

    def _drawEndBars(self):
        '''
        draw the vertical end bars on each line, two for line 3
        '''

        if self.numStaves >= 1:
            goocanvas.polyline_new_line(self.rootitem, self.endx,
                                    self.line1Y - 1, self.endx, self.line1Y + 53,
                                     stroke_color="black", line_width=3.0)

        if self.numStaves >= 2:
            goocanvas.polyline_new_line(self.rootitem, self.endx,
                                    self.line2Y - 1, self.endx, self.line2Y + 53,
                                     stroke_color="black", line_width=3.0)

        if self.numStaves >= 3:
            #doublebar
            goocanvas.polyline_new_line(self.rootitem, self.endx - 7,
                                    self.line3Y - 1, self.endx - 7, self.line3Y + 53,
                                     stroke_color="black", line_width=3.0)

            #final barline, dark
            goocanvas.polyline_new_line(self.rootitem, self.endx,
                                    self.line3Y - 1, self.endx, self.line3Y + 53,
                                     stroke_color="black", line_width=4.0)

    def drawNote(self, note):
        '''
        determine the correct x & y coordinate for the next note, and writes
        this note as an image to the canvas. An alert is triggered if no more
        room is left on the screen. Also color-codes the note if self.colorCodeNotes == True
        '''
        x = self.getNoteXCoordinate() #returns next x coordinate for note,
        if x == False:
            try:
                self.alert.remove()
            except:
                pass
            self.alert = goocanvas.Text(
              parent=self.rootitem,
              x=300,
              y=320,
              width=200,
              text=_("The staff is full. Please erase some notes"),
              fill_color="black",
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER
              )
            return
        y = self.getNoteYCoordinate(note) #returns the y coordinate based on note name
        self.lineNum = self.getLineNum(y) #updates self.lineNum
        note.draw(x, y) #draws note image on canvas
        if self.colorCodeNotes:
            note.colorCodeNote()
        self.noteList.append(note) #adds note object to staff list

        if self.labelBeatNumbers:
            for n in note.beatNums:
                if n == note.beatNums[0]:
                    size = "10000"
                else:
                    size = "5000"

                blob = goocanvas.Text(
                parent=self.rootitem,
                x=x,
                y=y - 75,
                text='<span size="' + size + '" >' + n + '</span>',
                fill_color="black",
                anchor=gtk.ANCHOR_CENTER,
                alignment=pango.ALIGN_CENTER,
                use_markup=True)
                self.beatNumLabels.append(blob)
                x += self.noteSpacingX / len(note.beatNums)


    def writeLabel(self, text, note):
        '''
        writes a note label below the note, such as labeling the note name,
        in color-code if applicable
        '''
        if self.colorCodeNotes:
            color = NOTE_COLOR_SCHEME[note.numID]

        if note in self.noteList:
            text = goocanvas.Text(
                  parent=self.rootitem,
                  x=note.x,
                  y=self.staffLineSpacing * 6 + 3,
                  text=text,
                  fill_color='black',
                  anchor=gtk.ANCHOR_CENTER,
                  alignment=pango.ALIGN_CENTER
                  )
            rect = goocanvas.Rect(parent=self.rootitem,
                      x=note.x - 10,
                      y=self.staffLineSpacing * 6 - 8,
                      width=20,
                      height=20,
                      line_width=.5,
                      fill_color=color)
            text.raise_(rect)

    def getNoteXCoordinate(self):
        '''
        determines note's x coordinate, with consideration for the maximum
        staff line length. increments self.lineNum and sets self.currentNoteXCoordinate
        '''
        self.currentNoteXCoordinate += self.noteSpacingX
        if self.currentNoteXCoordinate >= (self.endx - 5):
            if self.lineNum == 3:
                #NO MORE STAFF LEFT!
                return False
            else:
                self.currentNoteXCoordinate = self.startx + 50
                self.lineNum += 1

        return self.currentNoteXCoordinate

    def eraseOneNote(self, widget=None, target=None, event=None):
        '''
        removes the last note in the staff's noteList, updates self.lineNum if
        necessary, and updates self.currentNoteXCoordinate
        '''
        try:
            self.alert.remove()
        except:
            pass

        if len(self.noteList) > 1:
            if not ready(self):
              return
            else:
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
        #if not ready(self):
        #    return False
        for o in self.beatNumLabels:
            o.remove()
        for n in self.noteList:
          n.remove()
        self.currentNoteXCoordinate = self.initialX
        self.noteList = []
        self.lineNum = 1

        try:
            self.alert.remove()
        except:
            pass


    def clear(self):
        '''
        removes and erases all notes and clefs on staff (in preparation for
        a clef change)
        '''
        self.eraseAllNotes()
        if hasattr(self, 'staffImage1'):
            self.staffImage1.remove()
        if hasattr(self, 'staffImage2'):
            self.staffImage2.remove()
        if hasattr(self, 'staffImage3'):
            self.staffImage3.remove()
        if hasattr(self, 'noteText'):
            self.noteText.remove()

    def play_it(self, playingLineOnly=False):
        '''
        called to play one note. Checks to see if all notes have been played
        if not, establishes a timer for the next note depending on that note's
        duration (quarter, half, whole)
        colors the note white that it is currently sounding
        '''
        if self.currentNoteIndex >= len(self.noteList):
            if hasattr(self, 'verticalPlayLine'):
                self.verticalPlayLine.remove()
            self.notReadyToPlay = False
            return

        note = self.noteList[self.currentNoteIndex]
#        if not self.donotwritenotetext:
#            self.textBox('Note Name: ' + note.niceName)
        if hasattr(self, 'verticalPlayLine'):
            self.verticalPlayLine.remove()

        if self.drawPlayingLine or playingLineOnly:
            self.verticalPlayLine = goocanvas.polyline_new_line(self.rootitem,
                                note.x, note.y, note.x, note.y - 50,
                                stroke_color_rgba=0x121212D0, line_width=2)

            self.verticalPlayLine.animate(self.noteSpacingX, 0, 1.0, 0.0, \
                absolute=False, duration=note.toMillisecs(), step_time=50, type=goocanvas.ANIMATE_FREEZE)

        if not playingLineOnly:
            note.play()
        self.timers.append(gobject.timeout_add(self.noteList[self.currentNoteIndex].toMillisecs(), self.play_it, playingLineOnly))
        self.currentNoteIndex += 1

    def playComposition(self, widget=None, target=None, event=None, playingLineOnly=False):
        '''
        plays entire composition. establish timers, one per note, called after
        different durations according to noteType
        '''

        if not self.noteList or self.notReadyToPlay:
            return
        self.notReadyToPlay = True
        if not ready(self):
            return False

        self.timers = []
        self.currentNoteIndex = 0
        self.timers.append(gobject.timeout_add(self.noteList[self.currentNoteIndex].toMillisecs(), self.play_it, playingLineOnly))


    def sound_played(self, file):
        pass #mandatory method

    def drawFocusRect(self, x, y):
        '''
        draws focus rectangle around notes (quarter/half/whole) in piano_composition game
        '''
        if hasattr(self, 'focusRect'):
            self.focusRect.remove()
        self.focusRect = goocanvas.Rect(parent=self.rootitem,
                                    x=x,
                                    y=y,
                                    width=28, height=45,
                                    radius_x=5, radius_y=5,
                                    stroke_color="black", line_width=2.0)
    #update current note type based on button clicks
    def updateToEighth(self, widget=None, target=None, event=None):
        self.currentNoteType = 8
        self.drawFocusRect(-100, -60)
    def updateToQuarter(self, widget=None, target=None, event=None):
        self.currentNoteType = 4
        self.drawFocusRect(-70, -60)
    def updateToHalf(self, widget=None, target=None, event=None):
        self.currentNoteType = 2
        self.drawFocusRect(-42, -60)
    def updateToWhole(self, widget=None, target=None, event=None):
        self.currentNoteType = 1
        self.drawFocusRect(-15, -60)


    def staff_to_file(self, filename):
        '''
        uses python's cpickle to save the python object stored in self, a Staff instance
        '''
        file = open(filename , 'wb')
        file.write(self.staffName + ' ')
        for note in self.noteList:
            file.write(str(note.numID) + ',' + str(note.noteType) + ' ')


        file.close()


    def stringToNotation(self, melodyString):
        if hasattr(self, 'newClef'):
            self.newClef.clear()
        self.clear()
        keys = melodyString.split()
        staffName = keys[0]
        if staffName == 'trebleClef':
            self.newClef = TrebleStaff(self.x, self.y, self.originalRoot)
            self.newClef._drawClefs()
        elif staffName == 'bassClef':
            self.newClef = BassStaff(self.x, self.y, self.originalRoot)
            self.newClef._drawClefs()
        else:
            print "please use trebleClef or bassClef"
            return
        self.positionDict = self.newClef.positionDict
        for exp in keys[1:]:
            numID, duration = exp.split(',')
            duration = int(duration)
            numID = int(numID)
            if duration == 4:
                note = QuarterNote(numID, staffName, self.rootitem)
            elif duration == 2:
                note = HalfNote(numID, staffName, self.rootitem)
            elif duration == 1:
                note = WholeNote(numID, staffName, self.rootitem)
            elif duration == 8:
                note = EighthNote(numID, staffName, self.rootitem)
            else:
                print 'ERROR: notetype not supported', exp
                return

            self.drawNote(note)

    def file_to_staff(self, filename):
        '''
        uses python's cpickle to load the python object, a staff instance
        '''

        file = open(filename, 'rb')
        self.clear()
        self.stringToNotation(file.read())

#        try:



#            loadedStaff = pickle.load(file)
#        except:
#            file.close()
#            print 'Cannot load ', filename , " as a GCompris animation"
#            return
#        #self.rootitem = self.originalRoot
#
#       
#
#        '''
#        PROBLEM: I can't seem to be able to get a direct pointer from the
#        loadedStaff instance to the self instance....This would be cleanest,
#        but I'm getting a nasty error about rootitems that I can't seem
#        to fix. I tried copy.deepcopy on the loaded staff, but that also
#        doesn't work...
#        '''
##        self = copy.deepcopy(loadedStaff)
##        self = loadedStaff
##        for note in self.noteList:
##            print note
##            self.drawNote(note)
#
#        '''
#        So my fall-back solution is to reconstruct the objects manually. This
#        is a huge waste of the power of pickle, and I'd like to figure out
#        how not to do this. Help please ?
#        '''
#        if loadedStaff.staffName == 'trebleClef':
#            y = TrebleStaff(self.x, self.y, self.originalRoot)
#            y._drawClefs()
#        else:
#            y = BassStaff(self.x, self.y, self.originalRoot)
#            y._drawClefs()
#        self.positionDict = y.positionDict
#        self.numID = y.numID
#
#        for n in loadedStaff.noteList:
#            if n.noteType == 'quarterNote':
#                note = QuarterNote(n.numID, loadedStaff.staffName, self.rootitem)
#            elif n.noteType == 'halfNote':
#                note = HalfNote(n.numID, loadedStaff.staffName, self.rootitem)
#            elif n.noteType == 'wholeNote':
#                note = WholeNote(n.numID, loadedStaff.staffName, self.rootitem)
#            else:
#                print 'ERROR: notetype not supported: ' , n.noteType
#
#            self.drawNote(note)
#
#        file.close()
#        self.noteText = goocanvas.Text(
#          parent=self.originalRoot,
#          x=120,
#          y=81,
#          width=100,
#          text='',
#          fill_color="black",
#          anchor=gtk.ANCHOR_CENTER,
#          alignment=pango.ALIGN_CENTER
#          )

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

        if note.numID < 0 and note.sharpNotation:
            numID = {-1:1, -2:2, -3:4, -4:5, -5:6}[note.numID]
        elif note.numID < 0:
            numID = {-1:2, -2:3, -3:5, -4:6, -5:7}[note.numID]
        else:
            numID = note.numID

        return  self.positionDict[numID] + yoffset + 36

    def drawScale(self, scaleName, includeNoteNames=True):
        '''
        draw the scale on the staff, optionally including Note Names
        '''
        if scaleName == 'C Major':
            numIDs = [1, 2, 3, 4, 5, 6, 7, 8]
        for id in numIDs:
            note = QuarterNote(id, self.staffName, self.rootitem)
            self.drawNote(note)
            if includeNoteNames:
                text = getKeyNameFromID(note.numID)
                self.writeLabel(text, note)
            note.enablePlayOnClick()

    def colorCodeAllNotes(self):
        for note in self.noteList:
            note.colorCodeNote()

    def colorAllNotes(self, color):
        for note in self.noteList:
            note.color(color)

class TrebleStaff(Staff):
    '''
    unique type of Staff with clef type specified and certain dimensional
    conventions maintained for certain notes
    '''
    def __init__(self, x, y, canvasRoot, numStaves=3):
        Staff.__init__(self, x, y, canvasRoot, numStaves)

        self.staffName = 'trebleClef'

         # for use in getNoteYCoordinateMethod
        self.positionDict = {1:26, 2:22, 3:16, 4:9, 5:3,
                        6:-4, 7:-10, 8:-17}

    def drawStaff(self):
        self._drawClefs()
        Staff.drawStaff(self)

    def _drawClefs(self):
        '''
        draw all three clefs on canvas
        '''
        h = 65
        w = 30
        if self.numStaves >= 1:
            self.staffImage1 = goocanvas.Image(
                parent=self.rootitem,
                x=10,
                y= -3,
                height=h,
                width=w,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/trebleClef.png')
                )
        if self.numStaves >= 2:
            self.staffImage2 = goocanvas.Image(
                parent=self.rootitem,
                x=self.startx,
                y=self.line2Y,
                height=h,
                width=w,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/trebleClef.png')
                )
        if self.numStaves >= 3:
            self.staffImage3 = goocanvas.Image(
                parent=self.rootitem,
                x=self.startx,
                y=self.line3Y,
                height=h,
                width=w,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/trebleClef.png')
                )

class BassStaff(Staff):
    '''
    unique type of Staff with clef type specified and certain dimensional
    conventions maintained for certain notes
    '''
    def __init__(self, x, y, canvasRoot, numStaves=3):
        Staff.__init__(self, x, y, canvasRoot, numStaves)

        self.staffName = 'bassClef'

        # for use in getNoteYCoordinateMethod
        self.positionDict = {1:-4, 2:-11, 3:-17, 4:-24, 5:-30,
                        6:-36, 7:-42, 8:-48}

    def drawStaff(self, text=None):
        self._drawClefs()
        Staff.drawStaff(self)


    def _drawClefs(self):
        '''
        draw all three clefs on canvas
        '''
        h = 40
        w = 30
        if self.numStaves >= 1:
            self.staffImage1 = goocanvas.Image(
                parent=self.rootitem,
                x=10,
                y=0,
                height=h,
                width=w,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/bassClef.png')
                )
        if self.numStaves >= 2:
            self.staffImage2 = goocanvas.Image(
                parent=self.rootitem,
                x=self.startx,
                y=self.line2Y,
                height=h,
                width=w,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/bassClef.png')
                )
        if self.numStaves >= 3:
            self.staffImage3 = goocanvas.Image(
                parent=self.rootitem,
                x=self.startx,
                y=self.line3Y,
                height=h,
                width=w,
                pixbuf=gcompris.utils.load_pixmap('piano_composition/bassClef.png')
                )

# ---------------------------------------------------------------------------
#
#  NOTE OBJECTS
#
# ---------------------------------------------------------------------------


class Note():
    '''
    an object representation of a note object, containing the goocanvas image
    item as well as several instance variables to aid with identification
    '''
    def __init__(self, numID, staffType, rootitem, sharpNotation=True):
        self.numID = numID

        self.staffType = staffType #'trebleClef' or 'bassClef'

        self.x = 0
        self.y = 0
        self.rootitem = goocanvas.Group(parent=rootitem, x=self.x, y=self.y)

        self.silent = False #make note silent always?

        self.pitchDir = self._getPitchDir()

        self.timers = []
        self.sharpNotation = sharpNotation # toggle to switch note between sharp notation
        # and flat notation, if applicable

    def drawPictureFocus(self, x, y):
        self.playingLine = goocanvas.Image(
              parent=self.rootitem,
              pixbuf=gcompris.utils.load_pixmap("piano_composition/note_highlight.png"),
              x=x - 13,
              y=y - 15,
              )
        self.playingLine.props.visibility = goocanvas.ITEM_INVISIBLE

    def _drawMidLine(self, x, y):
        if self.staffType == 'trebleClef' and (self.numID == 1 or  (self.numID == -1 and self.sharpNotation)) or \
           (self.staffType == 'bassClef' and self.numID == 1 or self.numID == 8) :
            self.midLine = goocanvas.polyline_new_line(self.rootitem, x - 12, y, x + 12, y ,
                                        stroke_color_rgba=0x121212D0, line_width=1)

    def play(self, x=None, y=None, z=None):
        '''
        plays the note sound
        '''
        if not ready(self, 700) or self.silent:
            return False
        # sometimes this method is called without actually having fa note
        # printed on the page (we just want to hear the pitch). Thus, only
        # highlight a note if it exists!
        if hasattr(self, 'playingLine'):
            self.highlight()
        gcompris.sound.play_ogg(self._getPitchDir())


    def _getPitchDir(self):
        '''
        uses the note's raw name to find the pitch directory associate to it.
        Since only sharp pitches are stored, method finds the enharmonic name
        to flat notes using the circle of fifths dictionary
        '''

        if self.staffType == 'trebleClef':
             pitchDir = 'piano_composition/treble_pitches/' + str(self.noteType) + '/' + str(self.numID) + '.wav'
        else:
             pitchDir = 'piano_composition/bass_pitches/' + str(self.noteType) + '/' + str(self.numID) + '.wav'

        return pitchDir


    def _drawAlteration(self, x, y):
        '''
        draws a flat or a sharp sign in front of the note if needed
        width and height specifications needed because these images
        need to be so small that scaling any larger image to the correct
        size makes them extremely blury.
        '''
        if self.numID < 0:
            if self.sharpNotation:
                self.alteration = goocanvas.Image(
                  parent=self.rootitem,
                  pixbuf=gcompris.utils.load_pixmap("piano_composition/blacksharp.png"),
                  x=x - 23,
                  y=y - 9,
                  width=18,
                  height=18
                  )
            else:
                self.alteration = goocanvas.Image(
                  parent=self.rootitem,
                  pixbuf=gcompris.utils.load_pixmap("piano_composition/blackflat.png"),
                  x=x - 23,
                  y=y - 14,
                  width=20,
                  height=20,
                  )

    def remove(self):
        '''
        removes the note from the canvas
        '''
        self.rootitem.remove()

    def colorNoteHead(self, color, fill=True, outline=True):
        '''
        colors the notehead, by default both the fill and the outline
        '''
        if fill:
            self.noteHead.props.fill_color = color
        if outline:
            self.noteHead.props.stroke_color = "black"

        if hasattr(self, 'midLine'):
            self.midLine.props.fill_color = "black"
            self.midLine.props.stroke_color = "black"

    def color(self, color):
        '''
        default color method. colors all components, including notehead's fill
        '''
        self.colorNoteHead(color)

    def colorCodeNote(self):
        '''
        color the note the appropriate color based on the given color scheme
        '''
        self.color(NOTE_COLOR_SCHEME[self.numID])


    def enablePlayOnClick(self):
        '''
        enables the function that the note will be played when the user clicks
        on the note (not currently used)
        '''

        self.noteHead.connect("button_press_event", self.play)
        gcompris.utils.item_focus_init(self.noteHead, None)
        self.silent = False
    def disablePlayOnClick(self):
        self.silent = True

    def enablePlayOnMouseover(self):
        '''
        enables the function that the note will be played when the user
        runs the mouse over the note (used in note_names activity)

        Apparently mouseover actions aren't recommended for GCompris (touchpad
        issues, etc.) so this method isn't used.
        '''
        self.noteHead.connect("motion_notify_event", self.play)
        gcompris.utils.item_focus_init(self.noteHead, None)
        self.silent = False
    def stopHighLight(self):
        self.playingLine.props.visibility = goocanvas.ITEM_INVISIBLE

    def highlight(self):
        '''
        highlight the note for 700 milliseconds, then revert
        '''
        self.playingLine.props.visibility = goocanvas.ITEM_VISIBLE
        self.timers.append(gobject.timeout_add(self.toMillisecs(), self.stopHighLight))

class EighthNote(Note):
    '''
    an object inherited from Note, of specific duration (eighth length)
    '''
    noteType = 8
    beatNums = ['+']
    def toMillisecs(self):
        return 250

    def draw(self, x, y):
        '''
        places note image in canvas
        '''
        self.drawPictureFocus(x, y)

        # Thanks to Olivier Samyn for the note shape
        self.noteHead = goocanvas.Path(parent=self.rootitem,
            data="m %i %i a7,5 0 0,1 12,-3.5 v-32 h2 v35 a7,5 0 0,1 -14,0z" % (x - 7, y),
            fill_color='black',
            stroke_color='black',
            line_width=1.0
            )

        self._drawAlteration(x, y)

        self._drawMidLine(x, y)

        self._drawFlag(x, y)

        self.y = y
        self.x = x

    def _drawFlag(self, x, y):
        goocanvas.Image(
          parent=self.rootitem,
          pixbuf=gcompris.utils.load_pixmap("piano_composition/flag.png"),
          x=x + 7,
          y=y - 37,
          height=30,
          width=10
          )
class QuarterNote(Note):
    '''
    an object inherited from Note, of specific duration (quarter length)
    '''
    noteType = 4
    beatNums = ['1']
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

        self.drawPictureFocus(x, y)

        # Thanks to Olivier Samyn for the note shape
        self.noteHead = goocanvas.Path(parent=self.rootitem,
            data="m %i %i a7,5 0 0,1 12,-3.5 v-32 h2 v35 a7,5 0 0,1 -14,0z" % (x - 7, y),
            fill_color='black',
            stroke_color='black',
            line_width=1.0
            )

        self._drawAlteration(x, y)

        self._drawMidLine(x, y)

        self.y = y
        self.x = x



class HalfNote(Note):
    '''
    an object inherited from Note, of specific duration (half length)
    '''
    noteType = 2
    beatNums = ['1', '2']
    def toMillisecs(self):
        return 1000

    def draw(self, x, y):
        '''
        places note image in canvas
        '''
        self.drawPictureFocus(x, y)

        # Thanks to Olivier Samyn for the note shape
        self.noteHead = goocanvas.Path(parent=self.rootitem,
            data="m %i %i a7,5 0 0,1 12,-3.5 v-32 h2 v35 a7,5 0 0,1 -14,0 z m 3,0 a 4,2 0 0 0 8,0 4,2 0 1 0 -8,0 z" % (x - 7, y),
            fill_color='black',
            stroke_color='black',
            line_width=1.0
            )

        self._drawAlteration(x, y)

        self._drawMidLine(x, y)

        self.y = y
        self.x = x


class WholeNote(Note):
    '''
    an object inherited from Note, of specific duration (whole length)
    '''
    noteType = 1
    beatNums = ['1', '2', '3', '4']
    def toMillisecs(self):
        return 2000

    def draw(self, x, y):
        self.drawPictureFocus(x, y)

        # Thanks to Olivier Samyn for the note shape
        self.noteHead = goocanvas.Path(parent=self.rootitem,
            data="m %i %i a 7,5 0 1 1 14,0 7,5 0 0 1 -14,0 z m 3,0 a 4,2 0 0 0 8,0 a 4,2 0 1 0 -8,0 z" % (x - 7, y),
            fill_color='black',
            stroke_color='black',
            line_width=1.0
            )

        self._drawAlteration(x, y)

        self._drawMidLine(x, y)

        self.y = y
        self.x = x


# ---------------------------------------------------------------------------
#
#  PIANO KEYBOARD
#
# ---------------------------------------------------------------------------

class PianoKeyboard():
    '''
    object representing the one-octave piano keyboard
    '''
    def __init__(self, x, y, canvasroot):
        self.rootitem = goocanvas.Group(parent=canvasroot, x=0, y=0)
        self.x = x
        self.y = y
        self.blackKeys = False # display black keys with buttons?
        self.sharpNotation = True # use sharp notation for notes, (#)
        # if False, use flat notation (b)
        self.whiteKeys = True # display white keys with buttons?

        self.colors = NOTE_COLOR_SCHEME #provide this as an instance
        # variable so future users may edit it

    def draw(self, width, height, key_callback):
        '''
        create piano keyboard, with buttons for keys
        '''

        #piano keyboard image
        goocanvas.Image(
          parent=self.rootitem,
          pixbuf=gcompris.utils.load_pixmap("piano_composition/keyboard.png"),
          x=self.x,
          y=self.y,
          height=height,
          width=width
          )

        '''
        define colored rectangles to lay on top of piano keys for student to click on

        '''

        self.key_callback = key_callback
        w = width * 0.09
        h = height * 0.17
        y = self.y + 0.81 * height
        x = self.x + width * .02
        seperationWidth = w * 1.37

        if self.whiteKeys:
            self.drawKey(x, y, w, h, self.colors[1], 1)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[2], 2)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[3], 3)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[4], 4)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[5], 5)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[6], 6)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[7], 7)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[8], 8)
            x += seperationWidth

        if self.blackKeys:
            w = width * 0.07
            h = height * 0.15
            y = self.y + 0.6 * height
            x = self.x + width * .089
            seperationWidth = w * 1.780

            self.drawKey(x, y, w, h, self.colors[-1], -1)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[-2], -2)
            x += seperationWidth * 2
            self.drawKey(x, y, w, h, self.colors[-3], -3)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[-4], -4)
            x += seperationWidth
            self.drawKey(x, y, w, h, self.colors[-5], -5)


    def drawKey(self, x, y, width, height, color, numID):
        '''
        This function displays the clickable part of the key
        '''
        item = goocanvas.Rect(parent=self.rootitem, x=x, y=y,
                              width=width, height=height,
                              stroke_color="black", fill_color=color,
                              line_width=1.0)
        item.numID = numID

        if numID < 0:
            size = "11000"
            offset = 10
        else:
            size = "15000"
            offset = 13

        keyText = goocanvas.Text(
         parent=self.rootitem,
         x=x + offset,
         y=y + 18,
         width=10,
         text='<span font_family="URW Gothic L" size="' + size + '" weight="bold">' + getKeyNameFromID(numID, self.sharpNotation) + '</span>',
         fill_color="black",
         anchor=gtk.ANCHOR_CENTER,
         alignment=pango.ALIGN_CENTER,
         use_markup=True,
         pointer_events="GOO_CANVAS_EVENTS_NONE"
         )

        gcompris.utils.item_focus_init(keyText, item)

        '''
        connect the piano keyboard rectangles to a button press event,
        the method keyboard_click
        '''
        item.connect("button_press_event", self.key_callback)
        gcompris.utils.item_focus_init(item, None)
        return item




def drawBasicPlayHomePagePart1(self):
    if self.rootitem:
        self.rootitem.remove()

    self.rootitem = goocanvas.Group(parent=
                                   self.gcomprisBoard.canvas.get_root_item())

    # set background
    goocanvas.Image(
        parent=self.rootitem,
        x=0, y=0,
        pixbuf=gcompris.utils.load_pixmap('piano_composition/playActivities/background/' + str(randint(1, 6)) + '.png')
        )

    if hasattr(self, 'staff'):
        self.staff.clear()

    textBox(_('Play'), 220, 30, self, fill_color='gray')

    textBox(_('Okay'), 550, 30, self, fill_color='gray')

def drawBasicPlayHomePagePart2(self):
    # PLAY BUTTON
    self.playButton = goocanvas.Image(
            parent=self.rootitem,
            pixbuf=gcompris.utils.load_pixmap('piano_composition/playActivities/playbutton.png'),
            x=170,
            y=50,
            )
    self.playButton.connect("button_press_event", self.staff.playComposition)

    gcompris.utils.item_focus_init(self.playButton, None)

    # OK BUTTON
    self.okButton = goocanvas.Svg(parent=self.rootitem,
                         svg_handle=gcompris.skin.svg_get(),
                         svg_id="#OK"
                         )
    self.okButton.scale(1.4, 1.4)
    self.okButton.translate(-170, -400)
    self.okButton.connect("button_press_event", self.ok_event)
    gcompris.utils.item_focus_init(self.okButton, None)

    # ERASE BUTTON
    textBox(_("Erase Attempt"), 700, 150, self, fill_color='gray')

    self.eraseButton = goocanvas.Image(
            parent=self.rootitem,
            pixbuf=gcompris.utils.load_pixmap('piano_composition/playActivities/erase.png'),
            x=650,
            y=170,
            )
    self.eraseButton.connect("button_press_event", self.erase_entry)
    gcompris.utils.item_focus_init(self.eraseButton, None)




# ---------------------------------------------------------------------------
#
# UTILITY FUNCTIONS
#
# ---------------------------------------------------------------------------

def ready(self, timeouttime=200):
    '''
    function to help prevent "double-clicks". If your function call is
    suffering from accidental system double-clicks, import this module
    and write these lines at the top of your method:

        if not ready(self):
            return False
    '''
    print 'here'
    if not hasattr(self, 'clickTimers'):
        self.clickTimers = []
        self.readyForNextClick = True
        return True

    def clearClick():
        self.readyForNextClick = True
        return False

    if self.readyForNextClick == False:
        return
    else:
        self.clickTimers.append(gobject.timeout_add(timeouttime, clearClick))
        self.readyForNextClick = False
        return True

def clearResponsePic(self):
    self.responsePic.remove()

def displayYouWin(self, nextMethod):
    '''
    displays the happy note for 900 milliseconds
    '''
    if hasattr(self, 'responsePic'):
        self.responsePic.remove()

    self.responsePic = goocanvas.Image(
    parent=self.rootitem,
    pixbuf=gcompris.utils.load_pixmap('piano_composition/happyNote.png'),
    x=300,
    y=100,
    height=300,
    width=150
    )
    self.responsePic.raise_(None)
    self.timers.append(gobject.timeout_add(900, clearResponsePic, self))
    self.timers.append(gobject.timeout_add(910, nextMethod))
def displayIncorrectAnswer(self, nextMethod):
    '''
    displays the sad note for 900 milliseconds
    '''
    if hasattr(self, 'responsePic'):
        self.responsePic.remove()

    self.responsePic = goocanvas.Image(
    parent=self.rootitem,
    pixbuf=gcompris.utils.load_pixmap('piano_composition/sadNote.png'),
    x=300,
    y=100,
    height=300,
    width=150
    )
    self.responsePic.raise_(None)
    self.timers.append(gobject.timeout_add(900, clearResponsePic, self))
    self.timers.append(gobject.timeout_add(910, nextMethod))


def textButton(x, y, text, self, color='gray', width=100000):
    self.textbox = goocanvas.Text(
        parent=self.rootitem,
        x=x, y=y,
        width=width,
        text=text,
        fill_color="white", anchor=gtk.ANCHOR_CENTER,
        alignment=pango.ALIGN_CENTER,
        pointer_events="GOO_CANVAS_EVENTS_NONE"
        )
    TG = 15
    bounds = self.textbox.get_bounds()

    img = goocanvas.Image(
            parent=self.rootitem,
            x=bounds.x1 - TG,
            y=bounds.y1 - TG,
            height=bounds.y2 - bounds.y1 + TG * 2,
            width=bounds.x2 - bounds.x1 + TG * 2,
            pixbuf=gcompris.utils.load_pixmap('piano_composition/buttons/' + color + '.png')
            )

    gcompris.utils.item_focus_init(img, None)
    self.textbox.raise_(img)
    return img


def textBox(text, x, y , self, width=10000, fill_color=None, stroke_color=None, noRect=False):
    self.text = goocanvas.Text(
        parent=self.rootitem, x=x, y=y, width=width,
        text=text,
        fill_color="black", anchor=gtk.ANCHOR_CENTER,
        alignment=pango.ALIGN_CENTER,

        )
    TG = 10
    bounds = self.text.get_bounds()
    if not noRect:
        rect = goocanvas.Rect(parent=self.rootitem,
                              x=bounds.x1 - TG,
                              y=bounds.y1 - TG,
                              width=bounds.x2 - bounds.x1 + TG * 2,
                              height=bounds.y2 - bounds.y1 + TG * 2,
                              line_width=3.0)
        if fill_color:
            rect.props.fill_color = fill_color
        if stroke_color:
            rect.props.stroke_color = stroke_color
        self.text.raise_(rect)


def pianokeyBindings(keyval, self):
    if keyval == 49:
        self.keyboard_click(None, None, None, 1)
    elif keyval == 50:
        self.keyboard_click(None, None, None, 2)
    elif keyval == 51:
        self.keyboard_click(None, None, None, 3)
    elif keyval == 52:
        self.keyboard_click(None, None, None, 4)
    elif keyval == 53:
        self.keyboard_click(None, None, None, 5)
    elif keyval == 54:
        self.keyboard_click(None, None, None, 6)
    elif keyval == 55:
        self.keyboard_click(None, None, None, 7)
    elif keyval == 56:
        self.keyboard_click(None, None, None, 8)
    elif keyval == gtk.keysyms.F1:
        self.keyboard_click(None, None, None, -1)
    elif keyval == gtk.keysyms.F2:
        self.keyboard_click(None, None, None, -2)
    elif keyval == gtk.keysyms.F3:
        self.keyboard_click(None, None, None, -3)
    elif keyval == gtk.keysyms.F4:
        self.keyboard_click(None, None, None, -4)
    elif keyval == gtk.keysyms.F5:
        self.keyboard_click(None, None, None, -5)

