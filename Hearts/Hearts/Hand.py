'''
Created on Apr 20, 2019

@author: Doug Kamen
'''
from Deck import Card 
import importlib


class Hand:
    
    def __init__(self, name=None, score=None, inputString=None):
        self.cards = []
        if inputString != None: self.addCardsFromString(inputString)
        self.name = str(name)
        if score == None:
            self.score = Score()
        else:
            self.score =  score
        self.passComplete = False
        self.passedCards = []
        
    def addCard(self, card):
        self.cards.append(card)
    
    def addCardsFromString(self, inputString):
        for item in inputString.split():
            self.cards.append(Card.createCardFromString(item))
    
    def getName(self):
        return self.name

    def getCard(self, playableCards, promptMessage):
        return self.getCards(playableCards, 1, promptMessage)[0]
    
    def getCards(self, playableCards, numCards, promptMessage):
        
        while 1:
            usrInput = input(promptMessage).upper().split()
   
            if len(usrInput) != numCards:
                print('Wrong number of cards provided.  Please re-enter.')
                continue
            
            cards = []
            validInput = True
            while validInput:
                for token in usrInput: 
                
                    #Convert input into a card
                    try:
                        card = Card(token[0], token[1])
                        if not self.hasCard(card):
                            print('%s, %s%s is not in your hand.  Please re-enter.\n' % (self.getName(), card.getValue(), card.getSuit()))
                            validInput = False
                            return None
                            break
                    except:
                        validInput = False
                        print('%s, %s is not a valid card. Please re-enter.\n' % (self.getName(), usrInput))
                        return None
                        break

                    if card not in playableCards:
                        print('%s, %s%s is not a valid play.  Please re-enter.\n' % (self.getName(), card.getValue(), card.getSuit()))
                        validInput = False
                        break
                    
                    cards.append(card) 
                       
                break

            return cards
        
    def getPassedCards(self):
        return self.passedCards
                
    def hasSuit(self, suit):
        return len([card for card in self.card if card.suit == suit]) > 0
    
    def hasCard(self, card):
        return card in self.cards
    
    def playCard(self, playedCard):
        self.cards.remove(playedCard)
    
    def setPassedCards(self, cards):
        self.passedCards = cards
        
    def sortHand(self):
        self.cards = sorted(self.cards, key=lambda Card: (Card.suit, Card.getRank()))
        
    def __str__(self):
        return ' '.join((str(card) for card in self.cards))
    
    def __len__(self):
        return len(self.cards)

    def __getitem__(self, index):
        return self.cards[index]
    
    def __setitem__(self, index, value):
        self.cards[index] = value
        
        
class Board():
    def __init__(self, name=None, inputString=None):
        Hand.__init__(self, name, inputString)
        self.cardSource = {}
        
        
    def addCard(self, card, hand):
        Hand.addCard(self, card)
        self.cardSource[str(card)] = hand
    
class Score():
    def __init__(self):
        self.gameScore = 0
        self.roundScore = 0
        
class HeartsScore(Score):
    def __init__(self):
        Score.__init__(self)
        self.roundPointsTaken = False