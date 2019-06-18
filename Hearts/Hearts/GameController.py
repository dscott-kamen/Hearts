# import gui
# from Hearts import Hearts
import pygame
from pygame.locals import *
import time 
from resource import *
from Client import RECT_LOOKUP
from Client import *
import copy

class Event():
    def __init__(self):
        self.name = 'Generic Name'

class QuitEvent(Event):
    def __init__(self):
        Event.__init__(self)
        self.name = "Program Quit Event"
 
class TickEvent(Event):
    def __init__(self):
        Event.__init__(self)
        self.name = "CPU Tick Event"
 
class UserInputErrorEvent(Event):
    def __init__(self, message):
        Event.__init__(self)
        self.name = "User Input Error"
        self.message = message

class UserEvent(Event):
    def __init__(self):
        Event.__init__(self)
         
class CardSelectionRequestEvent(UserEvent):
    def __init__(self, handPosition, card):
        Event.__init__(self)
        self.name = 'Card Select Request'
        self.handPosition = handPosition
        self.card = card
 
class CardPlayRequestEvent(UserEvent):
    def __init__(self, handPosition, selectedCards):
        Event.__init__(self)
        self.name = 'Card Play Request'
        self.handPosition = handPosition
        self.selectedCards = selectedCards


class PassCompleteAcceptanceRequestEvent(UserEvent):
    def __init__(self, handPosition):
        Event.__init__(self)
        self.name = 'Pass Complete Acknowledgement Request'
        self.handPosition = handPosition

class GameUpdateRequestEvent(Event):
    def __init__(self):
        Event.__init__(self)
        self.name = 'Game Update Request'
    

class GameUpdateEvent():
    def __init__(self, game):
        Event.__init__(self)
        self.name = 'Game Update'
        self.game = game
        
class TrickAcceptanceRequestEvent(UserEvent):
    def __init__(self):
        Event.__init__(self)
        self.name = 'Trick Acceptance Request'
                 
         
class CardSelectedEvent(Event):
    def __init__(self, hand, card, game):
        Event.__init__(self)
        self.name = 'Card Selected'
        self.hand = hand
        self.card = card
        self.game = game
 
class CardPlayedEvent(Event):
    def __init__(self, hand, cards, game):
        Event.__init__(self)
        self.name = 'Card Played'
        self.hand = hand
        self.cards = cards
        self.game = game
         
class TrickCompleteEvent(Event):
    def __init__(self, winner, game):
        Event.__init__(self)
        self.name = 'Trick Complete'
        self.winner = winner
        self.game = game
 
class EventManager():
    def __init__(self):
        self.listeners = []
        self.eventQueue = []
        self.eventHistory = []
        self._locked = False
        self._lockKey = None
        self._quit = False
        
    
    def lock(self, lockKey):
        if not self._locked:
            self._locked = True
            self._lockKey = lockKey

    def unlock(self, lockKey):
        if self._locked and self._lockKey == lockKey:
            self._locked = False
            self._lockKey = None
    
    def shutdown(self):
        self._quit = True
        
    
    def registerListener(self, listener):
        if listener not in self.listeners:
            self.listeners.append(listener)
 
    def unRegisterListener(self, listener):
        self.listeners.remove(listener)
    
    def processEvents(self):
        while 1:
            if self._quit:
                break
            
            if len(self.eventQueue) > 0 and not self._locked:
                start = time.time()
                event = self.eventQueue[0]
                for listener in self.listeners:
                    listener.notify(event) 
                self.eventQueue.pop(0)
                end = time.time()
                print('Event: %s %f' % (event.name, end-start))
            time.sleep(.005)
        
    def post(self, event):
        
        self.eventQueue.append(event)
        self.eventHistory.append(event)


 

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


 


