import uuid
from requests import Request, Session
import json
import datetime

class GAAP():

	def __init__(self, baseUrl, auth, site):
		self.sessionId=''
		self.newurl=baseUrl+'/fish-messaging/CBPStart.jsp'
		self.msgurl=baseUrl+'/fish-messaging/CBPStep.jsp'
		self.siteID = site
		self.authToken = auth
		self.s=Session()
	

	def getCurrentDT(self):
		return str(datetime.datetime.now().isoformat())[:23]+'Z'

	def getID(self):
		return str(uuid.uuid1())

	def createStart(self, name):
		newID = self.getID()
		self.sessionId="purecloud.com"+newID
		startbody={
			"auth_token": self.authToken,
			"site_id": self.siteID,
			"is_test_call": True,
			"cli": "12347942080",
			"dnis": "8908",
			"full_session_id": newID,
			"session_id": self.sessionId,
			"channel": "FACEBOOK_MESSENGER",
			"attached_data": {
				"name": name
			}
		}
		return startbody

	def createMsg(self,userMessage):
		msgbody={
			'channel': 'FACEBOOK_MESSENGER',
			'event_details': {
				'event_timestamp': self.getCurrentDT()
				},
			'event_type': 'MessageRecieved',
			'session_id': self.sessionId,
			'message_text': userMessage
		}
		return msgbody

	def createEnd(self):
		endbody={
			'channel': 'FACEBOOK_MESSENGER',
			'event_details': {
				'event_timestamp': self.getCurrentDT()
			},
			'event_type': 'Hangup',
			'session_id': self.sessionId
		}
		return endbody

	def sendStart(self,username):
		r=self.s.post(self.newurl, json.dumps(self.createStart(username)))
		return r

	def sendMessage(self,userMessage):
		r=self.s.post(self.msgurl, json.dumps(self.createMsg(userMessage)))
		return r

	def sendEnd(self):
		r=self.s.post(self.msgurl, json.dumps(self.createEnd()))
		return r

