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

from twisted.web import server, resource, http, client
from twisted.internet import reactor
from M2Crypto import RSA, X509
from datetime import datetime
from io import BytesIO
from biplist import readPlist, InvalidPlistException, NotBinaryPlistException

import os
import sys
import uuid
import avahi
import dbus
import platform
import base64
import subprocess
import StringIO
import urlparse
import socket

AIRPLAY_PORT = 22555
AIRTUNES_PORT = 22556
HAIRTUNES_BINARY = "/usr/bin/hairtunes"
AIRPLAY_BANNER = "SIFTeam AirPlay on "
AIRPORT_PRIVATE_KEY = \
"-----BEGIN RSA PRIVATE KEY-----\n" \
"MIIEpQIBAAKCAQEA59dE8qLieItsH1WgjrcFRKj6eUWqi+bGLOX1HL3U3GhC/j0Qg90u3sG/1CUt\n" \
"wC5vOYvfDmFI6oSFXi5ELabWJmT2dKHzBJKa3k9ok+8t9ucRqMd6DZHJ2YCCLlDRKSKv6kDqnw4U\n" \
"wPdpOMXziC/AMj3Z/lUVX1G7WSHCAWKf1zNS1eLvqr+boEjXuBOitnZ/bDzPHrTOZz0Dew0uowxf\n" \
"/+sG+NCK3eQJVxqcaJ/vEHKIVd2M+5qL71yJQ+87X6oV3eaYvt3zWZYD6z5vYTcrtij2VZ9Zmni/\n" \
"UAaHqn9JdsBWLUEpVviYnhimNVvYFZeCXg/IdTQ+x4IRdiXNv5hEewIDAQABAoIBAQDl8Axy9XfW\n" \
"BLmkzkEiqoSwF0PsmVrPzH9KsnwLGH+QZlvjWd8SWYGN7u1507HvhF5N3drJoVU3O14nDY4TFQAa\n" \
"LlJ9VM35AApXaLyY1ERrN7u9ALKd2LUwYhM7Km539O4yUFYikE2nIPscEsA5ltpxOgUGCY7b7ez5\n" \
"NtD6nL1ZKauw7aNXmVAvmJTcuPxWmoktF3gDJKK2wxZuNGcJE0uFQEG4Z3BrWP7yoNuSK3dii2jm\n" \
"lpPHr0O/KnPQtzI3eguhe0TwUem/eYSdyzMyVx/YpwkzwtYL3sR5k0o9rKQLtvLzfAqdBxBurciz\n" \
"aaA/L0HIgAmOit1GJA2saMxTVPNhAoGBAPfgv1oeZxgxmotiCcMXFEQEWflzhWYTsXrhUIuz5jFu\n" \
"a39GLS99ZEErhLdrwj8rDDViRVJ5skOp9zFvlYAHs0xh92ji1E7V/ysnKBfsMrPkk5KSKPrnjndM\n" \
"oPdevWnVkgJ5jxFuNgxkOLMuG9i53B4yMvDTCRiIPMQ++N2iLDaRAoGBAO9v//mU8eVkQaoANf0Z\n" \
"oMjW8CN4xwWA2cSEIHkd9AfFkftuv8oyLDCG3ZAf0vrhrrtkrfa7ef+AUb69DNggq4mHQAYBp7L+\n" \
"k5DKzJrKuO0r+R0YbY9pZD1+/g9dVt91d6LQNepUE/yY2PP5CNoFmjedpLHMOPFdVgqDzDFxU8hL\n" \
"AoGBANDrr7xAJbqBjHVwIzQ4To9pb4BNeqDndk5Qe7fT3+/H1njGaC0/rXE0Qb7q5ySgnsCb3DvA\n" \
"cJyRM9SJ7OKlGt0FMSdJD5KG0XPIpAVNwgpXXH5MDJg09KHeh0kXo+QA6viFBi21y340NonnEfdf\n" \
"54PX4ZGS/Xac1UK+pLkBB+zRAoGAf0AY3H3qKS2lMEI4bzEFoHeK3G895pDaK3TFBVmD7fV0Zhov\n" \
"17fegFPMwOII8MisYm9ZfT2Z0s5Ro3s5rkt+nvLAdfC/PYPKzTLalpGSwomSNYJcB9HNMlmhkGzc\n" \
"1JnLYT4iyUyx6pcZBmCd8bD0iwY/FzcgNDaUmbX9+XDvRA0CgYEAkE7pIPlE71qvfJQgoA9em0gI\n" \
"LAuE4Pu13aKiJnfft7hIjbK+5kyb3TysZvoyDnb3HOKvInK7vXbKuU4ISgxB2bB3HcYzQMGsz1qJ\n" \
"2gG0N5hvJpzwwhbhXqFKA4zaaSrw622wDniAK5MlIE0tIAKKP4yxNGjoD2QYjhBGuhvkWKY=\n" \
"-----END RSA PRIVATE KEY-----"

