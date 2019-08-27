import os
import csv
import sys
import ntpath
import json
import datetime
import requests
import argparse

from config import TRELLO_API_KEY, TRELLO_API_TOKEN

from pprint import pprint

parser = argparse.ArgumentParser(description='Generate sprint burndown chart from Trello board.')
parser.add_argument('boards',help='File containing board(s) and corresponding configurations')

querystring = {"actions":"none","boardStars":"none","cards":"all","card_pluginData":"false","checklists":"none","customFields":"false","fields":"name,desc,descData,closed,idOrganization,pinned,url,shortUrl,prefs,labelNames,archive","lists":"open","labels": "all","members":"all","memberships":"none","membersInvited":"none","membersInvited_ields":"all","pluginData":"false","organization":"false","organization_pluginData":"false","myPrefs":"false","tags":"false","key":TRELLO_API_KEY,"token": TRELLO_API_TOKEN}

teamKanbanLabels = {}
kanbanLists = {}
teamPriorityLabels = {}
priorityLabels = {}
teamSizeLabels = {}
sizeLabels = {}
boards = []
skipMembers = []

def extractLists(lists):
    boardLists = {}
    for boardList in lists:
        boardLists[boardList.get('id')] = {}
        boardLists[boardList.get('id')]['name'] = boardList.get('name')
        if teamKanbanLabels.get(boardList.get('name')) is not None:
            kanbanLists[teamKanbanLabels.get(boardList.get('name'))] = boardList.get('id')
        boardLists[boardList.get('id')]['cards'] = []
    return boardLists

def extractCards(cardsDict,lists,members):
    cards = {}
    for card in cardsDict:
        # card['labels'] -> []
        # card['idLabels'] -> []
        # card['idList'] -> list ID
        # card['idMembers'] -> [member ids]
        if not card.get('closed'):
            newCard = {'name': card.get('name'),
                'idList': card.get('idList'),
                'idMembers': card.get('idMembers'),
                'labels': card.get('idLabels')}
            cards[card.get('id')] = newCard
            if card.get('idList') in lists:
                lists.get(card.get('idList')).get('cards').append(newCard)
    return cards

def extractLabels(labelsDict):
    labels = {}
    for label in labelsDict:
        labels[label.get('id')] = label.get('name') 
        if label.get('name') in teamSizeLabels:
            sizeLabels[teamSizeLabels.get(label.get('name'))] = label.get('id')
        elif label.get('name') in teamPriorityLabels:
            priorityLabels[teamPriorityLabels.get(label.get('name'))] = label.get('id')
    return labels

def extractMembers(membersDict):
    members = {}
    for member in membersDict:
        if member.get('fullName') not in skipMembers:
            newMember = {'name': member.get('fullName'),
                'cardsDone': { 'Size': {'Size - Small': 0,
                        'Size - Medium': 0,
                        'Size - Large': 0,
                        'Unsized': 0},
                    'Shared': { }}}
            for i in range(1,len(membersDict)+1):
                newMember['cardsDone']['Shared'][i] = 0
            members[member.get('id')] = newMember
    return members

# members is a dict of members to object of their counts
def countCardsInListByLabels(listDict,labels,members):
    for card in listDict.get('cards'):
        for cardMember in card.get('idMembers'):
            members[cardMember]['cardsDone']['Shared'][len(card.get('idMembers'))] += 1
            sizeAdded = False
            for labelName,labelId in labels.items():
                if labelId in card.get('labels'):
                    members[cardMember]['cardsDone']['Size'][labelName] += 1
                    sizeAdded = True
                    break
            if not sizeAdded:
                members[cardMember]['cardsDone']['Size']['Unsized'] += 1

def countCardsInListByMemberId(cardList,memberId):
    cardCount = 0
    for card in cardList:
        if memberId in card.get('idMembers'):
            cardCount += 1
    return cardCount

