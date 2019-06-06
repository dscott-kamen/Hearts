'''
Created on Apr 20, 2019

@author: Doug Kamen
'''
import math
import random
import Hand

class Deck:
    
    def __init__(self):
        self.cards = []
        for suit in Card.SUIT:
            for value in Card.VALUE:
                self.cards.append(Card(value, suit))
        
    def deal(self, players, numCards=-1):
        print(players[-1].getName() + ' is the dealer.')
        random.shuffle(self.cards)

        #If number of cards not provided, deal all cards
        if numCards == -1:
            numCards = int(len(self.cards)/len(players))

        #Deal the cards
        for j in range(numCards):
            for player in players:
                player.addCard(self.getNextCard())
        
        #Sort the hands
        for player in players:
            player.sortHand()    
            
    def getNextCard(self):
        return self.cards.pop()


class Card:
    SUIT = ('C', 'D', 'H', 'S')
    VALUE = ('2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')

    def __init__(self, value, suit):
        self.suit = suit
        self.value = value

    @classmethod
    def createCardFromString(cls, cardString):
        if cardString[0] not in cls.VALUE or cardString[1] not in cls.SUIT:
            raise TypeError("Not a valid card %s" % cardString)
        return Card(cardString[0], cardString[1])
        
    def getNumValue(self):
        return self.numValue

    def getRank(self):
        return self.VALUE.index(self.value)
    
    def getSuit(self):
        return self.suit
    
    def getValue(self): 
        return self.value
    
    def __str__(self):
        return self.getValue() + self.getSuit()
    
    def __eq__(self, other):
        if self is None and other is None: 
            return True
        elif self is not None and other is not None:
            return self.suit == other.suit and self.value == other.value