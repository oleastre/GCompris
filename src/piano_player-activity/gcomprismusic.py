# -*- coding: utf-8 -*-
#  gcompris - gcomprismusic.py
#
# Copyright (C) 2003, 2008 Bruno Coudoin
#    Module written by: Beth Hadley
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

    def __init__(self, x, y, canvasRoot):
      self.originalRoot = canvasRoot
      self.x = x        #master X position
      self.y = y        #master Y position

      # ALL LOCATIONS BELOW ARE RELATIVE TO self.x and self.y
      self.endx = 350     #rightend location of staff lines
      self.startx = 0  #leftend location of staff lines
      self.lineNum = 1    #the line number (1,2,3) we're currently writing notes to
      self.line1Y = 0     #starting Y position of first lines of staff
      self.line2Y = 115   #startying Y position of second lines of staff
      self.line3Y = 230   #starting Y position of third lines
      self.currentNoteXCoordinate = self.initialX = 30 #starting X position of first note
      self.noteSpacingX = 30 #distance between each note when appended to staff
      self.staffLineSpacing = 13 #vertical distance between lines in staff
      self.staffLineThickness = 2 # thickness of staff lines

      self.currentNoteType = 'quarterNote' #could be quarter, half, whole (not eight for now)

      self.rootitem = goocanvas.Group(parent=canvasRoot, x=self.x, y=self.y)

      self._drawStaffLines() #draw staff lines

      self.noteList = [] #list of note items written to staff
      self.playingNote = False

      self.timers = []

      self.noteText = goocanvas.Text(
          parent=self.rootitem,
          x=self.startx - 260,
          y= -90,
          width=100,
          text=_('Click a colored box on the keyboard'),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )

    def _drawStaffLines(self):
        '''
        draw three sets of staff lines
        '''
        self._drawLines(x=0, y=0, length=self.endx)
        self._drawLines(x=self.startx, y=self.line2Y, length=self.endx + abs(self.startx))
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
        draw the vertical end bars on each line, and two for the last line
        '''
        goocanvas.polyline_new_line(self.rootitem, self.endx, self.line3Y - 1, self.endx, self.line3Y + 53,
                                     stroke_color="black", line_width=4.0)
        goocanvas.polyline_new_line(self.rootitem, self.endx - 7, self.line3Y - 1, self.endx - 7, self.line3Y + 53,
                                     stroke_color="black", line_width=3.0)

        goocanvas.polyline_new_line(self.rootitem, self.endx, self.line1Y - 1, self.endx, self.line1Y + 53,
                                     stroke_color="black", line_width=3.0)

        goocanvas.polyline_new_line(self.rootitem, self.endx, self.line2Y - 1, self.endx, self.line2Y + 53,
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
        self.noteList.append(note) #adds note object to staff list

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
        if not ready(self):
            return False

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
        self.staffImage1.remove()
        self.staffImage2.remove()
        self.staffImage3.remove()
        self.noteText.remove()

    def play_it(self):
        '''
        called to play one note. Checks to see if all notes have been played
        if not, establishes a timer for the next note depending on that note's
        duration (quarter, half, whole)
        colors the note red that it is currently sounding
        '''

        if self._playedAll():
            self.noteList[self.currentNoteIndex - 1].color('black')
            return False
        note = self.noteList[self.currentNoteIndex]
        self.writeText('Note Name: ' + note.niceName)
        note.play()
        note.color('red')
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

        if not self.noteList:
            return

        if not ready(self):
            return False

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

    def writeText(self, text):
        self.noteText.props.text = text

    def staff_to_file(self, filename):
        '''
        uses python's cpickle to save the python object stored in self, a Staff instance
        '''
        file = open(filename, 'wb')

        # Save the descriptif frame:
        pickle.dump(self, file, 2)

        file.close()

    def file_to_staff(self, filename):
        '''
        uses python's cpickle to load the python object, a staff instance
        '''

        file = open(filename, 'rb')
        try:
            loadedStaff = pickle.load(file)
        except:
            file.close()
            print 'Cannot load ', filename , " as a GCompris animation"
            return
        #self.rootitem = self.originalRoot

        self.clear()

        '''
        PROBLEM: I can't seem to be able to get a direct pointer from the
        loadedStaff instance to the self instance....This would be cleanest,
        but I'm getting a nasty error about rootitems that I can't seem
        to fix. I tried copy.deepcopy on the loaded staff, but that also
        doesn't work...
        '''
#        self = copy.deepcopy(loadedStaff)
#        self = loadedStaff
#        for note in self.noteList:
#            print note
#            self.drawNote(note)

        '''
        So my fall-back solution is to reconstruct the objects manually. This
        is a huge waste of the power of pickle, and I'd like to figure out
        how not to do this. Help please ?
        '''
        if loadedStaff.name == 'trebleClef':
            y = TrebleStaff(self.x, self.y, self.originalRoot)

        else:
            y = BassStaff(self.x, self.y, self.originalRoot)
        self.positionDict = y.positionDict
        self.name = y.name

        for n in loadedStaff.noteList:
            if n.noteType == 'quarterNote':
                note = QuarterNote(n.noteName, loadedStaff.name, self.rootitem)
            elif n.noteType == 'halfNote':
                note = HalfNote(n.noteName, loadedStaff.name, self.rootitem)
            elif n.noteType == 'wholeNote':
                note = WholeNote(n.noteName, loadedStaff.name, self.rootitem)
            else:
                print 'ERROR: notetype not supported: ' , n.noteType

            self.drawNote(note)

        file.close()

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

        return  self.positionDict[note.noteName[0:2].strip()] + yoffset + 36


class TrebleStaff(Staff):
    '''
    unique type of Staff with clef type specified and certain dimensional
    conventions maintained for certain notes
    '''
    def __init__(self, x, y, canvasRoot):
        Staff.__init__(self, x, y, canvasRoot)
        self._drawClefs()
        self.name = 'trebleClef'

         # for use in getNoteYCoordinateMethod
        self.positionDict = {'C':26, 'D':22, 'E':16, 'F':9, 'G':3,
                        'A':-4, 'B':-10, 'C2':-17}
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

class BassStaff(Staff):
    '''
    unique type of Staff with clef type specified and certain dimensional
    conventions maintained for certain notes
    '''
    def __init__(self, x, y, canvasRoot):
        Staff.__init__(self, x, y, canvasRoot)
        self._drawClefs()
        self.name = 'bassClef'

        # for use in getNoteYCoordinateMethod
        self.positionDict = {'C':-4, 'D':-11, 'E':-17, 'F':-24, 'G':-30,
                        'A':-36, 'B':-42, 'C2':-48}
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
    def __init__(self, noteName, staffType, rootitem):
        self.noteName = noteName
        self.staffType = staffType #'trebleClef' or 'bassClef'
        self.niceName = noteName.replace('2', '')
        self.x = 0
        self.y = 0
        self.rootitem = goocanvas.Group(parent=rootitem, x=self.x, y=self.y)

        self.pitchDir = self._getPitchDir()

    def _drawMidLine(self, x, y):
        if self.staffType == 'trebleClef' and self.noteName == 'C'  or \
           self.staffType == 'bassClef' and self.noteName == 'C2' or \
           self.staffType == 'trebleClef' and self.noteName == 'C sharp':
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
        '''
        uses the note's raw name to find the pitch directory associate to it.
        Since only sharp pitches are stored, method finds the enharmonic name
        to flat notes using the circle of fifths dictionary
        '''
        circle_of_fifths = {'D flat' : 'Cs',
                            'E flat' : 'Ds',
                            'G flat' : 'Fs',
                            'A flat' : 'Gs',
                            'B flat' : 'As'
                            }

        if 'sharp' in self.noteName:
            self.pitchName = self.noteName[0] + 's'
        elif 'flat' in self.noteName:
            self.pitchName = circle_of_fifths[self.noteName]
        else:
            self.pitchName = self.noteName

        if self.staffType == 'trebleClef':
             pitchDir = 'treble_pitches/' + self.noteType + '/' + self.pitchName + '.ogg'
        else:
             pitchDir = 'bass_pitches/' + self.noteType + '/' + self.pitchName + '.ogg'

        return pitchDir


    def _drawAlteration(self, x, y):
        '''
        draws a flat or a sharp sign in front of the note if needed
        '''
        if 'sharp' in self.noteName:
            self.alteration = goocanvas.Image(
              parent=self.rootitem,
              pixbuf=gcompris.utils.load_pixmap("sharp.png"),
              x=x - 23,
              y=y - 10,
              height=20,
              width=20
              )
            self.alteration.set_data('type', 'sharp')
        elif 'flat' in self.noteName:
            self.alteration = goocanvas.Image(
              parent=self.rootitem,
              pixbuf=gcompris.utils.load_pixmap("flat.png"),
              x=x - 23,
              y=y - 14,
              height=20,
              width=20
              )
            self.alteration.set_data('type', 'flat')


    def remove(self):
        '''
        removes the note from the canvas
        '''
        self.noteHead.remove()
        if hasattr(self, 'noteFlag'):
            self.noteFlag.remove()
        if hasattr(self, 'midLine'):
            self.midLine.remove()
        if hasattr(self, 'alteration'):
            self.alteration.remove()

    def colorAlteration(self, color):
        '''
        colors the flat or sharp sign
        '''
        if hasattr(self, 'alteration'):
            str = self.alteration.get_data('type')
        else:
            return

        if color == 'red':
            self.alteration.props.pixbuf = gcompris.utils.load_pixmap("red" + str + ".png")
        elif color == 'black':
            self.alteration.props.pixbuf = gcompris.utils.load_pixmap(str + ".png")
        self.alteration.props.height = 20
        self.alteration.props.width = 20

    def colorNoteHead(self, color, fill=True, outline=True):
        '''
        colors the notehead, by default both the fill and the outline
        '''
        if fill:
            self.noteHead.props.fill_color = color
        if outline:
            self.noteHead.props.stroke_color = color

        if hasattr(self, 'midLine'):
            self.midLine.props.fill_color = color
            self.midLine.props.stroke_color = color

    def colorNoteFlag(self, color):
        '''
        colors the note flag (vertical line)
        '''
        if hasattr(self, 'noteFlag'):
            self.noteFlag.props.fill_color = color
            self.noteFlag.props.stroke_color = color

    def color(self, color):
        '''
        default color method. colors all components, including notehead's fill
        '''
        self.colorNoteHead(color)
        self.colorNoteFlag(color)
        self.colorAlteration(color)

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


        self._drawAlteration(x, y)

        self.y = y
        self.x = x

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
        self._drawAlteration(x, y)
        self.y = y
        self.x = x

    def color(self, color):
        '''
        colors all components except notehead fill
        '''
        self.colorNoteHead(color, fill=False)
        self.colorNoteFlag(color)
        self.colorAlteration(color)


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
        self._drawAlteration(x, y)
        self.y = y
        self.x = x

    def color(self, color):
        '''
        colors all components except notehead fill
        '''
        self.colorNoteHead(color, fill=False)
        self.colorAlteration(color)


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
        self.rootitem = goocanvas.Group(parent=canvasroot, x=x, y=y)
        self.x = x
        self.y = y
        self.blackKeys = False # display black keys with buttons?
        self.sharpNotation = True # use sharp notation for notes, (#)
        # if False, use flat notation (b)
        self.whiteKeys = True # display white keys with buttons?

    def draw(self, width, height):
        '''
        create piano keyboard, with buttons for keys
        '''
        #piano keyboard image
        goocanvas.Image(
          parent=self.rootitem,
          pixbuf=gcompris.utils.load_pixmap("keyboard.png"),
          x=0,
          y=0,
          height=height,
          width=width
          )

        '''
        define colored rectangles to lay on top of piano keys for student to click on

        Translators: note that you must write the translated note name matching the given note name in the English notation
         For example, in French the correct translations would be:
        A (la), B (si), C (do), D (ré), E (mi), F (fa) , G (sol)
        '''

        keyWidth = width * 0.09
        keyHeight = height * 0.09
        ypose = 0.85 * height
        xpose = width * .02
        seperationWidth = keyWidth * 1.37

        if self.whiteKeys:
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


        if self.blackKeys:

            keyWidth = width * 0.07
            keyHeight = height * 0.08
            ypose = 0.7 * height
            xpose = width * .089
            seperationWidth = keyWidth * 1.780


            self.key1 = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                            width=keyWidth, height=keyHeight,
                            stroke_color="black", fill_color="white",
                            line_width=1.0)

            xpose += seperationWidth
            self.key2 = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                       width=keyWidth, height=keyHeight,
                                       stroke_color="black", fill_color="purple",
                                       line_width=1.0)

            xpose += seperationWidth * 2
            self.key3 = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                       width=keyWidth, height=keyHeight,
                                       stroke_color="black", fill_color="pink",
                                       line_width=1.0)

            xpose += seperationWidth
            self.key4 = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                       width=keyWidth, height=keyHeight,
                                       stroke_color="black", fill_color="red",
                                       line_width=1.0)

            xpose += seperationWidth
            self.key5 = goocanvas.Rect(parent=self.rootitem, x=xpose, y=ypose,
                                       width=keyWidth, height=keyHeight,
                                       stroke_color="black", fill_color="orange",
                                       line_width=1.0)

            if self.sharpNotation:
                self.key1.name = _("C sharp")
                self.key2.name = _("D sharp")
                self.key3.name = _("F sharp")
                self.key4.name = _("G sharp")
                self.key5.name = _("A sharp")
            else:
                self.key1.name = _("D flat")
                self.key2.name = _("E flat")
                self.key3.name = _("G flat")
                self.key4.name = _("A flat")
                self.key5.name = _("B flat")


# ---------------------------------------------------------------------------
#
# UTILITY FUNCTIONS            
#
# ---------------------------------------------------------------------------

def ready(self):
    '''
    function to help prevent "double-clicks". If your function call is
    suffering from accidental system double-clicks, import this module
    and write these lines at the top of your method:
    
        if not ready(self):
            return False
    '''
    if not hasattr(self, 'clickTimers'):
        self.clickTimers = []
        self.readyForNextClick = True
        return True

    def clearClick():
        self.readyForNextClick = True
        return False

    if self.readyForNextClick == False:
        return False
    else:
        self.clickTimers.append(gobject.timeout_add(300, clearClick))
        self.readyForNextClick = False
        return True

