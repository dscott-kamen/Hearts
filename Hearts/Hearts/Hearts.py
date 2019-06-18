'''
Created on May 20, 2019

@author: Doug Kamen
'''
from Team import Team 
from Game import Game, InvalidCardException, Hand, Score, Card, Deck, ComputerPlayer, Player, copy
from GameController import *


class Hearts(Game):
    '''
    classdocs
    '''
    GAMESTATUS_PASSCARDS = 100
    
    def __init__(self, players, evManager):
        self.numPlayers = 4
        self.numTeams = 4
        self.maxScore = 100
        self.passComplete = False
        self.passTypes = ['Left', 'Right', 'Across','Keeper']
        self.passFromOffset = {'Left':3, 'Right':1, 'Across':2, 'Keeper':0}
        self.currentRoundPassType = 'Keeper'
        Game.__init__(self, players, evManager)
    
    
#     def notify(self, event):
#         
#         if isinstance(event, PassCompleteAcceptanceRequestEvent):
#             hand = self.hands[event.handPosition]
#             self.finalizePass(hand)
#             
#         else:
#             Game.notify(self, event)

    def autoPlay(self):
        if self.gameStatus == self.GAMESTATUS_PASSCARDS:
            for hand in self.hands:
                if isinstance(hand.player, ComputerPlayer) and not hand.passSubmitted:
                    while 1:
                        try:
                            cards = hand.player.autoPlayCard(hand, hand.cards, 3)
                            self.playCard(hand, cards)
                        except InvalidCardException:
                            continue
                        break
        else:
            Game.autoPlay(self)

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

    def createHand(self, name, score=None, inputString=None, position=None):
        return HeartsHand(name, score, inputString, position)

    def createScore(self):
        return HeartsScore()
    
    def determineTrickWinner(self, playOrder):
        suit = self.board.cards[0].suit
        return max([(card.getRank(), hand) for card, hand in zip(self.board.cards, playOrder) if card.suit == suit])[1]

    def finalizePass(self, hand):
        hand.selectedCards.clear()
        Game.postDealInitialization(self)

    def _getNextPassType(self):
        lookup = self.passTypes + self.passTypes
        idx = lookup.index(self.currentRoundPassType)
        return lookup[idx+1]

    def _getPassFromHand(self, hand):
        lookup = self.hands + self.hands
        idx = lookup.index(hand)
        offset = self.passFromOffset[self.currentRoundPassType]
        return lookup[idx+offset]        
        
    def getPlayableCards(self, hand):
        if self.gameStatus == self.GAMESTATUS_PASSCARDS:
            return hand.cards
        else:
            return Game.getPlayableCards(self, hand)
        
    def isFirstTrick(self, hand):
        return len(hand.cards) == 13

    def isFirstPlay(self):
        return len(self.board.cards) == 0

    def passCards(self):
        if len([hand for hand in self.hands if hand.passSubmitted]) == 4:
            
            #Send passedCard to each user
            for hand in self.hands:
                fromPlayer = self._getPassFromHand(hand)
                hand.setReceivedCards(fromPlayer.getPassedCards())
                for removedCard, addedCard in zip(hand.passedCards, fromPlayer.passedCards):
                    hand.cards.remove(removedCard)
                    hand.cards.append(addedCard)
                hand.sortHand()
            #Update post pass data
            self.set2ClubPlayOrder()
            self.passComplete = True
            self.evManager.post(GameUpdateEvent(self._copyGame()))
            self.gameStatus = self.GAMESTATUS_PLAYCARDS
            for hand in self.hands:
                hand.selectedCards.clear()
            self.evManager.post(GameUpdateEvent(self._copyGame()))
            
            self.autoPlay()

    def playCard(self, hand, cards):
        if self.gameStatus == self.GAMESTATUS_PASSCARDS:

            if len(cards) != 3:
                self.evManager.post(UserInputErrorEvent('Incorrect number of cards provided'))
                return 
            
            hand.setPassedCards(cards)
            hand.passSubmitted = True
            self.evManager.post(CardPlayedEvent(hand, cards, self._copyGame()))        
            self.passCards()
        else:
            Game.playCard(self, hand, cards)

    def postDealInitialization(self):
        self.set2ClubPlayOrder()
        if self.passComplete:
            Game.postDealInitialization(self)
        else:
            self.gameStatus = self.GAMESTATUS_PASSCARDS
            self.autoPlay()
 
    def postPlayProcessing(self, hand, card):
        if not self.heartsBroken and card.getSuit() == 'H':
            self.heartsBroken = True
 
    def preDealInitialization(self):
        for hand in self.hands:
            hand.score.roundScore = 0
            hand.score.roundPointsTaken = False
        self.heartsBroken = False
        
        # Initialized pass cards
        self.currentRoundPassType = self._getNextPassType()
        if self.currentRoundPassType == 'Keeper':
            self.passComplete = True
        else:
            self.passComplete = False
            for hand in self.hands:
                hand.passSubmitted = False            
        for hand in self.hands:
            hand.passedCards.clear()
            hand.receivedCards.clear()        
               
    def scoreTrick(self, playOrder):
        winner = self.determineTrickWinner(playOrder)
        points = self.computeTrickPoints()
        self.updateRoundScore(winner, points)
        return winner
    
    def selectCard(self, hand, card):
        if self.gameStatus == self.GAMESTATUS_PASSCARDS:
            #Once you've accepted pass complete, can't try to pass more cards
            if hand.passSubmitted:
                return
            
            replacedCard = None
            if card not in hand.selectedCards and len(hand.selectedCards) == 3:
                replacedCard = hand.selectedCards[0]
            hand.toggleSelectedCard(card, replacedCard)
                
            ev = CardSelectedEvent(hand, card, self._copyGame())
            self.evManager.post(ev)

        else:
            Game.selectCard(self, hand, card)
        
    def set2ClubPlayOrder(self):
        for hand in self.hands:
            if hand.hasCard(Card('2','C')):
                self.setPlayOrder(hand)
                break
 
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
        
        if self.isFirstPlay():
            heartsCount = len([card for card in hand.cards if card.suit == 'H'])
            handCount = len(hand.cards)
            if not self.heartsBroken and handCount > heartsCount and card.suit == 'H':
                raise InvalidCardException('Hearts not broken')
        
        if not self.isFirstPlay():
            suit = self.board.cards[0].suit
            suitCount = len([card for card in hand.cards if card.suit == suit])
            if suitCount > 0 and card.suit != suit:
                raise InvalidCardException('Must follow suit')
        
        return True

class HeartsHand(Hand):
    
    def __init__(self, name, score=None, inputString=None, position=None):
        Hand.__init__(self, name, score, inputString, position)

        self.passSubmitted = False
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
      
    def toggleSelectedCard(self, card, replacedCard):
        if replacedCard is not None:
            replacedCard = self.selectedCards[0]
            self.selectedCards.remove(replacedCard)
            
        if card in self.selectedCards:
            self.selectedCards.remove(card)
        else:
            self.selectedCards.append(card)


class HeartsComputerPlayer(ComputerPlayer):
    
    def __init__(self, game):
        ComputerPlayer.__init__(self, game)

          
      
class HeartsScore(Score):
    def __init__(self):
        Score.__init__(self)
        self.roundPointsTaken = False
        
        