SERVER_INFO_TEMPLATE = '<?xml version="1.0" encoding="UTF-8"?>\
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\
<plist version="1.0">\
<dict>\
<key>deviceid</key>\
<string>%s</string>\
<key>features</key>\
<integer>%d</integer>\
<key>model</key>\
<string>%s</string>\
<key>protovers</key>\
<string>1.0</string>\
<key>srcvers</key>\
<string>101.10</string>\
</dict>\
</plist>'

PLAYBACK_INFO_TEMPLATE = '<?xml version="1.0" encoding="UTF-8"?>\
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\
<plist version="1.0">\
<dict>\
<key>duration</key>\
<real>%f</real>\
<key>loadedTimeRanges</key>\
<array>\
    <dict>\
        <key>duration</key>\
        <real>%f</real>\
        <key>start</key>\
        <real>%f</real>\
    </dict>\
</array>\
<key>playbackBufferEmpty</key>\
<true/>\
<key>playbackBufferFull</key>\
<false/>\
<key>playbackLikelyToKeepUp</key>\
<true/>\
<key>position</key>\
<real>%f</real>\
<key>rate</key>\
<real>%d</real>\
<key>readyToPlay</key>\
<true/>\
<key>seekableTimeRanges</key>\
<array>\
    <dict>\
        <key>duration</key>\
        <real>%f</real>\
        <key>start</key>\
        <real>0.0</real>\
    </dict>\
</array>\
</dict>\
</plist>'

PLAYBACK_INFO_NOT_READY_TEMPLATE = '<?xml version="1.0" encoding="UTF-8"?>\
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\
<plist version="1.0">\
<dict>\
<key>readyToPlay</key>\
<false/>\
</dict>\
</plist>'


class APZeroConf():
	def __init__(self, info):
		self.info = info
		self.group = None

	def publish(self):
		text_ap = ["deviceid=" + self.info.deviceid, "features=" + hex(self.info.features), "model=" + self.info.model]
		text_at = ["tp=UDP", "sm=false", "sv=false", "ek=1", "et=0,1", "cn=0,1", "ch=2", "ss=16", "sr=44100", "pw=false", "vn=3", "txtvers=1"]
		bus = dbus.SystemBus()
		server = dbus.Interface(bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER), avahi.DBUS_INTERFACE_SERVER)

		self.group = dbus.Interface(bus.get_object(avahi.DBUS_NAME, server.EntryGroupNew()), avahi.DBUS_INTERFACE_ENTRY_GROUP)
		self.group.AddService(
			avahi.IF_UNSPEC,
			avahi.PROTO_UNSPEC,
			dbus.UInt32(0),
			AIRPLAY_BANNER + platform.node(),
			"_airplay._tcp",
			"",
			"",
			dbus.UInt16(AIRPLAY_PORT),
			avahi.string_array_to_txt_array(text_ap)
		)
		self.group.AddService(
			avahi.IF_UNSPEC,
			avahi.PROTO_UNSPEC,
			dbus.UInt32(0),
			self.info.deviceid + "@" + AIRPLAY_BANNER + platform.node(),
			"_raop._tcp",
			"",
			"",
			dbus.UInt16(AIRTUNES_PORT),
			avahi.string_array_to_txt_array(text_at)
		)
		self.group.Commit()

	def unpublish(self):
		if self.group is not None:
			self.group.Reset()


class RTSPRequest(http.Request):
	def process(self):
		self.channel.site.resource.render(self)


class RTSPChannel(http.HTTPChannel):
	requestFactory = RTSPRequest

	def checkPersistence(self, request, version):
		if version == "RTSP/1.0":
			return 1
		return 0


class RTSPSite(server.Site):
	protocol = RTSPChannel
	requestFactory = RTSPRequest


class APInfo():
	def __init__(self):
		self.deviceid = "%012X" % uuid.getnode()
		self.features = 0x77
		self.model = "AppleTV2,1"


