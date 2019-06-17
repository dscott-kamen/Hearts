'''
Created on Apr 21, 2019

@author: Doug Kamen
'''

from Hand import Hand
from Deck import Card, Deck
from Team import Team 
from Game import Game
import math
class Spades(Game):
    
    def __init__(self, args):
        self.numPlayers = 4
        self.numTeams = 2
        self.maxScore = 100
        Game.__init__(self, args)

    def getBids(self, playOrder):
        
        bids = []
        for hand in playOrder:

            while 1:
                print(hand)
                usrInput = input('%s, please enter your bid (0 for NIL): ' % (hand.getName()))
             
                try:
                    bid = int(usrInput)
                    if bid < 0 or bid > 13:
                        print('%s, %s is not a number between 0 and 13. Please re-enter.\n' % (hand.getName(), usrInput))
                        continue
                                             
                except:
                    print('%s, %s is not a number between 0 and 13. Please re-enter.\n' % (hand.getName(), usrInput))
                    continue
                     
                break
            bids.append(bid) 
                
        return bids
            
    def getPlayableCards(self, hand, board):
        
        if len(board) ==  0:
            playableCards = [card for card in hand.cards if self.spadesBroken or card.suit != 'S']
        else:
            leadSuit = board.cards[0].suit
            playableCards = [card for card in hand.cards if card.suit == leadSuit]
            if len(playableCards) == 0:
                playableCards = hand.cards
        return playableCards
        
    def initializeGame(self, args):

        Game.initializeGame(self, args)
        self.tricksBid = [0 for hand in self.hands]
        self.bags = [0 for hand in self.hands]
        self.totalScore = [0 for hand in self.teams]

   
    def playCard(self, hand, board):
            
        prompt = "%s, it's your turn\nYour cards: %s\nCards played: %s\nWhat's your play?:  " % (hand.getName(), str(hand), str(board))
        card = hand.getCard(self.getPlayableCards(hand, board), prompt)
        hand.playCard(card)
        if not self.spadesBroken and card.getSuit() == 'S':
            self.spadesBroken = True
        return card
    
    def postDealInitialization(self):
        self.tricksBid = self.getBids(self.getPlayOrder(self.getFirstPlayer()))
                 
    def preDealInitialization(self):
        self.tricksWon = [0 for hand in self.hands]
        self.roundScore = [0 for team in self.teams]
        self.spadesBroken = False

    def scoreRound(self):
        
        for (i, team) in enumerate(self.teams):
            tricksWon = 0
            tricksBid = 0
            points = 0
            for hand in team:
                position = hand.getPosition()
                if self.tricksBid[position] != 0:
                    tricksWon += self.tricksWon[position]
                    tricksBid += self.tricksBid[position]
                else:
                    if self.tricksWon[position] == 0:
                        points += 100
                        print('%s got Nil, 100 points awarded!' % (self.hands[position].getName()))
                    else:
                        points += -100
                        print('%s failed to get Nil' % (self.hands[position].getName()))
                
                        
            if tricksWon >= tricksBid:
                x = i
                bags = tricksWon - tricksBid
                points += tricksBid * 10 + bags
                print('%s/%s bid %d won %d for %d points.' % (team[0].getName(), team[1].getName(), tricksBid, tricksWon, tricksBid * 10 + bags))
                
                self.bags[i] += bags     
                if self.bags[i] >= 10:
                    points += -100
                    self.bags[i] += -10
                    print('%s/%s accumulated 10 bags for -100 points.' % (team[0].getName(), team[1].getName()))
            else:
                print('%s/%s bid %d won %d for 0 points.' % (team[0].getName(), team[1].getName(), tricksBid, tricksWon))
                print(team[0].getName() + '/' + team[1].getName() + ' bid ' + str(tricksBid) + ', won ' + str(tricksWon) + ' for 0 points.')
                
            self.roundScore[i] = points
            self.totalScore[i] += points
        
        self.printScore('Round')
        self.printScore('Total')        
                
    def scoreTrick(self, board, playOrder):
        
        suit = board.cards[0].suit
        winner = max([(Card.SUIT.index(c.suit), c.getRank(), hand) for c, hand in zip(board.cards, playOrder) if c.suit == suit or c.suit == 'S'])[2]
        self.tricksWon[self.hands.index(winner)] += 1
        
        print(board)
        print(winner.getName() + " took trick." )
        return winner

if __name__ == "__main__":
    
    #players = []    
    players = ['Al', 'Bob', 'Carol', 'Doug']
    spades = Spades(players)
    spades.playGame()
    
