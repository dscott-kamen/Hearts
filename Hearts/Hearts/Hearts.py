'''
Created on May 20, 2019

@author: Doug Kamen
'''
from Hand import Hand, HeartsScore
from Deck import Card, Deck
from Team import Team 
from Game import GameMaster, InvalidCardException
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
                #implement pass functionality
                #when pass is complete set flag and re-trigger RoundInitialized Event
        
        elif isinstance(event, CardPlayRequestEvent):
            if self.getGameStatus() == 'AwaitingPlay':
                self.playCard(event.hand, event.selectedCards)
            elif self.getGameStatus() == 'PassCards':
                self.passCards(event.hand, event.selectedCards)
                
        elif isinstance(event, CardPlayedEvent):
            if self.gameStatus == 'AwaitingPlay':
                if not self.heartsBroken and event.card.getSuit() == 'H':
                    self.heartsBroken = True
                    
            GameMaster.notify(self, event)

        elif isinstance(event, PassCompleteAcceptanceRequestEvent):
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
        
    def getScoreObject(self):
        return HeartsScore()
    
    def isFirstTrick(self, hand):
        return len(hand.cards) == 13

    def isFirstPlay(self):
        return len(self.board.cards) == 0
    
    def passCards(self, hand, cards):
        if len(cards) != 3:
                self.evManager.post(UserInputErrorEvent('Incorrect number of cards provided'))
                return
            
        hand.passComplete = True 
        hand.setPassedCards(cards)
        if len([hand for hand in self.hands if hand.passComplete]) == 4:

            #Send passedCard to each user
            for hand in self.hands:
                fromPlayer = self.getPassFromHand(hand)
                for removedCard, addedCard in zip(hand.passedCards, fromPlayer.passedCards):
                    hand.cards.remove(removedCard)
                    hand.cards.append(addedCard)
                hand.sortHand()
            
            #Update post pass data
            self.set2ClubPlayOrder()
            self.isPassComplete = True
            self.evManager.post(PassCompleteEvent())

    def postDealInitialization(self):
        self.set2ClubPlayOrder()
 
    def set2ClubPlayOrder(self):
        for hand in self.hands:
            if hand.hasCard(Card('2','C')):
                self.setPlayOrder(hand)
                break
 
    def postPlayProcessing(self, hand, card):
        if not self.heartsBroken and card.getSuit() == 'H':
            self.heartsBroken = True
 
        
    def preDealInitialization(self):
        for hand in self.hands:
            hand.score.roundScore = 0
            hand.score.roundPointsTaken = False
        self.heartsBroken = False
        self.passComplete = False
        self.currentRoundPassType = self.getNextPassType()
        if self.currentRoundPassType == 'Keeper':
            self.passComplete = True
        for hand in self.hands:
            hand.passedCards.clear()        
            
       
    def scoreTrick(self, playOrder):
        winner = self.determineTrickWinner(playOrder)
        points = self.computeTrickPoints()
        self.updateRoundScore(winner, points)
        return winner
    
    def selectCard(self, card, hand, selectedCards):
        if self.gameStatus == 'PassCards':
            #Once you've accepted pass complete, can't try to pass more cards
            if hand.passComplete:
                return
            
            replacedCard = None
            if card not in selectedCards and len(selectedCards) == 3:
                replacedCard = selectedCards[0]
            ev = CardSelectedEvent(card, hand, replacedCard)
            self.evManager.post(ev)

        else:
            GameMaster.selectCard(self, card, hand, selectedCards)
        
    
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
                                                    
if __name__ == "__main__":

    #players = []    
    players = ['Al', 'Bob', 'Carol', 'Doug']
    hearts = Hearts(players)
    hearts.playGame()

