# -*- coding: utf-8 -*-
import requests
import json
import time
import os
from os.path import expanduser
if os.name == 'posix':
    import notify2
# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

firststart = True

dictionary = dict()
gameDict = dict()
userDict = dict()

headers = {'Client-ID' : 'og1crpd047s8mo4ocshg1yf93x5ak3n'}

def printsummary(json):
    message = ''
    for channel in json:
        message += " {0:20}     {1:6}\n    {2}\n\n".format(channel['user_id'],str(channel['viewer_count']),getGameName(channel['game_id']))
    message = message[:-2]
    showmessage(message)

def showmessage(message):
    if os.name == 'posix':
        notify2.init('Streams Online')
        n = notify2.Notification("Streams:",message,"notification-message-im")
        n.show()

def loadFromFile():
    streamfile = open(expanduser("~")+"/.config/.pychecker/streams")
    channels = streamfile.read().replace("\n","").split(",")
    return channels

def getToken():
    link = "https://id.twitch.itv/oauth2/authorize?client_id=hb7zvth15ub915hs3qw0h5c6xab0a1&redirect_uri=http://localhost&response_type=token&scope=analytics:read:games"
    s = requests.get(link)
    return s.text

def getUserID():
    link = "https://api.twitch.tv/helix/users?login=Fozruk_"
    s = requests.get(link,headers=headers)
    json2 = json.loads(s.text)
    return json2["data"][0]["id"]

#TODO pagination
def getFollowedStreams(userID):
    link = 'https://api.twitch.tv/helix/users/follows?first=100&from_id=%s' % userID
    s = requests.get(link,headers=headers)
    return json.loads(s.text)

def getStreamIDs(followedStreamsResponse):
    return '&user_id='.join(map(lambda x: x['to_id'], followedStreamsResponse['data']))

def getStreamUserIDs(streamsResponse):
    return '&id='.join(map(lambda x: x['user_id'], streamsResponse))

def getGameIDs(streamsResponse):
    return '&id='.join(map(lambda x: x['game_id'], streamsResponse))

def getStreams():
    link = "https://api.twitch.tv/helix/streams?first=100&user_id=%s" % getStreamIDs(getFollowedStreams(userID))
    s = requests.get(link,headers=headers)
    return json.loads(s.text)

def downloadjson(channellist):
    link = 'https://api.twitch.tv/kraken/streams/?channel=%s' % ','.join(channels)
    #print "Connect to %s" % link
    s = requests.get(link,headers=headers)
    return json.loads(s.text)

def fillUserDict(userlist):
    global userDict
    userDict = dict(map(lambda x: (x['id'],x['display_name']),userlist['data']))

def fillGameDict(gamelist):
    global gameDict
    gameDict = dict(map(lambda x: (x['id'],x['name']),gamelist))

def showList():
    json = downloadjson(channels)
    printsummary(json)

def fetchGameNames(gameIDs):
    link = "https://api.twitch.tv/helix/games?id=%s" % gameIDs
    s = requests.get(link,headers=headers)
    return json.loads(s.text)['data']

def fetchUserNames(listOfUserIds):
    link = "https://api.twitch.tv/helix/users?id=%s" % listOfUserIds
    s = requests.get(link,headers=headers)
    return json.loads(s.text)['data']

def startMainLoop():
    while True:
        parsedJson = getStreams()['data']
        global firststart
        if firststart == True:
            #print "First"
            printsummary(parsedJson)
            firststart = False

        onlineoffline = ''
        #print "Else"
        for channel in dictionary.keys():
            found = False
            dictionary[channel]['urlname'] = channel
            #print channel
            for listchannel in parsedJson['streams']:
                #print channel,'=',listchannel['channel']['name']
                if listchannel['channel']['name'] == channel:
                    #print "Channel Found %s , State in dict: %s" % (channel,dictionary[channel])
                    #https://stackoverflow.com/questions/5618878/how-to-convert-list-to-string
                    found = True
                    foundchannel = dictionary[channel]

                    topic = listchannel['channel']['status']
                    game = listchannel['channel']['game']
                    name = listchannel['channel']['display_name']
                    viewers = listchannel['viewers']

                    foundchannel['topic'] = topic
                    foundchannel['game'] = game
                    foundchannel['name'] = name
                    foundchannel['viewers'] = viewers

                    if foundchannel['online'] == False:
                        onlineoffline +=  "  %s \n" % listchannel['channel']['display_name']
                        dictionary[channel]['online'] = True
            #print "ended iteration, %s, %s, %s" % (found,dictionary[channel],channel)
            if found == False and dictionary[channel]['online'] == True:
                onlineoffline +=  "  %s \n" % listchannel['channel']['display_name']
                dictionary[channel] = False
                dictionary[channel]['topic'] = ''
                dictionary[channel]['game'] = ''
        if(len(onlineoffline) > 0):
            showmessage(onlineoffline)
        time.sleep(60)


userID = getUserID()
channels = getFollowedStreams(userID)

for channelname in channels:
    dictionary[channelname] = {'name' : channelname, 'online' : False , "viewers" : 0 , 'topic' : '' , 'game' : '', 'urlname' : ''}

startMainLoop()
