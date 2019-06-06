# import gui
# from Hearts import Hearts
import pygame
from pygame.locals import *
import time 
from resource import *
from dataclasses import replace

class Event():
    def __init__(self):
        self.name = 'Generic Name'
 
class QuitEvent(Event):
    def __init__(self):
        self.name = "Program Quit Event"
 
class TickEvent(Event):
    def __init__(self):
        self.name = "CPU Tick Event"
 
class UserInputErrorEvent(Event):
    def __init__(self, message):
        self.name = "User Input Error"
        self.message = message

class CardSelectionRequestEvent(Event):
    def __init__(self, card, hand, selectedCards):
        self.name = 'Card Select Request'
        self.card = card
        self.hand = hand
        self.selectedCards = selectedCards
 
class CardSelectedEvent(Event):
    def __init__(self, card, hand, replacedCard):
        self.name = 'Card Selected'
        self.card = card
        self.hand = hand
        self.replacedCard = replacedCard
 
class CardPlayRequestEvent(Event):
    def __init__(self, hand, selectedCards):
        self.name = 'Card Play Request'
        self.hand = hand
        self.selectedCards = selectedCards
 
class CardPlayedEvent(Event):
    def __init__(self, hand, card, nextHand):
        self.name = 'Card Played'
        self.hand = hand
        self.card = card
        self.nextHand = nextHand
         
class PassCompleteEvent(Event):
    def __init__(self):
        self.name = 'Pass Complete'
 
class PassCompleteAcceptanceRequestEvent(Event):
    def __init__(self):
        self.name = 'Pass Complete Acknowledgement Request'
        
class TrickAcceptanceRequestEvent(Event):
    def __init__(self):
        self.name = 'Trick Acceptance Request'
                 
class TrickCompleteEvent(Event):
    def __init__(self, winner):
        self.name = 'Trick Complete'
        self.winner = winner
 
class TrickInitializedEvent(Event):
    def __init__(self, playOrder, nextHand):
        self.name = 'Trick Initialized'
        self.playOrder = playOrder
        self.nextHand = nextHand
 
class RoundCompleteEvent(Event):
    def __init__(self):
        self.name = 'Round Complete'
 
class RoundInitializedEvent(Event):
    def __init__(self):
        self.name = 'Round Initialized'
 
class GameCompleteEvent(Event):
    def __init__(self):
        self.name = 'Game Complete'
 
class GameInitializedEvent(Event):
    def __init__(self, hands, board):
        self.name = 'Game Initialized'
        self.hands = hands
        self.board = board
 
 
class BoardSelectedEvent(Event):
    def __init__(self, board):
        self.name = 'Board Selected'
        self.board = board
 
# 
# 
class EventManager():
    def __init__(self):
        self.listeners = []
        self.eventQueue = []
        self.eventHistory = []
        
    def registerListener(self, listener):
        if listener not in self.listeners:
            self.listeners.append(listener)
 
    def unRegisterListener(self, listener):
        self.listeners.remove(listener)
    
    def processEvents(self):
        while len(self.eventQueue) > 0:
            start = time.time()
            event = self.eventQueue[0]
            for listener in self.listeners:
                listener.notify(event) 
            self.eventQueue.pop(0)
            end = time.time()
            print('Event: %s %f' % (event.name, end-start))
        
    def post(self, event):
        
        queueLength = len(self.eventQueue)
        self.eventQueue.append(event)
        self.eventHistory.append(event)
        if queueLength == 0:
            self.processEvents()

 

class CPUSpinnerController:
    """..."""
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener( self )

        self.keepGoing = 1

    #----------------------------------------------------------------------
    def Run(self):
        while self.keepGoing:
            event = TickEvent()
            self.evManager.Post( event )

    #----------------------------------------------------------------------
    def Notify(self, event):
        if isinstance( event, QuitEvent ):
            #this will stop the while loop from running
            self.keepGoing = False


 
class UIGameController():
    def __init__(self, model, view, evManager):
        self.model = model
        self.view = view
        self.evManager = evManager
# 
#    def notify(self, event):
    def processGUIEvents(self, events):
#        if isinstance(event, TickEvent):
        for event in events:
#            for event in pygame.event.get():
                 
            if event.type == QUIT:
                self.evManager(QuitEvent())
                 
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.model.gameStatus == 'AwaitingPlay':
                    self.evManager.post(TrickAcceptanceRequestEvent())

                if self.model.gameStatus == 'PassCards' and self.model.isPassComplete:
                    self.evManager.post(PassCompleteAcceptanceRequestEvent())
                    
                pos = pygame.mouse.get_pos()
                
                #See if any cards selected
                for handWIDGET in self.view.handWIDGETS:
                    selectedCards = handWIDGET.cardWIDGETS.get_sprites_at(pos)
                    if selectedCards:
                        if self.model.gameStatus == 'PassCards' and handWIDGET.hand.passComplete:
                            continue
                        
                        card = selectedCards[-1].card
                        self.evManager.post(CardSelectionRequestEvent(card, handWIDGET.hand, handWIDGET.getSelectedCards()))
                        return True

                #User select board to acknowledge trick, pass cards
                rect = Rect(155, 155, 490, 290)
                if rect.collidepoint(pos):
                    for handWIDGET in self.view.handWIDGETS:
                        if handWIDGET.getSelectedCards():
                            if self.model.gameStatus == 'PassCards':
                                if not handWIDGET.hand.passComplete:
                                    ev = CardPlayRequestEvent(handWIDGET.hand, handWIDGET.getSelectedCards())
                                    self.evManager.post(ev)         
                            
                            if self.model.gameStatus == 'AwaitingPlay':
                                ev = CardPlayRequestEvent(handWIDGET.hand, handWIDGET.getSelectedCards())
                                self.evManager.post(ev)         
                                
        return True
     