# boardDict contains the dict of the JSON file from Trello
def analyzeSprint(boardDict):
    print("Analyzing "+boardDict.get('name')+"...")
    boardData = {'name': boardDict.get('name'), 'date': boardDict.get('dateLastView')}

    members = extractMembers(boardDict.get('members'))
    boardLists = extractLists(boardDict.get('lists'))
    labels = extractLabels(boardDict.get('labels'))
    cards = extractCards(boardDict.get('cards'),boardLists,members)
    return {**boardData,**{'members': members, 'boardLists': boardLists, 'labels': labels, 'cards': cards}}

def writeBurndown(csvFilename,burndownDict,memberBreakdown=[]):
    print("Writing to "+csvFilename+"...")
    data = [['',burndownDict.get('date')]]
    for kanbanList in kanbanLists:
        cardList = burndownDict.get('boardLists').get(kanbanLists.get(kanbanList)).get('cards')
        cardsInList = len(cardList)
        data.append([kanbanList,cardsInList])
        if kanbanList in memberBreakdown:
            for memberId,member in burndownDict.get('members').items():
                data.append([member.get('name'),countCardsInListByMemberId(cardList,memberId)])
    countCardsInListByLabels(burndownDict.get('boardLists').get(kanbanLists.get('Biz/Dev Done')),sizeLabels,
        burndownDict.get('members'))
    data.append(['name','hours','small','medium','large','1','2','3','4','5','share average'])
    for memberId,member in burndownDict.get('members').items():
        small = member.get('cardsDone').get('Size').get('Size - Small')
        medium = member.get('cardsDone').get('Size').get('Size - Medium')
        large = member.get('cardsDone').get('Size').get('Size - Large')
        one = member.get('cardsDone').get('Shared').get(1)
        two = member.get('cardsDone').get('Shared').get(2)
        three = member.get('cardsDone').get('Shared').get(3)
        four = member.get('cardsDone').get('Shared').get(4)
        five = member.get('cardsDone').get('Shared').get(5)
        try:
            shareAverage = (one + 2*two + 3*three + 4*four + 5*five) / (one + two + three + four + five)
            hours = (small * 2 + medium * 4 + large * 8) / shareAverage
        except ZeroDivisionError:
            print("Warning: "+member.get('name')+" has not worked on any cards")
            shareAverage = 0
            hours = 0
        data.append([member.get('name'),hours,small,medium,large,one,two,three,four,five,shareAverage])
    with open(csvFilename,'w') as csvfile:
        csvwriter = csv.writer(csvfile,delimiter=',',quotechar='|',quoting=csv.QUOTE_MINIMAL)
        for dataRow in data:
            csvwriter.writerow(dataRow)

def configure(batchFilename):
    with open(batchFilename,'r') as batchFile:
        configuration = json.loads(batchFile.read())
        if 'skipMembers' in configuration:
            global skipMembers
            skipMembers = configuration.get('skipMembers')
        for newBoard in configuration.get('boards'):
            boards.append(newBoard)

def runBatch():
    for board in boards:
        global teamKanbanLabels
        global teamPriorityLabels
        global teamSizeLabels
        if 'skipMembers' in board:
            global skipMembers
            skipMembers = board.get('skipMembers')
        initializeGlobals()
        teamKanbanLabels = board.get('teamKanbanLabels')
        teamPriorityLabels = board.get('teamPriorityLabels') if 'teamPriorityLabels' in board else {}
        teamSizeLabels = board.get('teamSizeLabels')
        boardJson = retrieveJsonFromURL(board.get('url'))
        burndownFilename = "csv/"+boardJson.get('name')+'.csv'
        writeBurndown(burndownFilename,analyzeSprint(boardJson),
            ['Biz/Dev Backlog',
             'Biz/Dev In Progress',
             'Biz/Dev In Review'])

        
def retrieveJsonFromURL(url):
    return json.loads(requests.request("GET", url, params=querystring).text)

def initializeGlobals():
    global teamKanbanLabels
    global kanbanLists
    global teamPriorityLabels
    global priorityLabels
    global teamSizeLabels
    global sizeLabels
    teamKanbanLabels = {}
    kanbanLists = {}
    teamPriorityLabels = {}
    priorityLabels = {}
    teamSizeLabels = {}
    sizeLabels = {}
    
if __name__ == '__main__':
    args = parser.parse_args()
    if args.boards is not None:
        configure(args.boards)
        runBatch()
        