class GameController():
    def __init__(self, game, ui, evManager):
        self.ui = ui
        self.game = game
        self.evManager = evManager
        self.evManager.registerListener(self)

        self.seatLabels = ['Bottom', 'Left', 'Top', 'Right']
        self.rotation = [0, -90, 0, 90]

        self.ui.notificationAreaWIDGET.setMessage("Retrieving game info...")
        self.getGameUpdate()
            
    def notify(self, event):

        if isinstance(event, UserEvent):
            self.processUserEvent()
 
        if isinstance(event, UserInputErrorEvent):
            self.processUserInputError(event.message)
 
        if isinstance(event, CardSelectedEvent):
            self.selectCard(event.hand, event.card, event.game)
 
        elif isinstance(event, CardPlayedEvent):
            self.playCard(event.hand, event.cards, event.game)
         
        elif isinstance(event, GameUpdateEvent):
            self.updateGame(event.game)
             
        elif isinstance(event, TrickCompleteEvent):
            self.finalizeTrick(event.winner, event.game)
 
    def finalizeTrick(self, winner, game):
        self.game = game
        #Trigger trickwinner automation
        self._animateTrickWinner(winner)
        self._buildWIDGETS()
    
    def getGameUpdate(self):
        self.evManager.post(GameUpdateRequestEvent())
        
    def isAnimationActive(self, animationType):
        return [anima for anima in self.ui.animations if anima.animationType == animationType]

    def playCard(self, playedHand, playedCards, game):
        self.game = game
        
        #Trigger playcard animation 
        if game.gameStatus == 'AwaitingPlay':
            handWIDGET = self._getHandWIDGET(playedHand)
            cardWIDGET = self._getCardWIDGET(handWIDGET, playedCards)
            self._animatePlayCard(handWIDGET, cardWIDGET)

        #Rebuild widgets
        self._buildWIDGETS()
            
    def processUserEvent(self):
        self.ui.notificationAreaWIDGET.clearMessage()

    def processUserInputError(self, message):
        self.ui.notificationAreaWIDGET.setMessage(message)
              
    def selectCard(self, hand, card, game):
        self.game = game

        #Rebuild widgets
        self._buildWIDGETS()
                             
    def updateGame(self, game):
        if self.ui.currentPosition < 0:
            self._initializePosition(game) 
            self.ui.notificationAreaWIDGET.setMessage('')
        
        self.game = game
        
        #if this is a pass complete update, lock event processing until pass acknowledged
        if self.game.gameStatus == 'PassCards' and self.game.isPassComplete:
            self.evManager.lock('PassCards')
            
        self._buildWIDGETS()
        self.ui.redraw()
        
    def _animatePlayCard(self, handWIDGET, cardWIDGET):        
        
        if self.ui.gameInitialized:
            self.evManager.lock("playCard")
            
            #get start rect
            if handWIDGET.seatLabel == 'Bottom':
                startRect = cardWIDGET.rect
            else:
                rect = RECT_LOOKUP[('TopLevel', ('Hand', handWIDGET.seatLabel))]
                startRect = cardWIDGET.image.get_rect(center=rect.center)
                
            boardRect = self.ui.boardWIDGET._getCardRect(handWIDGET.seatLabel)
            endRect = get_absolute_rect(boardRect, RECT_LOOKUP[('TopLevel','Board')])
            moveSpeed = 25
            redrawWIDGETS = [handWIDGET, self.ui.boardWIDGET, self.ui.notificationAreaWIDGET]
            self.ui.animations.append(Animation('PlayCard', cardWIDGET.image, moveSpeed, startRect, endRect, redrawWIDGETS, self._animatePlayCardCallback))

    def _animatePlayCardCallback(self, anima):
        for cardWIDGET in self.ui.boardWIDGET.cardWIDGETS:
            cardWIDGET.visible = True
        self.ui.boardWIDGET.redraw()
        if len(self.game.board.cards) < 4:
            self.evManager.unlock("playCard")

    def _animateTrickWinner(self, winner):
        if self.ui.gameInitialized:
            self.evManager.lock("trickWinner")
            handWIDGET = self._getHandWIDGET(winner)
            cardWIDGET = self.ui.boardWIDGET._getCard(handWIDGET.seatLabel)
            scoreAreaWIDGET = self._getScoreAreaWIDGET(winner)

            startRect, endRect = self._getTrickWinnerAnimationRects(handWIDGET.seatLabel)
            moveSpeed = 25
            redrawWIDGETS = [handWIDGET, scoreAreaWIDGET, self.ui.notificationAreaWIDGET]
            self.ui.animations.append(Animation('TrickWinner', cardWIDGET.image, moveSpeed, startRect, endRect, redrawWIDGETS, self._animateTrickWinnerCallback))

    def _animateTrickWinnerCallback(self, anima):
        for widget in anima.redrawWIDGETS:
            widget.redraw()
        self.evManager.unlock("trickWinner")

    def _applyPassLock(self, hand, handWIDGET, cardWIDGETS):
        if self.game.gameStatus == 'PassCards' and handWIDGET.seatLabel == 'Bottom':
            for cardWIDGET in cardWIDGETS:
                if cardWIDGET.card in hand.passedCards:
                    cardWIDGET.highlighted = True
                    cardWIDGET.selected = True

    def _applyPassComplete(self, hand, handWIDGET, cardWIDGETS):
        if self.game.gameStatus == 'PassCards' and self.game.isPassComplete and handWIDGET.seatLabel == 'Bottom':
            for cardWIDGET in cardWIDGETS:
                if cardWIDGET.card in hand.receivedCards:
                    cardWIDGET.highlighted = True

    def _applySelectCards(self, hand, cardWIDGETS):
        for cardWIDGET in cardWIDGETS:
            if cardWIDGET.card in hand.selectedCards:
                cardWIDGET.selected = True

    def _buildBoard(self):
        self.ui.boardWIDGET.cardWIDGETS = self._buildBoardCardWIDGETS()
        self.ui.boardWIDGET.setPlayOrder(self._getSeatOrder())
        
    def _buildBoardCardWIDGETS(self):
        cardWIDGETS = []
        for i, card in enumerate(self.game.board.cards):
            
            visible = True
            if self.isAnimationActive('PlayCard'):
                #last card played is not visible until playcard animation completes
                if i == len(self.game.board.cards)-1:
                    visible = False
                    
            if self.isAnimationActive('TrickWinner'):
                visible = False
            
            cardWIDGETS.append(CardWIDGET(card, card.suit+card.value+'.png', visible=visible))
                
        return cardWIDGETS

    def _buildCardWIDGETS(self, hand):
        handWIDGET = self._getHandWIDGET(hand)
        showFront = handWIDGET.seatLabel == 'Bottom'
        
        cardWIDGETS = pygame.sprite.LayeredUpdates()
        for card in hand:
            cardWIDGET = CardWIDGET(card, card.suit+card.value+'.png', showFront=showFront, rotation=handWIDGET.rotation)
            cardWIDGETS.add(cardWIDGET)

        self._applySelectCards(hand, cardWIDGETS)        
        self._applyPassLock(hand, handWIDGET, cardWIDGETS)
        self._applyPassComplete(hand, handWIDGET, cardWIDGETS)
        
        return cardWIDGETS

    def _buildHandArea(self, hand):
        handWIDGET = self._getHandWIDGET(hand)
        handWIDGET.cardWIDGETS = self._buildCardWIDGETS(hand)

    def _buildScoreArea(self, hand):
        scoreAreaWIDGET = self._getScoreAreaWIDGET(hand)
        currentHand = self.game.getTurn()
        
        if self.game.gameStatus == 'AwaitingPlay' and currentHand is not None and currentHand.position == hand.position:
            scoreAreaWIDGET.colorLabel = 'scoreAreaCurrentTurnColor'
        else:
            scoreAreaWIDGET.colorLabel = 'scoreAreaColor'
        
        if hand.player is not None:
            scoreAreaWIDGET.nameText = hand.player.name
        scoreAreaWIDGET.scoreText = self._getScoreText(hand)

    def _buildWIDGETS(self):
        if self.ui.gameInitialized:
            for hand in self.game.hands:
                self._buildHandArea(hand)
                self._buildScoreArea(hand)
            self._buildBoard()
        
        
    def _getCardWIDGET(self, handWIDGET, card):
        for cardWIDGET in handWIDGET.cardWIDGETS:
            if cardWIDGET.card == card:
                return cardWIDGET
        return None
        
    def _getHand(self, handWIDGET):
        idx = self.seatLabels.index(handWIDGET.seatLabel)
        return self.game.hands[(idx + self.ui.currentPosition)%4]
    
    def _getHandWIDGET(self, hand):
        idx = (hand.position - self.ui.currentPosition + 4)%4 
        return self.ui.handWIDGETS[idx]

    def _getScoreAreaWIDGET(self, hand):
        idx = (hand.position - self.ui.currentPosition + 4)%4 
        return self.ui.scoreAreaWIDGETS[idx]

    def _getScoreText(self, hand):
        return 'Score: %d (%d)' % (hand.score.gameScore, hand.score.roundScore)

    def _getSeatOrder(self):
        hand = self.game.getPlayOrder()[0]
        idx = (hand.position - self.ui.currentPosition + 4)%4 
        lookup = self.seatLabels + self.seatLabels
        return lookup[idx:idx+4]

    def _getTrickWinnerAnimationRects(self, seatLabel):
        topLevelRect = RECT_LOOKUP[('TopLevel', 'TopLevel')]
        cardWidth = SCR_ATTR['cardWidth']
        cardHeight = SCR_ATTR['cardHeight']
        x = topLevelRect.width/2 - cardWidth/2
        y = topLevelRect.height/2 - cardHeight/2
        startRect = Rect(x, y, cardWidth, cardHeight)
        
        if seatLabel == 'Top':
            y = 0
        elif seatLabel == 'Bottom':
            y = topLevelRect.bottom - cardHeight
        elif seatLabel == 'Left':
            x = 0
        elif seatLabel == 'Right':
            x = topLevelRect.right - cardWidth
        endRect = Rect(x, y, cardWidth, cardHeight)

        return startRect, endRect

    def _initializePosition(self, game):
        #find out position of hand in game
        for i, hand in enumerate(game.hands):
            if hand.player is not None and hand.player.name == self.ui.player.name:
                self.ui.currentPosition = i
                break
        self.ui.gameInitialized = True 
    
    def processGUIEvents(self, events):
