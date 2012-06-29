#  gcompris - world_explore_template.py
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
# world_explore_template

'''
TO-DO:
    - write credits from content.desktop.in to xml file?

    - add more features???
    - make the 'game' for challenging?

Done:
    - completed two locations as samples (Australia and Africa)
    - make music playing/pausing/etc smooth...right now the music stops spontaneously
    - use template to make music around the world activity
    - replace boring icons with exciting images
'''

'''
HOW-TO USE THIS TEMPLATE:

This activity is intended to be used as a template for development of future
activities of similar format. The activity features an exploration of interesting
topics at different locations around the world. For example, themes might include
music, landmarks, traditions, languages, etc. around the world.

Customizing this activity for a specific theme is easy. All information
is read from a text file, so you must only modify the text file (entitled content.desktop.in)
However, to create the locations on the map that you'd like to discuss in your activity,
you must, run this activity with RECORD_LOCATIONS = True. This will open the map,
and you can click locations on the map. Notice the numbers that appear when you
click. These numbers correspond to the section in the text file that you will
enter content regarding that location, so it is best to keep a record of which
locations you choose on the map correspond to which numbers.

Once you've entered all locations, quit the gcompris program and be sure to set
RECORD_LOCATIONS = False. Next, find content.desktop.in in the resources folder and modify
the content. Each section corresponds to a location on your map. For example,
section 1 looks like this:

[1]
x = 270
y = 245
name = Location Title Here
text = location text here
image = default.png
music = music file name here
question = enter question about topic here
answeroptions = provide comma-seperated list, of answer options here, The correct answer should, be listed FIRST.

This is automatically generated with the section number, and correct x and y corrdinates.
You then must enter the correct content:

name: Enter the name of the location

text: Enter whatever textual information you'd like to appear on the page

image: Enter the file location of a picture you'd like to appear on the page. Be sure
to save the picture in the resources folder. The size of the picture will not be
scaled in any way, so save the picture at the size you'd like it to appear in
the activity. (example: default.png) You should use png files.

music: Enter the file location of a .wav file you'd like to play for the lcoation.
You must use .wav files. Use audacity to convert .ogg and .mp3 files to .wav

question: Enter a quesiton you'd like to ask the students about the topic to
test their understanding. This provides some challenge in the game and an incentive
to visit all the locations. Example: Where is the Eiffel Tower?

answeroptions: the list of optional answers to your question (like multiple-choice).
list the correct answer first, followed by any number of incorrect choices. During runtime,
the options will be sorted alphabetically so the correct answer won't always be first.
Example: France, Italy, USA, China

Be sure all the image and music files you specified are in the resources folder
of your new activity. If you do not wish to include an entry (no music for example)
just leave that line blank.
'''

import gobject
import gtk
import gtk.gdk
import gcompris
import gcompris.utils
import gcompris.skin
import goocanvas
import pango
import ConfigParser
import gcompris.sound
from gcompris import gcompris_gettext as _

