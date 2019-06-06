'''
Created on Apr 23, 2019

@author: Doug Kamen
'''

class Team(object):
    '''
    classdocs
    '''



    def __init__(self):
        '''
        Constructor
        '''
        self.roundScore = 0
        self.totalScore = 0
        self.bags = 0
        self.hands = []

    def setBags(self, bags):
        self.bags = bags
        
    def getBags(self):
        return self.bags
    
    def setTotalScore(self, totalScore):
        self.totalScore = totalScore
        
    def getTotalScore(self):
        return self.totalScore

    def setRoundScore(self, roundScore):
        self.__roundScore = roundScore
        
    def getRoundScore(self):
        return self.roundScore

    def addHand(self, hand):
        self.hands.append(hand)
        
    def getHands(self):
        return self.hands