#        if isinstance(event, TickEvent):
        for event in events:
#            for event in pygame.event.get():
                 
            if event.type == QUIT:
                return False
                 
            elif event.type == pygame.MOUSEBUTTONUP:
                handWIDGET = self.ui.handWIDGETS[0]
                hand = self._getHand(handWIDGET)
                pos = pygame.mouse.get_pos()

                if self.game.gameStatus == 'AwaitingPlay':
                    if len(self.game.board.cards) == 4:
                        self.evManager.unlock("playCard")

                if self.game.isPassComplete and self.game.gameStatus == 'PassCards':
                    self.evManager.unlock("PassCards")
                    
                #See if any cards selected
                selectedCards = handWIDGET.cardWIDGETS.get_sprites_at(pos)
                if selectedCards:
                    if self.game.gameStatus == 'PassCards' and hand.passStatus != 'Initiated':
                        continue
                        
                    card = selectedCards[-1].card
                    self.evManager.post(CardSelectionRequestEvent(hand.position, card))
                    return True

                #User select board to acknowledge trick, pass cards
                rect = Rect(155, 155, 490, 290)
                if rect.collidepoint(pos):
                    if hand.selectedCards:
                        if ((self.game.gameStatus == 'PassCards' and hand.passStatus == 'Initiated') 
                                or (self.game.gameStatus == 'AwaitingPlay')):
                            ev = CardPlayRequestEvent(hand.position, hand.selectedCards)
                            self.evManager.post(ev)         
                                
        return True