# set to True if you'd like to record selected locations to make a new activity
# BEWARE: setting this to true will delete all your previous records!
RECORD_LOCATIONS = False
ACTIVITY = 'worldanimals' # or 'worldmusic' (THIS IS A TEMPORARY SOLUTION UNTIL
# I FIGURE OUT HOW TO DO HAVE SEPERATE ACTIVITIES!)
class Gcompris_explore:


    def __init__(self, gcomprisBoard):
        # Save the gcomprisBoard, it defines everything we need
        # to know from the core
        self.gcomprisBoard = gcomprisBoard

        # Needed to get key_press
        gcomprisBoard.disable_im_context = True


        self.numLocations = 0 # the total number of locations in this activity
        self.data = ConfigParser.RawConfigParser() # the data that is parsed from
        # content.desktop.in
        self.timers = []
        self.score = 0 # the number of locations the student has selected the
        # correct answer for (max score == self.numLocations)
        self.sectionsAnsweredCorrectly = [] # list of section numbers that
        # the student has successfully answered

    def start(self):
        '''
        method called to create 'home-page', the world map with all the locations.
        This method is re-called whenever 'Go Back To Map' button is pressed
        by any of the location pages.
        '''
        # Set the buttons we want in the bar
        gcompris.bar_set(0) # just quit and help buttons
        gcompris.bar_location(20, -1, 0.6) # small, bottom left corner

        gcompris.set_default_background(self.gcomprisBoard.canvas.get_root_item())

        # are these the correct commands to suspend sound?
        self.saved_policy = gcompris.sound.policy_get()
        gcompris.sound.policy_set(gcompris.sound.PLAY_AND_INTERRUPT)
        gcompris.sound.pause()

        self.loadHomePage()

    def loadHomePage(self, x=None, y=None, z=None):
        gcompris.sound.play_ogg('//boards/sounds/silence1s.ogg')
        # Create our rootitem.
        if hasattr(self, 'rootitem'):
            self.rootitem.remove()
        self.rootitem = goocanvas.Group(parent=
                                        self.gcomprisBoard.canvas.get_root_item())

        # -------------------------------------------------------------
        # Draw home page
        # -------------------------------------------------------------
        self.read_data() # read in the data from content.desktop.in file

        self.map = goocanvas.Image(
            parent=self.rootitem,
            x=20, y=20,
            width=760,
            height=450,
            pixbuf=gcompris.utils.load_pixmap(self.background)
            )

        if RECORD_LOCATIONS:
            for section in self.data.sections():
                if section != 'common':
                    self.data.remove_section(section)

            self.map.connect("button_press_event", self.record_location)
            gcompris.utils.item_focus_init(self.map, None)
        else:

            self.drawLocations() # draw the locations on the map
            txt = _('Explore the world! Click the locations.')
            goocanvas.Text(
              parent=self.rootitem,
              x=100,
              y=230,
              width=150,
              text='<span font_family="URW Gothic L" size="medium" \
              weight="bold" style="italic">' + txt + '</span>',
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER,
              use_markup=True
              )

            txt2 = _('Explore Status:')
            goocanvas.Text(
              parent=self.rootitem,
              x=180,
              y=490,
              text='<span font_family="URW Gothic L" size="medium" \
              weight="bold" style="italic">' + txt2 + '</span>',
              anchor=gtk.ANCHOR_CENTER,
              alignment=pango.ALIGN_CENTER,
              use_markup=True
              )