class APRtspRoot(resource.Resource):
	isLeaf = True

	def __init__(self, callbacks, info):
		resource.Resource.__init__(self)
		self.callbacks = callbacks
		self.info = info
		self.aesiv = None
		self.rsaaeskey = None
		self.fmtp = None
		self.process = None

	def dump(self, data):
		dmp = ""
		for ch in data:
			dmp += "0x%x " % ord(ch)

		dmp = dmp.strip()
		print dmp

	def prepareBaseReply(self, request):
		request.setETag("RTSP/1.0")
		request.setResponseCode(200)
		request.setHeader("cseq", request.received_headers["cseq"])
		request.setHeader("audio-jack-status", "connected; type=analog")

		if "apple-challenge" in request.received_headers:
			challenge = request.received_headers["apple-challenge"]
			if challenge[-2:] != "==":
				challenge += "=="

			data = base64.b64decode(challenge)

			host = request.getHost().host

			if (host.split(".")) == 4:	# ipv4
				data += socket.inet_pton(socket.AF_INET, host)
			elif host[:7] == "::ffff:":
				data += socket.inet_pton(socket.AF_INET, host[7:])
			else:
				data += socket.inet_pton(socket.AF_INET6, host.split("%")[0])

			hwaddr = self.info.deviceid
			for i in range(0, 12, 2):
				data += chr(int(hwaddr[i:i + 2], 16))

			data = data.ljust(32, '\0')
			#self.dump(data)

			key = RSA.load_key_string(AIRPORT_PRIVATE_KEY)
			signature = base64.b64encode(key.private_encrypt(data, RSA.pkcs1_padding))
			if signature[-2:] == "==":
				signature = signature[:-2]
			request.setHeader("apple-response", signature)

	def render_OPTIONS(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)

		self.prepareBaseReply(request)
		request.setHeader("public", "ANNOUNCE, SETUP, RECORD, PAUSE, FLUSH, TEARDOWN, OPTIONS, GET_PARAMETER, SET_PARAMETER")
		request.write("")
		request.finish()

	def render_ANNOUNCE(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)

		self.prepareBaseReply(request)

		content = request.content.read()
		for row in content.split("\n"):
			row = row.strip()
			if row[:2] != "a=":
				continue

			row = row[2:]
			seppos = row.find(":")
			key = row[:seppos].strip()
			value = row[seppos + 1:].strip()

			if key == "aesiv" or key == "rsaaeskey":
				if value[-2:] != "==":
					value += "=="

			if key == "aesiv":
				self.aesiv = base64.b64decode(value)
			elif key == "rsaaeskey":
				self.rsaaeskey = base64.b64decode(value)
				key = RSA.load_key_string(AIRPORT_PRIVATE_KEY)
				self.rsaaeskey = key.private_decrypt(self.rsaaeskey, RSA.pkcs1_oaep_padding)
			elif key == "fmtp":
				self.fmtp = value

		request.write("")
		request.finish()

	def render_SETUP(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)

		self.prepareBaseReply(request)

		if self.aesiv is not None and self.rsaaeskey is not None and self.fmtp is not None and "transport" in request.received_headers:
			data_port = 0
			timing_port = 59010
			control_port = 59012
			for row in request.received_headers["transport"].split(";"):
				row = row.strip()
				seppos = row.find("=")
				if seppos == -1:
					continue

				key = row[:seppos].strip()
				value = row[seppos + 1:].strip()

				if key == "timing_port":
					timing_port = int(value)
				elif key == "control_port":
					control_port = int(value)

			aesiv = ""
			for ch in self.aesiv:
				aesiv += "%02X" % ord(ch)

			rsaaeskey = ""
			for ch in self.rsaaeskey:
				rsaaeskey += "%02X" % ord(ch)

			args = [
				HAIRTUNES_BINARY,
				"iv", aesiv,
				"key", rsaaeskey,
				"fmtp", self.fmtp,
				"cport", str(control_port),
				"tport", str(timing_port),
				"dport", "0"
			]
			self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			while self.process.poll() == None:
				buff = self.process.stdout.readline()
				if len(buff) > 0:
					if buff[:6] == "port: ":
						data_port = int(buff[6:])
						break

			if data_port != 0:
				self.callbacks.audio()
				request.setHeader("transport", request.received_headers["transport"] + ";server_port=" + str(data_port))
				request.setHeader("session", "DEADBEEF")
		request.write("")
		request.finish()

	def render_RECORD(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)
		self.prepareBaseReply(request)
		request.write("")
		request.finish()

	def render_FLUSH(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)

		if self.process is not None and self.process.poll() is None:
			self.process.stdin.write("flush\n")

		self.prepareBaseReply(request)
		request.write("")
		request.finish()

	def render_TEARDOWN(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)

		if self.process != None and self.process.poll() == None:
			self.process.stdin.write("exit\n")
			self.process.wait()
		self.process = None

		self.callbacks.stopAudio()

		self.prepareBaseReply(request)
		request.setHeader("connection", "close")
		request.write("")
		request.finish()

	def render_SET_PARAMETER(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)
		buff = request.content.read().split("\n")
		for row in buff:
			if row[:7] == "volume:":
				volume = row[7:].strip()
				if self.process is not None and self.process.poll() is None:
					self.process.stdin.write("vol: " + volume + "\n")
		self.prepareBaseReply(request)
		request.write("")
		request.finish()

	def render_GET_PARAMETER(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)
		self.prepareBaseReply(request)
		request.write("")
		request.finish()

	def render_DENIED(self, request):
		print "[SIFTeam OpenAirPlay] " + str(request)
		self.prepareBaseReply(request)
		request.write("")
		request.finish()


