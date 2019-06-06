'''
Created on Apr 21, 2019

@author: Doug Kamen
'''

from Hand import Hand, Board
from Deck import Deck, Card
from Team import Team 
from Hand import Score
from GameController import *
        
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
        
        if isinstance(event, TrickAcceptanceRequestEvent):
            self.processTrick()
            
        elif isinstance(event, RoundInitializedEvent):
            self.initializeTrick()
            
        elif isinstance(event, CardSelectionRequestEvent):
            self.selectCard(event.card, event.hand, event.selectedCards)

        elif isinstance(event, TrickCompleteEvent):
            self.initializeTrick(event.winner)

        elif isinstance(event, RoundCompleteEvent):
            self.initializeRound()
            
        elif isinstance(event, GameInitializedEvent):
            self.initializeRound()
            
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
    