#            goocanvas.Image(
#                parent=self.rootitem,
#                x=30,
#                y=280,
#                pixbuf=gcompris.utils.load_pixmap('travel.png')
#                )

            # check to see if student has won game
            if self.score == (len(self.data.sections()) - 1) and self.score != 0:
                # show congratulations image!
                goocanvas.Image(
                parent=self.rootitem,
                x=100, y= -30,
                pixbuf=gcompris.utils.load_pixmap('explore/winner.png')
                )
                # reset the game
                self.score = 0
                self.sectionsAnsweredCorrectly = []
                self.timers = []
                self.timers.append(gobject.timeout_add(3000, self.loadHomePage))

            x = 240 # starting x position of progress bar
            self.progressBar = goocanvas.Rect(parent=self.rootitem,
                    x=x, y=480, width=500, height=25,
                    stroke_color="black",
                    line_width=3.0)

            # display the correct progress in the progress bar, according to the 
            # number of locations the student has correclty answered the question for
            for num in range(0, self.score):
                barwidth = 500.0 / (len(self.data.sections()) - 1)
                goocanvas.Rect(parent=self.rootitem,
                x=x, y=480, width=barwidth, height=25,
                stroke_color="black",
                fill_color="#32CD32",
                line_width=3.0)

                goocanvas.Image(
                parent=self.rootitem,
                x=x + (barwidth / 2.0) - 15,
                y=460,
                pixbuf=gcompris.utils.load_pixmap('explore/ribbon.png')
                )
                x += barwidth

    def record_location(self, widget=None, target=None, event=None):
        '''
        method generates output to content.desktop.in according to the specified format.
        Method called if RECORD_LOCATIONS = True and developer clicks map. Merhod
        record the location of the click, and writes a template of the section
        to content.desktop.in to be filled in later by the developer.
        '''
        self.numLocations += 1
        self.data.add_section(str(self.numLocations))
        x = event.x
        y = event.y
        self.data.set(str(self.numLocations), 'x', int(x))
        self.data.set(str(self.numLocations), 'y', int(y))
        self.data.set(str(self.numLocations), '_title', _('Location Title Here'))
        self.data.set(str(self.numLocations), '_text', _('location text here'))
        self.data.set(str(self.numLocations), 'image', _('/explore/default.png'))
        self.data.set(str(self.numLocations), 'music', _('music file name here'))
        self.data.set(str(self.numLocations), '_question', _('enter question about topic here'))
        self.data.set(str(self.numLocations), '_answerOptions', _('provide \
comma-seperated list, of answer options here, The correct answer should, be listed FIRST.'))

        # draw small elipse on screen to show developer where they clicked
        goocanvas.Ellipse(parent=self.rootitem,
        center_x=x,
        center_y=y,
        radius_x=5,
        radius_y=5,
        fill_color='white',
        stroke_color='white',
        line_width=1.0)

        # write a small number ontop of the ellipse so developer can record
        # which numbers (sections) correspond to which locations
        goocanvas.Text(
        parent=self.rootitem,
        x=x,
        y=y,
        text=str(self.numLocations),
        anchor=gtk.ANCHOR_CENTER,
        alignment=pango.ALIGN_CENTER,
        )

    def read_data(self):
        '''
        method to read in the data from content.desktop.in. Saves this data as
        self.data for reference later.
        '''
        config = ConfigParser.RawConfigParser()
        filename = gcompris.DATA_DIR + '/explore/' + ACTIVITY + '/content.desktop.in'
        try:
            gotit = config.read(filename)
            if not gotit:
                gcompris.utils.dialog(_("Cannot find the file '{filename}'").\
                                    format(filename=filename),
                                None)
                return False
        except ConfigParser.Error, error:
                gcompris.utils.dialog(_("Failed to parse data set '{filename}'"
                                  " with error:\n{error}").\
                                  format(filename=filename, error=error),
                                None)
                return False

        self.data = config
        self.parseData()

    def parseData(self):
        self.sectionNames = []
        for section in self.data.sections():
            if section == 'common':
                try: self.credits = self.data.get('common', 'credits')
                except: self.credits = ''
                try: self.background = self.data.get('common', 'background')
                except:  gcompris.utils.dialog(_("Cannot find background in \
                content.desktop.in"), None, None)
                try: self.author = self.data.get('common', 'author')
                except: self.author = ''
                try: self.locationPic = self.data.get('common', 'locationpic')
                except: self.locationPic = '/explore/defaultLocationPic.png'
                try: self.completedLocationPic = self.data.get('common', 'completedlocationpic')
                except: self.completedLocationPic = '/explore/defaultCompletedLocationPic.png'
            else:
                self.sectionNames.append(section)

    def drawLocations(self):
        '''
        draw ellipses on the map, one for each section in content.desktop.in at the
        location specified in the file by 'x' and 'y'. If the student
        has already visited the location and correctly answered the quetsion,
        thellipse will be colored green. Otherwise, the ellipse is red.
        '''

        for section in self.sectionNames:
            if section in self.sectionsAnsweredCorrectly:
                filename = self.completedLocationPic
            else:
                filename = self.locationPic
            vars()[section] = goocanvas.Image(
                parent=self.rootitem,
                x=int(self.data.get(section, 'x')) - 20,
                y=int(self.data.get(section, 'y')) - 20,
                pixbuf=gcompris.utils.load_pixmap(filename)
                )

            vars()[section].connect("button_press_event", self.goto_location)
            gcompris.utils.item_focus_init(vars()[section], None)
            vars()[section].set_data('sectionNum', section)

    def goto_location(self, widget=None, target=None, event=None):
        '''
        method called when student clicks on one of the ellipses.
        method loads the location page, including the text, picture, music, and question.
        '''
        self.rootitem.remove()
        self.rootitem = goocanvas.Group(parent=
                                        self.gcomprisBoard.canvas.get_root_item())
        sectionNum = target.get_data('sectionNum')


        # ---------------------------------------------------------------------
        # Page Decorations
        # ---------------------------------------------------------------------
#        self.image = goocanvas.Image(
#            parent=self.rootitem,
#            x=330,
#            y=460,
#            pixbuf=gcompris.utils.load_pixmap('explore/plane.png')
#            )

