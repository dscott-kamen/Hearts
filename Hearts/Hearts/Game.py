'''
Created on Apr 21, 2019

@author: Doug Kamen
'''

from GameController import *
from Team import Team
import importlib
import math
import random
import copy

        
class InvalidCardException(Exception):
    pass

class Game():
    
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
            hand = self.hands[event.handPosition]
            self.playCard(hand, event.selectedCards)
        
        elif isinstance(event, CardSelectionRequestEvent):
            hand = self.hands[event.handPosition]
            self.selectCard(hand, event.card)
            
        elif isinstance(event, GameUpdateRequestEvent):
            self.getGameInfo()
            
#        elif isinstance(event, TrickAcceptanceRequestEvent):
#            self.processTrick()
            
#        elif isinstance(event, HandRequestEvent):
#            self.processHandRequest(event.playerName, event.position)

    def autoPlay(self):
        currentHand = self.getTurn()
        if currentHand is not None and isinstance(currentHand.player, ComputerPlayer):
            while 1:
                try:
                    cards = currentHand.player.autoPlayCard(currentHand, self.getPlayableCards(currentHand), 1)
                    self.playCard(currentHand, cards)
                except InvalidCardException:
                    continue
                break
                    

    def createHand(self, name, score=None, inputString=None, position=None):
        return Hand(name, score, inputString, position)

    def createScore(self):
        return Score()

    def deal(self):
        Deck().deal(self.playOrder)

    def finalizeGame(self):
        pass

    def getFirstPlayer(self):
        lookup = self.hands + self.hands
        dealIndex = lookup.index(self.dealer)
        return lookup[dealIndex+1]
        
    def getGameStatus(self):
        return self.gameStatus

    def _copyGame(self):
        game = copy.copy(self)
        game.board = copy.deepcopy(self.board)
        game.hands = copy.deepcopy(self.hands)
        return game
        
    def getGameInfo(self):
        self.evManager.post(GameUpdateEvent(self._copyGame()))

    def getPlayableCards(self, hand):
         
        playableCards = []
        for card in hand.cards:
            try:
                self.validatePlay(hand, card)
                playableCards.append(card)
            except InvalidCardException:
                continue    
        
        return playableCards

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
        
    
    def getTurn(self):
        if len(self.board.cards) < len(self.playOrder):
            return self.playOrder[len(self.board.cards)]
        else:
            return None

    def initializeGame(self, players):
        self.initializeSeats(players)
        self.playOrder = self.hands
                    
    def initializeRound(self):
        if self.isGameComplete():
            self.finalizeGame()
        else:
            self.setDealer()
            self.setPlayOrder(self.getFirstPlayer())
            self.preDealInitialization()
            
            self.deal()            
            self.evManager.post(GameUpdateEvent(self._copyGame()))
            self.postDealInitialization()

    def initializeTrick(self, winner=None):
        if self.isRoundComplete():
            self.initializeRound()
        else:
            if winner is not None:
                self.setPlayOrder(winner)
            self.gameStatus = 'AwaitingPlay'
            self.evManager.post(GameUpdateEvent(self._copyGame()))
            self.autoPlay()
    
    def initializeSeats(self, players):
        
        if self.numTeams is None:
            self.numTeams = self.numPlayers
        
        if not players:
            players = self.getPlayers(self.numPlayers, self.numTeams)
            
        #Set teams and hands
        for i, player in enumerate(players):
            hand = self.createHand(player, score=self.createScore(), position=i)
            self.hands.append(hand)
            if self.numTeams and self.numPlayers != self.numTeams:
                if i < self.numTeams:
                    self.teams.append(Team())
                self.teams[i%2].hands.append(hand)        

    def isGameComplete(self):
        return max([hand.score.gameScore for hand in self.hands]) > self.maxScore
    
    def isRoundComplete(self):
        return len(self.hands[0]) == 0

    def isTrickComplete(self):
        return len(self.board.cards) == len(self.playOrder)


    def playCard(self, hand, cards):
        if isinstance(cards, list):
            if len(cards) != 1:
                self.evManager.post(UserInputErrorEvent('Incorrect number of cards provided'))
                return
            
            card = cards[0]

        if self.getTurn() != hand:
            self.evManager.post(UserInputErrorEvent('It is not your turn'))
            return
        
        #card = hand.selectedCards[0]
        try:
            self.validatePlay(hand, card)
        except InvalidCardException as message:
            self.evManager.post(UserInputErrorEvent(message.args[0]))
            return
                
        self.board.addCard(card, hand)
        hand.playCard(card)
        hand.selectedCards.clear()
        self.postPlayProcessing(hand, card)
        self.evManager.post(CardPlayedEvent(hand, card, self._copyGame()))
        self.processTrick()
        self.autoPlay()
                

    def playGame(self):
        self.initializeRound()

    def postDealInitialization(self):
        self.initializeTrick()

                 
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
            self.evManager.post(TrickCompleteEvent(winner, self._copyGame()))

            self.board.cards.clear()
            self.initializeTrick(winner)
        
    def requestHand(self, player, position=None):
        if position is None:
            for i, hand in enumerate(self.hands):
                if not hand.occupied:
                    position = i
                    break
            
        found = False
        if position is not None:     
            if not self.hands[position].occupied:
                found = True
                self.hands[position].occupied = True
                self.hands[position].name = player.name
                self.hands[position].player = player
            
            
        if found:
#            self.evManager.post(HandRequestResponseEvent(position, self))
            if len([hand.occupied for hand in self.hands if hand.occupied]) == 4:
                self.startGame()
        else:
            position = -1
#            self.evManager.post(HandRequestResponseEvent(position))
                    
        return position
        
    def scoreRound(self):
        raise RuntimeError("Must be implemented in subclass")
                
    def scoreTrick(self, playOrder):
        raise RuntimeError("Must be implemented in subclass")

    def selectCard(self, hand, card):
        #Ignore selection request if its not your turn
        if hand != self.getTurn():
            return
        
        try:
            self.validatePlay(hand, card)
        except InvalidCardException as message:
            self.evManager.post(UserInputErrorEvent(message.args[0]))
            return

        replacedCard = None
        if card not in hand.selectedCards and len(hand.selectedCards) == 1:
            replacedCard = hand.selectedCards[0]
        hand.toggleSelectedCard(card, replacedCard)
    
        ev = CardSelectedEvent(hand, card, self._copyGame())
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
            
    def startGame(self):
        for hand in self.hands:
            if not hand.occupied:
                hand.player = ComputerPlayer()
                hand.occupied = True
        self.initializeRound()
    
    def validatePlay(self, hand, cards):
        pass
   
   
   

class Hand():
    
    def __init__(self, name=None, score=None, inputString=None, position=None):
        self.cards = []
        if inputString != None: self.addCardsFromString(inputString)
        self.name = str(name)
        self.occupied = False
        self.player = None
        self.selectedCards = []
        self.position = position
        
        if score == None:
            self.score = Score()
        else:
            self.score =  score
        
    def addCard(self, card):
        self.cards.append(card)
    
    def addCardsFromString(self, inputString):
        for item in inputString.split():
            self.cards.append(Card.createCardFromString(item))
    
    def getName(self):
        return self.name

    def getCards(self, playableCards, numCards):
        pass
#     def getCards(self, playableCards, numCards, promptMessage):
#         
#         while 1:
#             usrInput = input(promptMessage).upper().split()
#    
#             if len(usrInput) != numCards:
#                 print('Wrong number of cards provided.  Please re-enter.')
#                 continue
#             
#             cards = []
#             validInput = True
#             while validInput:
#                 for token in usrInput: 
#                 
#                     #Convert input into a card
#                     try:
#                         card = Card(token[0], token[1])
#                         if not self.hasCard(card):
#                             print('%s, %s%s is not in your hand.  Please re-enter.\n' % (self.getName(), card.getValue(), card.getSuit()))
#                             validInput = False
#                             return None
#                             break
#                     except:
#                         validInput = False
#                         print('%s, %s is not a valid card. Please re-enter.\n' % (self.getName(), usrInput))
#                         return None
#                         break
# 
#                     if card not in playableCards:
#                         print('%s, %s%s is not a valid play.  Please re-enter.\n' % (self.getName(), card.getValue(), card.getSuit()))
#                         validInput = False
#                         break
#                     
#                     cards.append(card) 
#                        
#                 break
# 
#             return cards
        
    def hasSuit(self, suit):
        return len([card for card in self.card if card.suit == suit]) > 0
    
    def hasCard(self, card):
        return card in self.cards
    
    def playCard(self, playedCard):
        self.cards.remove(playedCard)
    
    def sortHand(self):
        self.cards = sorted(self.cards, key=lambda Card: (Card.suit, Card.getRank()))

    def __getitem__(self, index):
        return self.cards[index]
    
    def __len__(self):
        return len(self.cards)

    def __setitem__(self, index, value):
        self.cards[index] = value

    def __str__(self):
        return ' '.join((str(card) for card in self.cards))
    
class Player():
    def __init__(self, name):
        self._name = name
        self._position = ''
    
    @property
    def name(self): return self._name   
    @property
    def position(self): return self._position

    @name.setter
    def name(self, name):
        self._name = name

    @position.setter
    def position(self, position):
        self._position = position

class ComputerPlayer(Player):
    def __init__(self):
        Player.__init__(self, "Computer")
        
    def autoPlayCard(self, hand, playableCards, numCards):
        return self.randomCardSelector(playableCards, numCards)
    
    def randomCardSelector(self, playableCards, numCards):
        return random.sample(playableCards, numCards)
    
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