class APWebRoot(resource.Resource):
	isLeaf = False

	def __init__(self, callbacks, info):
		resource.Resource.__init__(self)
		self.callbacks = callbacks
		self.info = info

	def getChild(self, path, request):
		print "[SIFTeam OpenAirPlay] " + str(request)
		if path == "server-info":
			return APWebServerInfo(self.callbacks, self.info)
		elif path == "reverse":
			return APWebReverse(self.callbacks, self.info)
		elif path == "stop":
			return APWebStop(self.callbacks, self.info)
		elif path == "photo":
			return APWebPhoto(self.callbacks, self.info)
		elif path == "slideshow-features":
			return APWebSlideShowFeatures(self.callbacks, self.info)
		elif path == "play":
			return APWebPlay(self.callbacks, self.info)
		elif path == "rate":
			return APWebRate(self.callbacks, self.info)
		elif path == "scrub":
			return APWebScrub(self.callbacks, self.info)
		elif path == "playback-info":
			return APWebPlaybackInfo(self.callbacks, self.info)
		elif path == "setProperty":
			return APWebSetProperty(self.callbacks, self.info)
		elif path == "getProperty":
			return APWebGetProperty(self.callbacks, self.info)

		print "[SIFTeam OpenAirPlay] the api '%s' is not yet implemented" % path
		return APWebNotFound(self.callbacks, self.info)


class APWebBase(resource.Resource):
	isLeaf = True

	def __init__(self, callbacks, info):
		resource.Resource.__init__(self)
		self.callbacks = callbacks
		self.info = info

	def getDateTime(self):
		return datetime.now().strftime("%a, %d %b %Y %H:%M:%S") + " GMT"

	def commonRender(self, request, body="", retcode=200):
		request.setResponseCode(retcode)
		if retcode == 101:
			request.setHeader("upgrade", "PTTH/1.0")
			request.setHeader("connection", "Upgrade")

		request.setHeader("content-length", len(body))
		request.setHeader("date", self.getDateTime())
		request.write(body)
		request.finish()


class APWebNotFound(APWebBase):
	def render(self, request):
		self.commonRender(request, "", 404)
		return server.NOT_DONE_YET


class APWebReverse(APWebBase):
	def render(self, request):
		self.commonRender(request, "", 101)
		return server.NOT_DONE_YET


class APWebSlideShowFeatures(APWebBase):
	def render(self, request):
		# ?? UNKNOW!
		self.commonRender(request)
		return server.NOT_DONE_YET


class APWebServerInfo(APWebBase):
	def render(self, request):
		request.setHeader("content-type", "text/x-apple-plist+xml")
		self.commonRender(request, SERVER_INFO_TEMPLATE % (self.info.deviceid, self.info.features, self.info.model))
		return server.NOT_DONE_YET


class APWebStop(APWebBase):
	def render(self, request):
		self.callbacks.stop()
		self.commonRender(request)
		return server.NOT_DONE_YET


class APWebPhoto(APWebBase):
	def render(self, request):
		request.setResponseCode(200)
		buff = request.content.read()
		self.callbacks.photo(buff)
		self.commonRender(request)
		return server.NOT_DONE_YET