#        goocanvas.Image(
#            parent=self.rootitem,
#            x=610,
#            y=350,
#            pixbuf=gcompris.utils.load_pixmap('explore/luggage.png')
#            )

        goocanvas.Image(
            parent=self.rootitem,
            x=10,
            y=10,
            pixbuf=gcompris.utils.load_pixmap('explore/border.png')
            )

        # draw back button
        txt = _('Back To World Map')
        self.backButton = goocanvas.Text(
          parent=self.rootitem,
          x=230,
          y=490,
          text='<span font_family="purisa" size="medium" style="italic">' + txt + '</span>',
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER,
          use_markup=True
          )

        self.backButton.connect("button_press_event", self.loadHomePage)
        gcompris.utils.item_focus_init(self.backButton, None)

        # ---------------------------------------------------------------------
        # WRITE LOCATION-SPECIFIC CONTENT TO PAGE
        # ---------------------------------------------------------------------

        name = _(self.data.get(sectionNum, '_title'))
        goocanvas.Text(
          parent=self.rootitem,
          x=410,
          y=50,
          text='<span font_family="century schoolbook L" size="x-large" weight="bold">' + name + '</span>',
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER,
          use_markup=True
          )

        text = self.data.get(sectionNum, '_text')
        goocanvas.Text(
          parent=self.rootitem,
          x=150,
          y=290,
          width=220,
          text=_(text),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )
        image = self.data.get(sectionNum, 'image')
        goocanvas.Image(
            parent=self.rootitem,
            x=300,
            y=75,
            pixbuf=gcompris.utils.load_pixmap(image)
            )

        question = self.data.get(sectionNum, '_question')
        goocanvas.Text(
          parent=self.rootitem,
          x=500,
          y=390,
          width=400,
          text=_(question),
          fill_color="black",
          anchor=gtk.ANCHOR_CENTER,
          alignment=pango.ALIGN_CENTER
          )

        options = self.data.get(sectionNum, '_answerOptions').split(',')
        m = []
        for el in options:
            m.append(el.strip())
        self.correctAnswer = m[0]
        m.sort()
        y = 400
        for answer in m:
            y += 25
            vars(self)[answer] = goocanvas.Text(
                  parent=self.rootitem,
                  x=500,
                  y=y,
                  text=_(answer),
                  anchor=gtk.ANCHOR_CENTER,
                  alignment=pango.ALIGN_CENTER,
                  )

            vars(self)[answer].connect("button_press_event",
            lambda x, y, z: self.check_answer(sectionNum, x, y, z))
            gcompris.utils.item_focus_init(vars(self)[answer], None)

        # play music...do I need a timer to do this? seems to work okay so far....
        try:
            music = str(self.data.get(sectionNum, 'music'))
            gcompris.sound.play_ogg(music)
        except: pass



    def check_answer(self, sectionNum, widget=None, target=None, event=None):
        '''
        check to see if the student pressed the correct answer. If so, increment
        score. Display appropriate face (happy or sad) for 800 ms.
        '''
        if target.props.text == self.correctAnswer:
            if not (sectionNum in self.sectionsAnsweredCorrectly):
                self.score += 1
                self.sectionsAnsweredCorrectly.append(sectionNum)
            pic = 'explore/happyFace.png'
        else:
            pic = 'explore/sadFace.png'

        if hasattr(self, 'responsePic'):
            self.responsePic.remove()

        self.responsePic = goocanvas.Image(
        parent=self.rootitem,
        pixbuf=gcompris.utils.load_pixmap(pic),
        x=200,
        y=50
        )
        self.timers.append(gobject.timeout_add(800, self.clearPic))

    def clearPic(self):
        '''
        remove happy/sad face
        '''
        if hasattr(self, 'responsePic'):
            self.responsePic.remove()

    def end(self):
        if RECORD_LOCATIONS:
            # write locations and template to content.desktop.in
            self.data.set('common', 'credits', _('enter a list of credits and \
links to resources you used here'))
            self.data.set('common', 'creator', _('enter your name here!'))
            with open(gcompris.DATA_DIR + '/explore/' + ACTIVITY + '/content.desktop.in', 'wb') as configfile:
                self.data.write(configfile)

        self.rootitem.remove()
        gcompris.sound.policy_set(self.saved_policy)
        gcompris.sound.resume()

    def ok(self):
        pass
    def repeat(self):
        pass

    def config_stop(self):
        pass

    def config_start(self, profile):
        pass

    def key_press(self, keyval, commit_str, preedit_str):
        utf8char = gtk.gdk.keyval_to_unicode(keyval)
        strn = u'%c' % utf8char

    def pause(self, pause):
        pass

    def set_level(self, level):
        pass


