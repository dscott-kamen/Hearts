'''
Created on May 20, 2019

@author: Doug Kamen
'''
from Team import Team 
from Game import GameMaster, InvalidCardException, Hand, Score, Card, Deck
from GameController import *


class Hearts(GameMaster):
    '''
    classdocs
    '''
    def __init__(self, players, evManager):
        self.numPlayers = 4
        self.numTeams = 4
        self.maxScore = 100
        self.isPassComplete = False
        self.passTypes = ['Left', 'Right', 'Across','Keeper']
        self.passFromOffset = {'Left':3, 'Right':1, 'Across':2, 'Keeper':0}
        self.currentRoundPassType = 'Keeper'
        GameMaster.__init__(self, players, evManager)
    
    def notify(self, event):
        
        if isinstance(event, RoundInitializedEvent):
            if self.isPassComplete:
                GameMaster.notify(self, event)
            else:
                self.gameStatus = 'PassCards'
        
        elif isinstance(event, CardPassRequestEvent):
            self.submitHandPassCards(event.hand, event.selectedCards)
                
        elif isinstance(event, PassCompleteAcceptanceRequestEvent):
            event.hand.passStatus = 'Complete'
            self.evManager.post(RoundInitializedEvent())
            
        else:
            GameMaster.notify(self, event)

    def computeTrickPoints(self):
        points = 0
        for card in self.board.cards:
            if card.suit == 'H':
                points += 1
            if card.suit == 'S' and card.value == 'Q':
                points += 13
            if card.suit == 'D' and card.value == 'J':
                points += -10
        return points

    def createHand(self, name, score=None, inputString=None):
        return HeartsHand(name, score, inputString)

    def createScore(self):
        return HeartsScore()
    
    def determineTrickWinner(self, playOrder):
        suit = self.board.cards[0].suit
        return max([(card.getRank(), hand) for card, hand in zip(self.board.cards, playOrder) if card.suit == suit])[1]
        
    def getCardCountToPlay(self):
        if self.getGameStatus() == 'AwaitingPass':
            return 3        
        elif self.getGameStatus() == 'AwaitingPlay':
            return 1
 
    def getNextPassType(self):
        lookup = self.passTypes + self.passTypes
        idx = lookup.index(self.currentRoundPassType)
        return lookup[idx+1]

    def getPassFromHand(self, hand):
        lookup = self.hands + self.hands
        idx = lookup.index(hand)
        offset = self.passFromOffset[self.currentRoundPassType]
        return lookup[idx+offset]        
        
    def isFirstTrick(self, hand):
        return len(hand.cards) == 13

    def isFirstPlay(self):
        return len(self.board.cards) == 0
    
    def passCards(self):
        if len([hand for hand in self.hands if hand.passStatus == 'Submitted']) == 4:
            
            #Send passedCard to each user
            for hand in self.hands:
                fromPlayer = self.getPassFromHand(hand)
                hand.setReceivedCards(fromPlayer.getPassedCards())
                for removedCard, addedCard in zip(hand.passedCards, fromPlayer.passedCards):
                    hand.cards.remove(removedCard)
                    hand.cards.append(addedCard)
                hand.sortHand()
                self.evManager.post(PassCompleteEvent(hand, hand.passedCards, fromPlayer.passedCards))
            
            #Update post pass data
            self.set2ClubPlayOrder()
            self.isPassComplete = True
            self.gameStatus = 'AwatingPlay'

    def postDealInitialization(self):
        self.set2ClubPlayOrder()
 
    def postPlayProcessing(self, hand, card):
        if not self.heartsBroken and card.getSuit() == 'H':
            self.heartsBroken = True
 
    def preDealInitialization(self):
        for hand in self.hands:
            hand.score.roundScore = 0
            hand.score.roundPointsTaken = False
        self.heartsBroken = False
        
        # Initialized pass cards
        self.currentRoundPassType = self.getNextPassType()
        if self.currentRoundPassType == 'Keeper':
            self.passComplete = True
            for hand in self.hands:
                self.passStatus = 'Complete'
        else:
            self.passComplete = True
            for hand in self.hands:
                hand.passStatus = 'Initiated'            
        for hand in self.hands:
            hand.passedCards.clear()
            hand.receivedCards.clear()        
               
    def scoreTrick(self, playOrder):
        winner = self.determineTrickWinner(playOrder)
        points = self.computeTrickPoints()
        self.updateRoundScore(winner, points)
        return winner
    
    def selectCard(self, card, hand, selectedCards):
        if self.gameStatus == 'PassCards':
            #Once you've accepted pass complete, can't try to pass more cards
            if hand.passStatus == 'Submitted':
                return
            
            replacedCard = None
            if card not in selectedCards and len(selectedCards) == 3:
                replacedCard = selectedCards[0]
            ev = CardSelectedEvent(card, hand, replacedCard)
            self.evManager.post(ev)

        else:
            GameMaster.selectCard(self, card, hand, selectedCards)
        
    def set2ClubPlayOrder(self):
        for hand in self.hands:
            if hand.hasCard(Card('2','C')):
                self.setPlayOrder(hand)
                break
 
    def submitHandPassCards(self, hand, cards):
        if len(cards) != 3:
                self.evManager.post(UserInputErrorEvent('Incorrect number of cards provided'))
                return
            
        hand.passStatus = 'Submitted' 
        hand.setPassedCards(cards)
        self.evManager.post(CardPassLockEvent(hand, cards))
        
        self.passCards()
    
    def updateGameScore(self):
        for hand in self.hands:
            hand.score.gameScore += hand.score.roundScore
        
    def updateRoundScore(self, winner, points):
        winner.score.roundScore += points
        if points != 0 and points != -10:
            winner.score.roundPointsTaken = True

    def updateRoundScoreWithEndRoundAdjustments(self):
        roundPointsTaken = [hand for hand in self.hands if hand.score.roundPointsTaken]
        if len(roundPointsTaken) == 1:
            for hand in self.hands:
                if hand.score.roundPointsTaken:
                    hand.score.roundScore += -26
                else:
                    hand.score.roundScore += 26

    def validatePlay(self, hand, card):
        #first play must be 2C
        if self.isFirstTrick(hand) and self.isFirstPlay() and not (card.suit == 'C' and card.value == '2'):
            raise InvalidCardException('First play must 2C')
        
        if self.isFirstTrick(hand) and (card.suit == 'H' or (card.suit == 'S' and card.value == 'Q')):
            raise InvalidCardException('Cannot draw blood on first trick')
        
        if self.isFirstTrick(hand):
            heartsCount = len([card for card in hand.cards if card.suit == 'H'])
            handCount = len(hand.cards)
            if self.heartsBroken and handCount > heartsCount and card.suit == 'H':
                raise InvalidCardException('Hearts not broken')
        
        if not self.isFirstPlay():
            suit = self.board.cards[0].suit
            suitCount = len([card for card in hand.cards if card.suit == suit])
            if suitCount > 0 and card.suit != suit:
                raise InvalidCardException('Must follow suit')
        
        return True

class HeartsHand(Hand):
    
    def __init__(self, name, score=None, inputString=None):
        Hand.__init__(self, name, score, inputString)

        self.passStatus = ''
        self.passedCards = []
        self.receivedCards = []

    def getPassedCards(self):
        return self.passedCards
    
    def getReceivedCards(self):
        return self.receivedCards
                
    def setPassedCards(self, cards):
        self.passedCards.clear()
        for card in cards:
            self.passedCards.append(card)

    def setReceivedCards(self, cards):
        self.receivedCards.clear()
        for card in cards:
            self.receivedCards.append(card)
        
class HeartsScore(Score):
    def __init__(self):
        Score.__init__(self)
        self.roundPointsTaken = False
        
        
