'''
Created on Apr 21, 2019

@author: Doug Kamen
'''

from Hand import Hand, Board
from Deck import Deck, Card
from Team import Team 
from Hand import Score
from GameController import *
import importlib
import math
import random
        
class InvalidCardException(Exception):
    pass

class GameMaster():
    
    MAXSCORE = 500
    
    def __init__(self, players, evManager):
        self.evManager = evManager
        self.evManager.registerListener(self)
        self.hands = []
        self.teams = []
        self.board = Board()
        self.dealer = -1
        self.gameStatus = ''
        self.initializeGame(players)

    def notify(self, event):
        
        if isinstance(event, CardPlayRequestEvent):
            self.playCard(event.hand, event.selectedCards)
        
        elif isinstance(event, CardSelectionRequestEvent):
            self.selectCard(event.card, event.hand, event.selectedCards)

        elif isinstance(event, GameInitializedEvent):
            self.initializeRound()
            
        elif isinstance(event, RoundCompleteEvent):
            self.initializeRound()
            
        elif isinstance(event, RoundInitializedEvent):
            self.initializeTrick()
            
        elif isinstance(event, TrickAcceptanceRequestEvent):
            self.processTrick()
            
        elif isinstance(event, TrickCompleteEvent):
            self.initializeTrick(event.winner)

    def deal(self):
        Deck().deal(self.playOrder)

    def getFirstPlayer(self):
        lookup = self.hands + self.hands
        dealIndex = lookup.index(self.dealer)
        return lookup[dealIndex+1]
        
    def getPlayableCards(self, hand):
         
        playableCards = []
        for card in hand.cards:
            try:
                self.validatePlay(hand, card)
                playableCards.append(card)
            except InvalidCardException:
                continue            

    def getPlayers(self, numPlayers, numTeams=None):
        
        if numTeams == None:
            numTeams = numPlayers

            
        players = []
        for i in range(0, numPlayers):
                if numTeams == numPlayers:
                    name = input('Enter Player %d name: ' % (i+1))                    
                else:
                    name = input('Enter Team %d/Hand %d name: ' % (i%numTeams+1, i//numTeams+1))
                players.append(name)
        return players    
    
    def getPlayOrder(self):
        return self.playOrder
        
    def getGameStatus(self):
        return self.gameStatus
    
    def getTurn(self):
        if len(self.board.cards) < len(self.playOrder):
            return self.playOrder[len(self.board.cards)]
        else:
            return None

    def initializeGame(self, players):
        self.initializeSeats(players)
        self.evManager.post(GameInitializedEvent(self.hands, self.board))
                    
    def initializeRound(self):
        if self.isGameComplete():
            self.evManager.post(GameCompleteEvent())
        else:
            self.setDealer()
            self.setPlayOrder(self.getFirstPlayer())
            self.preDealInitialization()
            
            self.deal()
            
            self.postDealInitialization()
            self.evManager.post(RoundInitializedEvent())

    def initializeTrick(self, winner=None):
        if self.isRoundComplete():
            self.evManager.post(RoundCompleteEvent())
        else:
            self.board.cards.clear()
            if winner is not None:
                self.setPlayOrder(winner)
            self.gameStatus = 'AwaitingPlay'
            self.evManager.post(TrickInitializedEvent(self.playOrder, self.getTurn()))
    
    def initializeSeats(self, players):
        
        if self.numTeams is None:
            self.numTeams = self.numPlayers
        
        if not players:
            players = self.getPlayers(self.numPlayers, self.numTeams)
            
        #Set teams and hands
        for i, player in enumerate(players):
            hand = Hand(player, score=self.getScoreObject())
            self.hands.append(hand)
            if self.numTeams and self.numPlayers != self.numTeams:
                if i < self.numTeams:
                    self.teams.append(Team())
                self.teams[i%2].hands.append(hand)        

    def getScoreObject(self):
        return Score()

    def isGameComplete(self):
        return max([hand.score.gameScore for hand in self.hands]) > self.maxScore
#        return max(self.gameScore) > self.maxScore
    
    def isRoundComplete(self):
        return len(self.hands[0]) == 0

    def isTrickComplete(self):
        return len(self.board.cards) == len(self.playOrder)

    def playCard(self, hand, cards):
        
        if len(cards) != self.getCardCountToPlay():
                self.evManager.post(UserInputErrorEvent('Incorrect number of cards provided'))
                return
            
        card = cards[0]
        if self.getTurn() != hand:
            self.evManager.post(UserInputErrorEvent('It is not your turn'))
            return
    
        try:
            self.validatePlay(hand, card)
        except InvalidCardException as message:
            self.evManager.post(UserInputErrorEvent(message.args[0]))
            return
                
        self.board.addCard(card, hand)
        hand.playCard(card)
        self.postPlayProcessing(hand, card)
        self.evManager.post(CardPlayedEvent(hand, card, self.getTurn()))

    def playGame(self):
        self.initializeRound()

    def postDealInitialization(self):
        pass
                 
    def postPlayProcessing(self, hard, card):
        pass
    
    def preDealInitialization(self):
        pass
    
    def processTrick(self):
            
        if self.isTrickComplete():            
            winner = self.scoreTrick(self.playOrder)

            if self.isRoundComplete():
                self.updateRoundScoreWithEndRoundAdjustments()
                self.updateGameScore()

            self.gameStatus = 'Scoring Trick'
            self.evManager.post(TrickCompleteEvent(winner))
            
            return winner
        else:
            return None
        
    def scoreRound(self):
        raise RuntimeError("Must be implemented in subclass")
                
    def scoreTrick(self, playOrder):
        raise RuntimeError("Must be implemented in subclass")

    def selectCard(self, card, hand, selectedCards):
        #Ignore selection request if its not your turn
        if hand != self.getTurn():
            return
        
        try:
            self.validatePlay(hand, card)
        except InvalidCardException as message:
            self.evManager.post(UserInputErrorEvent(message.args[0]))
            return
        
        replacedCard = None
        if card not in selectedCards and len(selectedCards) == 1:
            replacedCard = selectedCards[0]
        ev = CardSelectedEvent(card, hand, replacedCard)
        self.evManager.post(ev)
    
    def setDealer(self):
        #Set the dealer
        if self.dealer==-1:
            self.dealer = self.hands[-1]
        else:
            self.dealer = self.getPlayOrder()[1]

    def setPlayOrder(self, firstHand):
        firstHandIndex = self.hands.index(firstHand)
        self.playOrder = self.hands[firstHandIndex:] + self.hands[:firstHandIndex]
            
    def validatePlay(self, hand, cards):
        pass
    


class Hand:
    
    def __init__(self, name=None, score=None, inputString=None):
        self.cards = []
        if inputString != None: self.addCardsFromString(inputString)
        self.name = str(name)
        if score == None:
            self.score = Score()
        else:
            self.score =  score
        self.passStatus = ''
        self.passedCards = []
        self.receivedCards = []
        
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
    
    def getReceivedCards(self):
        return self.receivedCards
                
    def hasSuit(self, suit):
        return len([card for card in self.card if card.suit == suit]) > 0
    
    def hasCard(self, card):
        return card in self.cards
    
    def playCard(self, playedCard):
        self.cards.remove(playedCard)
    
    def setPassedCards(self, cards):
        self.passedCards.clear()
        for card in cards:
            self.passedCards.append(card)

    def setReceivedCards(self, cards):
        self.receivedCards.clear()
        for card in cards:
            self.receivedCards.append(card)
        
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