class APWebPlay(APWebBase):
	def render(self, request):
		request.setResponseCode(200)
		content = request.content.read()

		url = ""
		tmp = StringIO.StringIO()
		tmp.write(content)
		# TODO: check for content type 'application/x-apple-binary-plist'
		try:
			plist = readPlist(tmp)
			url = plist["Content-Location"]
			startposition = float(plist["Start-Position"])
		except (InvalidPlistException, NotBinaryPlistException), e:
			startposition = 0.0
			for row in content.split("\n"):
				row = row.strip()
				seppos = row.find(":")
				key = row[:seppos].strip()
				value = row[seppos + 1:].strip()
				if key == "Content-Location":
					url = value
				elif key == "Start-Position":
					startposition = float(value)

		if url != "":
			self.callbacks.video(url, startposition)

		self.commonRender(request)
		return server.NOT_DONE_YET


class APWebRate(APWebBase):
	def render(self, request):
		if 'value' in request.args:
			if float(request.args['value'][0]):
				self.callbacks.videoPlay()
			else:
				self.callbacks.videoPause()

		self.commonRender(request)
		return server.NOT_DONE_YET


class APWebScrub(APWebBase):
	def render_GET(self, request):
		position = self.callbacks.videoGetPosition()
		if position is not None:
			body = "duration: %f\r\nposition: %f\r\n" % (position["duration"], position["position"])
		else:
			body = "duration: 0.0\r\nposition: 0.0\r\n"
		self.commonRender(request, body)
		return server.NOT_DONE_YET

	def render_POST(self, request):
		if "position" in request.args:
			self.callbacks.videoSetPosition(float(request.args["position"][0]))
		self.commonRender(request)
		return server.NOT_DONE_YET


class APWebPlaybackInfo(APWebBase):
	def render(self, request):
		info = self.callbacks.videoGetPosition()
		if info["duration"] == 0 or info["position"] == info["duration"]:
			body = PLAYBACK_INFO_NOT_READY_TEMPLATE
		else:
			body = PLAYBACK_INFO_TEMPLATE % (info["duration"], info["loaded"], info["position"], info["position"], int(not info["paused"]), info["duration"])

		request.setHeader("content-type", "text/x-apple-plist+xml")
		self.commonRender(request, body)
		return server.NOT_DONE_YET


class APWebSetProperty(APWebBase):
	def render(self, request):
		self.commonRender(request)
		return server.NOT_DONE_YET


class APWebGetProperty(APWebBase):
	def render(self, request):
		self.commonRender(request)
		return server.NOT_DONE_YET


class APCallbacks():
	def __init__(self):
		self.photo = None
		self.audio = None
		self.video = None
		self.videoPlay = None
		self.videoPause = None
		self.videoGetPosition = None
		self.videoSetPosition = None
		self.stop = None
		self.stopAudio = None


class APServer():
	def __init__(self, apcb):
		self.atconn = None
		self.apconn = None

		self.apcb = apcb
		self.apinfo = APInfo()
		self.zeroconf = APZeroConf(self.apinfo)

		self.atroot = APRtspRoot(self.apcb, self.apinfo)
		self.aproot = APWebRoot(self.apcb, self.apinfo)
		self.atsite = RTSPSite(self.atroot)
		self.apsite = server.Site(self.aproot)

	def start(self):
		self.zeroconf.publish()
		try:
			self.atconn = reactor.listenTCP(AIRTUNES_PORT, self.atsite, interface="::")
		except Exception:
			print "[SIFTeam OpenAirPlay] cannot bind airtunes server on ipv6 interface"
			self.atconn = None

		if self.atconn is None:
			try:
				self.atconn = reactor.listenTCP(AIRTUNES_PORT, self.atsite)
			except Exception:
				self.atconn = None
				self.apconn = None
				print "[SIFTeam OpenAirPlay] cannot start airtunes server"
				return

		try:
			self.apconn = reactor.listenTCP(AIRPLAY_PORT, self.apsite, interface="::")
		except Exception:
			print "[SIFTeam OpenAirPlay] cannot bind airplay server on ipv6 interface"
			self.apconn = None

		if self.apconn is None:
			try:
				self.apconn = reactor.listenTCP(AIRPLAY_PORT, self.apsite)
			except Exception:
				self.atconn.stopListening()
				self.atconn = None
				self.apconn = None
				print "[SIFTeam OpenAirPlay] cannot start airplay server"
				return

		print "[SIFTeam OpenAirPlay] server started"

	def stop(self):
		self.zeroconf.unpublish()
		if self.atconn is not None:
			self.atconn.stopListening()
		if self.apconn is not None:
			self.apconn.stopListening()
		print "[SIFTeam OpenAirPlay] server stopped"
