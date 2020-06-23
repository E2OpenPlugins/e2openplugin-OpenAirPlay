from __future__ import absolute_import
from __future__ import print_function
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

from enigma import ePicLoad, eServiceReference, eTimer
from Screens.Screen import Screen
from Components.config import config
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.ServiceEventTracker import ServiceEventTracker

from .airplayserver import APServer, APCallbacks

class AirPlayPhoto(Screen):
	skin = """
		<screen position="0,0" size="e,e" flags="wfNoBorder">
			<widget name="image" position="20,20" size="e-40,e-40" />
		</screen>"""
		
	def __init__(self, session):
		Screen.__init__(self, session)
		self["image"] = Pixmap()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.__showPic)
		
	def __showPic(self, picInfo=""):
		ptr = self.picload.getData()
		if ptr != None:
			self["image"].instance.setPixmap(ptr.__deref__())
			self["image"].show()
			
	def load(self, data):
		open("/tmp/airphoto.jpg", "w").write(data)
		#sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self["image"].instance.size().width(), self["image"].instance.size().height(), 1, 1, False, 1, "#FF000000"))
		self.picload.startDecode("/tmp/airphoto.jpg")
		
	def exit(self):
		self.close()

class AirPlayAudio(Screen):
	skin = """
		<screen position="0,0" size="e,e" flags="wfNoBorder">
		</screen>"""
		
	def __init__(self, session):
		Screen.__init__(self, session)
		self.serviceref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		
	def exit(self):
		if self.serviceref is not None:
			self.session.nav.playService(self.serviceref)
		self.close()
		
class AirPlayVideo(Screen):
	skin = """
		<screen position="0,0" size="e,e" flags="wfNoBorder" backgroundColor="#FF000000">
		</screen>"""
		
	def __init__(self, session):
		Screen.__init__(self, session)
		self.videomodes = ["4_3_letterbox", "4_3_panscan", "16_9", "16_9_always", "16_10_letterbox", "16_10_panscan", "16_9_letterbox"]
		#self.videodescs = ["4:3 Letterbox", "4:3 Panscan", "16:9", "16:9 Always", "16:10 Letterbox", "16:10 Panscan", "16:9 Letterbox"]
		self.serviceref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		self.paused = True
		self.position = 0
		
		self["setupActions"] = ActionMap(["ColorActions"],
		{
			"green": self.changeVideoMode
		}, -2)

	def changeVideoMode(self):
		iAVSwitch = AVSwitch()
		aspectnum = iAVSwitch.getAspectRatioSetting()
		aspectnum += 1
		if aspectnum >= len(self.videomodes):
			aspectnum = 0
		iAVSwitch.setAspectRatio(aspectnum)
		config.av.aspectratio.setValue(self.videomodes[aspectnum])
		
	def open(self, url):
		self.session.nav.playService(eServiceReference(4097, 0, url))
		self.paused = False
		
	def play(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return
			
		pauseable = service.pause()
		if pauseable is None:
			return
			
		pauseable.unpause()
		self.paused = False
		if self.position != 0:
			self.setPosition(self.position)
		
	def pause(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return
			
		pauseable = service.pause()
		if pauseable is None:
			return
			
		pauseable.pause()
		self.paused = True
		
	def getPosition(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		
		seek = service.seek()
		if seek is None:
			return None
		
		length = 0.0
		position = 0.0
		llength = seek.getLength()
		lposition = seek.getPlayPosition()
		
		if not llength[0]:
			length = float(llength[1]) / 90000.0
		
		if self.paused:
			position = self.position
		elif not lposition[0]:
			position = float(lposition[1]) / 90000.0
			
		if position < 0.0:
			position = 0.0
			
		if length < 0.0:
			length = 0.0
			
		# if near the end or over we override the position
		if position > length - 1.0:
			position = length
			
		loaded = 0.0
		streamed = service.streamed()
		if streamed is not None:
			charge = streamed.getBufferCharge()
			
			if charge[2] != 0:
				loaded = float(charge[4]) / float(charge[2])
				
		return {
			"duration": length,
			"position": position,
			"loaded": loaded,
			"paused": self.paused
		}
		
	def setPosition(self, position):
		if self.paused:
			self.position = position
			return
			
		service = self.session.nav.getCurrentService()
		if service is None:
			return
		
		seek = service.seek()
		if seek is None:
			return
			
		if not seek.isCurrentlySeekable():
			print("[SIFTeam OpenAirPlay] service not currently seekable")
			return
			
		seek.seekTo(int(position * 90000))
		self.position = 0
		
	def exit(self):
		if self.serviceref is not None:
			self.session.nav.playService(self.serviceref)
		self.close()
		
class AirPlay():
	def __init__(self, session):
		self.session = session
		self.callbacks = APCallbacks()
		self.callbacks.photo = self.__photo
		self.callbacks.audio = self.__audio
		self.callbacks.video = self.__video
		self.callbacks.videoPlay = self.__videoPlay
		self.callbacks.videoPause = self.__videoPause
		self.callbacks.videoGetPosition = self.__videoGetPosition
		self.callbacks.videoSetPosition = self.__videoSetPosition
		self.callbacks.stop = self.__close
		self.callbacks.stopAudio = self.__closeAudio
		self.server = APServer(self.callbacks)
		self.current = None
		self.videorequest = False
		self.videourl = ""
		
	def stop(self):
		self.server.stop()
		
	def start(self):
		self.server.start()
		
	def __photo(self, data):
		if self.current is None:
			self.current = self.session.open(AirPlayPhoto)
			
		if self.current.__class__.__name__ != "AirPlayPhoto":
			print("[SIFTeam OpenAirPlay] is it busy with other contents?")
			return
			
		self.current.load(data)
		
	def __audioClosed(self):
		if self.videorequest:
			self.current = self.session.open(AirPlayVideo)
			self.current.open(self.videourl)
			self.videorequest = False
		
	def __audio(self):
		if self.current is None:
			self.current = self.session.openWithCallback(self.__audioClosed, AirPlayAudio)
		
	def __video(self, url, startposition):
		if self.current is None:
			self.current = self.session.open(AirPlayVideo)
			
		if self.current.__class__.__name__ != "AirPlayVideo":
			# if audio we replace it
			if self.current.__class__.__name__ == "AirPlayAudio":
				self.videourl = url
				self.videorequest = True
				self.current.exit()
				return
			else:
				print("[SIFTeam OpenAirPlay] is it busy with other contents?")
				return
			
		self.current.open(url)
		
	def __videoPlay(self):
		if self.current is not None and self.current.__class__.__name__ == "AirPlayVideo":
			self.current.play()
		
	def __videoPause(self):
		if self.current is not None and self.current.__class__.__name__ == "AirPlayVideo":
			self.current.pause()
		
	def __videoGetPosition(self):
		if self.current is not None and self.current.__class__.__name__ == "AirPlayVideo":
			return self.current.getPosition()
			
		return None
	
	def __videoSetPosition(self, position):
		if self.current is not None and self.current.__class__.__name__ == "AirPlayVideo":
			self.current.setPosition(position)
	
	def __close(self):
		if self.current is not None:
			self.current.exit()
			self.current = None
			self.videorequest = False
	
	def __closeAudio(self):
		if self.current is not None and self.current.__class__.__name__ == "AirPlayAudio":
			self.current.exit()
			self.current = None
		