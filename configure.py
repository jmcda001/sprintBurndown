import requests
import argparse
import re
import json

from pprint import pprint

from config import TRELLO_API_KEY, TRELLO_API_TOKEN

parser = argparse.ArgumentParser(description='Generate configuration for sprint burndown for a specific Trello board.')
parser.add_argument('--url',dest='url',help='URL for the trello board')
parser.add_argument('--id',dest='id',help='ID for the trello board')
parser.add_argument('-o',dest='outFilename',help='Output filename for the configuration')

APIKeyToken = {"key":TRELLO_API_KEY,"token": TRELLO_API_TOKEN}
querystring = {**{"actions":"none","boardStars":"none","cards":"none","card_pluginData":"false","checklists":"none","customFields":"false","fields":"name","lists":"open","labels": "none","members":"none","memberships":"none","membersInvited":"none","membersInvited_ields":"none","pluginData":"false","organization":"false","organization_pluginData":"false","myPrefs":"false","tags":"false"},**APIKeyToken}


#https://trello.com/b/wrXzb9ug/checkmates
trelloBoardURL = re.compile('https://trello.com/b/(\w+)/\S+')
def extractTrelloBoardID(url):
    if trelloBoardURL.match(url):
        return trelloBoardURL.match(url).group(1)
    else:
        print("Warning: \""+url+"\" is not a URL for a trello board")
        return None
    

def configureMembers(boardId):
    print('Configuring tracked members.......')
    skipMembers = []
    members = json.loads(requests.request("GET", "https://api.trello.com/1/boards/"+boardId+"/members", 
        params=APIKeyToken).text)
    for index,member in enumerate(members):
        print(str(index)+") "+member.get('fullName'))
    print()
    skippedIndices = input("List the indices of members you DON'T want to track: ")
    for index in skippedIndices.split(','):
        skipMembers.append(members[int(index)].get('fullName'))
    return {"skipMembers": skipMembers}

def configureTrackedLists(boardId):
    print('Configuring tracked lists.......')
    trackedLists = {}
    lists = json.loads(requests.request("GET", "https://api.trello.com/1/boards/"+boardId+"/lists", 
        params=APIKeyToken).text)
    for index,boardList in enumerate(lists):
        print(str(index)+") "+boardList.get('name'))
    print()
    usBacklog = input("Which list corresponds to the 'User Story Backlog'? ")
    usDoing = input("Which list corresponds to the 'User Story In Progress'? ")
    usDone = input("Which list corresponds to the 'User Story Done'? ")
    bizDevBacklog = input("Which list corresponds to the 'Biz/Dev Backlog'? ")
    bizDevDoing = input("Which list corresponds to the 'Biz/Dev In Progress'? ")
    bizDevReview = input("Which list corresponds to the 'Biz/Dev In Review'? ")
    bizDevDone = input("Which list corresponds to the 'Biz/Dev Done'? ")
    print()
    return { "teamKanbanLabels": {lists[int(usBacklog)].get('name'): "US - Backlog",
        lists[int(usDoing)].get('name'): "US - In Progress",
        lists[int(usDone)].get('name'): "US - Done",
        lists[int(bizDevBacklog)].get('name'): "Biz/Dev Backlog",
        lists[int(bizDevDoing)].get('name'): "Biz/Dev In Progress",
        lists[int(bizDevReview)].get('name'): "Biz/Dev In Review",
        lists[int(bizDevDone)].get('name'): "Biz/Dev Done"}}

def configureLabelMapping(boardId):
    print('Configuring label mapping.......')
    teamLabels = []
    labels = json.loads(requests.request("GET", "https://api.trello.com/1/boards/"+boardId+"/labels", 
        params=APIKeyToken).text)
    for label in labels:
        teamLabels.append(label.get('name'))
    for index,label in enumerate(teamLabels):
        print(str(index)+") "+label)
    print()
    smallIndex = input("Which label corresponds to a 'Size - Small' task? ")
    mediumIndex = input("Which label corresponds to a 'Size - Medium' task? ")
    largeIndex = input("Which label corresponds to a 'Size - Large' task? ")
    print()
    return {"teamSizeLabels": {teamLabels[int(smallIndex)]: "Size - Small",
        teamLabels[int(mediumIndex)]: "Size - Medium",
        teamLabels[int(largeIndex)]: "Size - Large"}}


def configure(boardId):
    boardURL = "https://api.trello.com/1/boards/"+boardId
    boardName = json.loads(requests.request("GET", "https://api.trello.com/1/boards/"+boardId, 
        params=querystring).text).get('name')
    skipMembers = configureMembers(boardId)
    listsMapping = configureTrackedLists(boardId)
    labelMapping = configureLabelMapping(boardId)
    return {"boards":[{**{"name":boardName,"url":boardURL},**listsMapping,**skipMembers,**labelMapping}]}


if __name__ == '__main__':
    args = parser.parse_args()
    if args.url is not None:
        boardId = extractTrelloBoardID(args.url)
    elif args.id is not None:
        boardId = args.id
    else:
        boardId = extractTrelloBoardID(input("Input the URL for the Trello board"))
    if boardId is not None:
        configuration = configure(boardId)
    if args.outFilename is not None:
        print("Writing configuration to \""+args.outFilename+"\"...")
        with open(args.outFilename,'w') as out:
            out.write(json.dumps(configuration))
    else:
        pprint(configuration)
        
