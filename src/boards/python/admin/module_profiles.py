#  gcompris - module_profiles.py
# 
# Copyright (C) 2005 Bruno Coudoin and Yves Combe
# 
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import gnome
import gnome.canvas
import gcompris
import gcompris.utils
import gcompris.skin
import gtk
import gtk.gdk
from gettext import gettext as _

import module
import profile_list

# Database
from pysqlite2 import dbapi2 as sqlite

class Profiles(module.Module):
  """Administrating GCompris Profiles"""


  def __init__(self, canvas):
    print("Gcompris_administration __init__ profiles panel.")
    module.Module.__init__(self, canvas, "profiles", _("Profiles list"))

  # Return the position it must have in the administration menu
  # The smaller number is the highest.
  def position(self):
    return 2
  
  def start(self, area):
    print "starting profiles panel"

    # Connect to our database
    self.con = sqlite.connect(gcompris.get_database())
    self.cur = self.con.cursor()
        
    # Create our rootitem. We put each canvas item in it so at the end we
    # only have to kill it. The canvas deletes all the items it contains automaticaly.

    self.rootitem = self.canvas.add(
        gnome.canvas.CanvasGroup,
        x=0.0,
        y=0.0
        )

    module.Module.start(self)

    hgap = 20
    vgap = 15

    # Define the area percent for each list
    group_percent = 1.0

    origin_y = area[1]+vgap

    group_height = (area[3]-area[1])*group_percent - vgap
    list_area = ( area[0], origin_y, area[2], group_height)
    profile_list.Profile_list(self.rootitem,
                              self.con, self.cur,
                              list_area, hgap, vgap)

  def stop(self):
    print "stopping profiles panel"
    module.Module.stop(self)

    # Remove the root item removes all the others inside it
    self.rootitem.destroy()

    # Close the database
    self.cur.close()
    self.con.close()