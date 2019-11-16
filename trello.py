import os
import sys
'''
SECRETS:
 1. API_KEY
 2. TOKEN
'''

API_KEY = ""
TOKEN = ""

#Load secrets.
f = open("secrets.txt", 'r')
secrets = f.readlines()
API_KEY = secrets[0].strip('\n')
TOKEN = secrets[1].strip('\n')
f.close()

#Load board id
f = open("boardID.txt", 'r')
work_break_id = f.readlines()[0].strip('\n')
f.close()

import argparse as ap
import requests
import json



BASE_API = "https://api.trello.com/1/"
AUTH = "key=" + API_KEY + "&token=" + TOKEN


###############################################################################
# JSON Helper
###############################################################################

def dumpJson(jsonData):
    with open("trello.txt", 'w') as f:
        json.dump(jsonData, f)

###############################################################################
# Trello Helper
###############################################################################

def getBoard(boardId):
    url = BASE_API + "boards/" + boardId + "?fields=all&" + AUTH
    response = requests.get(url)
    return json.loads(response.text)

def getBoardLists(boardId):
    url = BASE_API + "boards/" + boardId + "?fields=name&lists=all&list_fields=all&" + AUTH
    response = requests.get(url)
    return json.loads(response.text)

def getListId(listName):
    jsonData = getBoardLists(work_break_id)
    jsonLists = jsonData["lists"]
    for trelloList in jsonLists:
        closed = trelloList["closed"]
        name = trelloList["name"]
        #Ignore archive lists.
        if not closed:
            if listName in name:
                return trelloList["id"]
    raise Exception("Could not find list with name: " + listName)

def getListCards(listId):
    url = BASE_API + "lists/" + listId + "/cards?" + AUTH
    response = requests.get(url)
    return json.loads(response.text)


def archiveListCards(listName):
    listId = getListId(listName)
    queryString = {
        "key": API_KEY,
        "token": TOKEN
        }    
    url = BASE_API + "lists/" + listId + "/archiveAllCards"
    response = requests.request("POST", url, params=queryString)
    return json.loads(response.text)
    

def deleteListCards(listName):
    queryString = {
        "key": API_KEY,
        "token": TOKEN
        }        
    listId = getListId(listName)
    listCards = getListCards(listId)
    for card in listCards:
        cardId = card["id"]
        url = BASE_API + "cards/" + cardId
        response = requests.request("DELETE", url, params=queryString)
        

###############################################################################
# Commands.
###############################################################################

'''
Run this command when the sprint is completed
 - Generates a report of all tickets completed during the sprint.
'''
def completeSprint():
    sprintFile = open("sprint-complete.txt", 'w')
    sprintFile.write("Completed Sprint details:\n\n")

    listId = getListId("DONE")
    listCards = getListCards(listId)
    details = cardDetails(listCards)
    statusBucket = {}
    epicCount = 0
    for d in details:
        sprintFile.write("  > " + d["name"] + " - " + d["status"] + "\n")

        # Count ticket status for summary.
        dStat = d["status"]
        if dStat not in statusBucket:
            statusBucket[dStat] = 1
        else:
            statusBucket[dStat] += 1

        # Count epics for summary.
        if d["epic"]:
            epicCount += 1
            
    sprintFile.write("\nEpics:" + str(epicCount) + ", ")
    for k,v in statusBucket.items():
        sprintFile.write(k + ":" + str(v) + ", ")
    sprintFile.write('\n')
    sprintFile.close()


'''
Deletes all tickets in the DONE column
'''    
def clearDone():
    deleteListCards("DONE")


###############################################################################
# Functions.
###############################################################################

def cardDetails(jsonCards):
    detailsList = []
    for card in jsonCards:
        details = {}
        isEpic = False

        #-- Name.
        name = card["name"]

        #-- Is Epic?
        if "[Epic]" in name:
            isEpic = True

        #-- Status.
        status = cardStatus(card)
        details["name"] = name
        details["epic"] = isEpic
        details["status"] = status
        detailsList.append(details)
    return detailsList


def cardStatus(jsonCard):
    label = jsonCard["labels"]
    for x in label:
        if x["color"] == "green":
            return "Completed"
        elif x["color"] == "red":
            return "Declined"
        elif x["color"] == "yellow":
            return "Partial Completion"
    return "Unknown"

###############################################################################
# Test Cases.
###############################################################################

def testCaseA():
    boardLists = getBoardLists(work_break_id)
    jsonData = boardLists
    with open("trello.txt", 'w') as f:
        json.dump(jsonData, f)
    

def testCaseB():
    listId = getListId("DONE")
    print(listId)

    listCards = getListCards(listId)
    details = cardDetails(listCards)
    for x in details:
        myStr = ""
        for k,v in x.items():
            myStr += k + ": " + str(v) + " "
        print(myStr)


def testCaseC():
    deleteListCards("TestList")

if __name__ == "__main__":
    parser = ap.ArgumentParser(description="Trello Action aid")
    parser.add_argument("command", type=str, help="command to perform")
    args = parser.parse_args()
    command = args.command
    if command == "complete-sprint":
        completeSprint()
    elif command == "clear-done":
        clearDone()
    else:
        print("Unknown command")

