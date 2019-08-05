# SIFTeam OpenAirPlay
# Copyright (C) <2012> skaman (SIFTeam)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigYesNo

from airplay import AirPlay

config.OpenAirPlay = ConfigSubsection()
config.OpenAirPlay.enabled = ConfigYesNo(default=True)

global_session = None
global_airplay = None

class OpenAirPlayConfig(Screen, ConfigListScreen):
	skin = """
	<screen position="center,center" size="560,400" title="SIFTeam OpenAirPlay Configuration">
		<ePixmap name="red" pixmap="buttons/red.png" position="0,0" size="140,40" zPosition="0" transparent="1" alphatest="on" />
		<ePixmap name="green" pixmap="buttons/green.png" position="140,0" size="140,40" zPosition="0" transparent="1" alphatest="on" />
		<ePixmap name="yellow" pixmap="buttons/yellow.png" position="280,0" size="140,40" zPosition="0" transparent="1" alphatest="on" />
		<ePixmap name="blue" pixmap="buttons/blue.png" position="420,0" size="140,40" zPosition="0" transparent="1" alphatest="on" />
		
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="1" transparent="1" foregroundColor="white" font="Regular;18" />
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="1" transparent="1" foregroundColor="white" font="Regular;18" />
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="1" transparent="1" foregroundColor="white" font="Regular;18" />
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="1" transparent="1" foregroundColor="white" font="Regular;18" />
		
		<widget name="config" position="10,50" size="540,240" scrollbarMode="showOnDemand" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [])
		
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")
		
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"red": self.keyCancel,
			"back": self.keyCancel,
			"green": self.ok
		}, -2)
		
		self.list = []
		self.list.append(getConfigListEntry(_("OpenAirPlay Enabled"), config.OpenAirPlay.enabled))
		self["config"].setList(self.list)
		
	def ok(self):
		self.keySave()
		
		if config.OpenAirPlay.enabled.value:
			startServer()
		else:
			stopServer()
			
		self.close()

def startConfiguration(session, **kwargs):
		session.open(OpenAirPlayConfig)

def startServer():
	global global_session
	global global_airplay
	
	if global_session is None:
		return
		
	if global_airplay is None:
		global_airplay = AirPlay(global_session)
		global_airplay.start()
	
def stopServer():
	global global_airplay
	
	if global_airplay is not None:
		global_airplay.stop()
		global_airplay = None

def autoStart(reason, **kwargs):
	# we use autostart only for stop server... the start is handled on networkConfigRead
	if reason == 1:
		stopServer()
		
def networkConfigRead(reason, **kwargs):
	if reason is True:
		if config.OpenAirPlay.enabled.value:
			startServer()
	else:
		stopServer()
		
def sessionStart(reason, session):
	global global_session
	global_session = session

def Plugins(**kwargs):
	return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionStart),
		PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART], fnc=autoStart),
		PluginDescriptor(where=[PluginDescriptor.WHERE_NETWORKCONFIG_READ], fnc=networkConfigRead),
		PluginDescriptor(name="OpenAirPlay", description="SIFTeam OpenAirPlay Configuration", icon="openairplay.png", where=[PluginDescriptor.WHERE_PLUGINMENU], fnc=startConfiguration)]


