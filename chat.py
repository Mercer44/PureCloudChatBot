from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.chrome.options import Options
from gaap import GAAP
from requests import Request
import configparser
import contextlib

chrome_options = Options()  
chrome_options.add_argument("headless") 
chrome_options.add_argument('window-size=1200x600')
c = webdriver.Chrome(chrome_options=chrome_options)
delay=5
timeout=12
agentName="Agent Two"
username=""
userpass=""
gaapAuthToken=""
gaapBaseUrl=""
gaapSiteId=0
wait=WebDriverWait(c, timeout)
errorCount=100

def readSettings():
	global username
	global userpass
	global gaapAuthToken
	global gaapBaseUrl
	global gaapSiteId

	conf = configparser.ConfigParser()
	conf.read('service.conf')
	username = conf.get('purecloud','useremail')
	userpass = conf.get('purecloud','userpass')
	gaapAuthToken = conf.get('gaap','authtoken')
	gaapBaseUrl = conf.get('gaap','baseurl')
	gaapSiteId = conf.get('gaap','siteid')
	print('read config')

def loadBrowser():
	c.get("https://apps.mypurecloud.com")

def waitUntil(selector):
	wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,selector)))
	sleep(.1)

def waitUntilInvisible(selector):
	global errorCount
	try:
		wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR,selector)))
		sleep(.1)
	except:
		errorCount=errorCount-1
		print('failed to wait for invisible: ' + selector)

def login():
	waitUntil('#email')
	print('Signing in: ' + username)
	c.find_element_by_id("email").send_keys(username)

	c.find_element_by_id("password").send_keys(userpass)

	c.find_element_by_class_name("btn-login").click()
	sleep(timeout)

def onqueue():
	#onqueue
	waitUntil('.toggle-switch-container')
	goBackOnQueue()

def isNew():
	try:
		ans = c.find_element_by_css_selector(".answer-interaction")
		return ans.is_displayed()
	except:
		return False

def answer():
	global errorCount
	try:
		c.find_element_by_css_selector(".answer-interaction").click()
	except:
		errorCount=errorCount-1
		print('failed to answer interaction')

def respond(message):
	currentInteractionInput = c.find_elements_by_css_selector("textarea.message-input")[1]
	currentInteractionInput.send_keys(message)
	currentInteractionInput.send_keys(Keys.RETURN)
	print('replied ' + message)

def getNotificationText():
	try:
		return c.find_element_by_css_selector(".notification-text").text
	except:
		return ""

def goBackOnQueue():
	try:
		print('going on queue')
		sleep(2)
		c.find_element_by_css_selector(".on-queue-inactive").click()
		sleep(2)
		c.find_element_by_css_selector(".select-phone-message .messenger-actions span:nth-child(2)").click()
	except:
		print("should already be on queue")
		try:
			c.find_element_by_css_selector(".not-responding-message .messenger-actions span:nth-child(1)").click()
		except:
			print("failed to reactivate queue")
		
	

def isFirstMessage():
	try:
		#should fail to find anything
		messagePane = c.find_element_by_css_selector(".chat-messages .chat-message")
		return False
	except:
		return True

def newestMessage():
	try:
		messagePane = c.find_element_by_css_selector(".chat-messages .chat-message:last-child")
		user = messagePane.find_element_by_css_selector(".user-name").text
		print('newest message by: ' + str(user))
		return str(user).strip() != agentName
	except:
		return False

def getParticipantName():
	try:
		partName = c.find_element_by_css_selector(".participant-name").text
		name=str(partName).splitlines()[0].strip()
		return name
	except:
		return ''

def getSenderName():
	try:
		partName = c.find_element_by_css_selector(".participant-name").text
		name=str(partName).splitlines()[0].strip()
		return name
	except:
		return ''

def getLastMessage():
	messagePane = c.find_element_by_css_selector(".chat-messages .chat-message:last-child")
	message = messagePane.find_element_by_css_selector(".message-container").text
	print(str(message).strip())
	return str(message).strip()

def replyGaap(resp):
	global errorCount
	try:
		mes = resp.json()
		print(mes)
		for m in mes['messages']:
			respond(m['text'])
			sleep(1)
		if(mes['is_call_ended']):
			endChatAgent()
		
	except:
		print('failed to replyGaap')
		errorCount=errorCount-1

def isChatEnded():
	try:
		return c.find_element_by_css_selector(".done-btn.enabled").is_displayed()
	except:
		return False

def endChat():
	waitUntil('.done-btn.enabled')
	c.find_element_by_css_selector(".done-btn.enabled").click()
	sleep(2)


def endChatAgent():
	waitUntil('.pc-chat-off')
	c.find_element_by_css_selector(".pc-chat-off").click()
	endChat()

def needToSwitchChats(element):
	global errorCount
	try:
		try:
			element.find_element_by_css_selector(".interaction-state-chat-indicator.agent-waiting")
			return False
		except:
			element.find_element_by_css_selector(".interaction-state-chat-indicator.customer-waiting")
			return True
	except:
		print('failed to determine is switch chat needed')
		errorCount=errorCount-1
		return False

def sendFirstMessage(name):
	glist[partName] = GAAP(gaapBaseUrl,gaapAuthToken,gaapSiteId)
	st = glist[partName].sendStart(partName)
	replyGaap(st)

readSettings()
loadBrowser()
login()
onqueue()

roundCount=0
chatCount=0
glist={}

while True:
	sleep(.5)
	if "Not Responding" in getNotificationText():
		goBackOnQueue()

	currChats = c.find_elements_by_css_selector(".acd-interaction-card .interaction-card-wrapper")
	for index, i in enumerate(currChats):
		if len(currChats) > 1 and needToSwitchChats(i):
			i.click()
			sleep(2)

		partName = getParticipantName()
		if isNew():
			answer()
			chatCount=chatCount+1
			print('answering chat: ' + str(chatCount) + ' with ' + partName)
		elif isFirstMessage():
			sendFirstMessage(partName)
		elif newestMessage():
			print(partName + " said: " + getLastMessage())
			if partName not in glist:
				sendFirstMessage(partName)
			else:
				rep = glist[partName].sendMessage(getLastMessage())
				replyGaap(rep)
		elif isChatEnded():
			endChat()
			glist[partName].sendEnd()
			del glist[partName]
			print('finished chat with: ' + partName + ' chat#: ' + str(chatCount))
	if errorCount < 0:
		print('too many errors, shutting down')
		c.close()
		exit()

