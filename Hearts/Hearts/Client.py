import os, pygame
from Hearts import Hearts
from GameController import *
from Deck import Card
from resource import *

SCR_ATTR = {
            'tableTopColor': (55, 166, 51),
            'rectangleColor' : (255, 0, 0),
            'scoreAreaColor' : (0, 64, 255),
            'scoreAreaCurrentTurnColor' : (135, 206, 250),
            'font' : 'arial',
            'notificationAreaColor' : (248, 255, 131),
            'cardHeight' : 105,
            'cardWidth' : 70,
            'handSpacing' : 40,
            'cardSpacing' : 10,
            'scoreAreaHeight' : 40,
            'topLevelWidth' : 800,
            'topLevelHeight' : 600,
            'notificationPadding' : (20,5),
            'notificationHeight' : 20,
            'cardSelectionSpacing' : 30}

RECT_LOOKUP = {}
SURFACE_LOOKUP = {}

class NotificationWIDGET(pygame.Surface):
    def __init__(self):
        rect = RECT_LOOKUP[('TopLevel', 'NotificationArea')]
        pygame.Surface.__init__(self, rect.size)
        self.fill(SCR_ATTR['notificationAreaColor'])

        
        self._message = 'This is a notification test to see how much information I can put into a single line of text and what happens if that amount is exceeded.'
        self._changed = True
    
    def draw(self):
        if self.hasChanged():
            #clear existing text
            self.fill(SCR_ATTR['notificationAreaColor'])
            
            #create new text
            font = pygame.font.SysFont(SCR_ATTR['font'], 12)
            text = font.render(self._message, 0, (10, 10, 10))
            rect = self.get_rect(topleft=(5, 2))
            self.blit(text, rect)        
            self._setChanged(False)

    def clearMessage(self):
        self.setMessage('')
    
    def hasChanged(self):
        return self._changed
    
    def setMessage(self, message):
        self._setChanged(True)
        self._message = message
        
    def redraw(self):
        self._setChanged(True)

    def _setChanged(self, value):
        self._changed = True
    

        
class CardWIDGET(pygame.sprite.Sprite):
    def __init__(self, card, rotation=0):
        pygame.sprite.Sprite.__init__(self)
        
        self.card = card
        self.rect = Rect(0,0,0,0)
        self.relativeRect = Rect(0,0,0,0)
        self.image = load_image('%s%s.png' % (card.suit, card.value), size = (SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight']))
        self.image = pygame.transform.rotate(self.image, rotation)
        
    def getRelativeRect(self):
        return self.relativeRect

    def setRect(self, rect):
        self.rect = rect
        
    def setRelativeRect(self, rect):
        self.relativeRect = rect

        
class ScoreAreaWIDGET(pygame.Surface):
    def __init__(self, seatLabel, hand):
        rect = RECT_LOOKUP['TopLevel', ('ScoreArea', seatLabel)]
        pygame.Surface.__init__(self, rect.size)
        
        self.seatLabel = seatLabel
        self.hand = hand
        self.currentTurn = False

        self._changed = True
    
    def draw(self):
        if self._changed:
            self.fill((self._getScoreAreaColor()))
            
            rect = RECT_LOOKUP[('TopLevel', ('ScoreArea', self.seatLabel))]
            pygame.draw.rect(self, SCR_ATTR['rectangleColor'], self.get_rect(), 1)
        
            #create name text
            text, rect = self._createNameText()    
            self.blit(text, rect)
        
            #create score text
            text, rect = self._createScoreText()            
            self.blit(text, rect)

        self._changed = False

    def hasChanged(self):
        return self._changed

    def redraw(self):
        self._changed = True
            
    def setCurrentTurn(self, currentTurn):
        self.currentTurn = currentTurn
        self._changed = True

    def _createNameText(self):
        font = pygame.font.SysFont(SCR_ATTR['font'], 24)
        text = font.render(self.hand.getName(), 1, (10, 10, 10))
        return self._transformNameText(text)
    
    def _createScoreText(self):
        font = pygame.font.SysFont(SCR_ATTR['font'], 18)
        text = font.render('Score: %d (%d)' % (self.hand.score.gameScore ,self.hand.score.roundScore), 1, (10, 10, 10))
        return self._transformScoreText(text)
    
    def _getCardRotation(self):
        if self.seatLabel == 'Right':
            return 90
        elif self.seatLabel == 'Left':
            return -90
        else:
            return 0

    def _getScoreAreaColor(self):
            if self.currentTurn:
                return SCR_ATTR['scoreAreaCurrentTurnColor']
            else:
                return SCR_ATTR['scoreAreaColor']
        
    def _transformNameText(self, text):
        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            return text, text.get_rect(midleft=(5,self.get_rect().height/2))
        elif self.seatLabel == 'Left':
            text = pygame.transform.rotate(text, self._getCardRotation())
            return text, text.get_rect(midtop=(self.get_rect().width/2, 5))
        elif self.seatLabel == 'Right':
            text = pygame.transform.rotate(text, self._getCardRotation())
            return text, text.get_rect(midbottom=(self.get_rect().width/2, self.get_rect().height - 5))

    def _transformScoreText(self, text):
        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            return text, text.get_rect(midright=(self.get_rect().width - 5, self.get_rect().height/2))
        elif self.seatLabel == 'Right':
            text = pygame.transform.rotate(text, self._getCardRotation())
            return text, text.get_rect(midtop=(self.get_rect().width/2, 5))
        elif self.seatLabel == 'Left':
            text = pygame.transform.rotate(text, self._getCardRotation())
            return text, text.get_rect(midbottom=(self.get_rect().width/2, self.get_rect().height - 5))
 

class Animation():
    def __init__(self, animationType, widget, moveSpeed, startRect, endRect=None):
        self.animationType = animationType
        self.WIDGET = widget
        self.currentPos = startRect.topleft  
        self.startPos = startRect.topleft
        self.endPos = endRect.topleft
        self.moveXY = calculateMoveXY(startRect, endRect, moveSpeed)
    
    def getRect(self):
        return Rect(self.currentPos + self.WIDGET.get_rect().size)
    
    def isMoveComplete(self):
        x, y = self.moveXY
        currentx, currenty = self.currentPos
        endx, endy = self.endPos
        xDiff, yDiff = endx - currentx, endy - currenty
        
        xReached = (x >= 0 and xDiff<=0) or (x < 0 and xDiff > 0)
        yReached = (y >= 0 and yDiff<=0) or (y < 0 and yDiff > 0)
        
        return xReached and yReached
    
    def move(self):
        x,y = self.moveXY
        curX, curY = self.currentPos
        curX += x 
        curY += y
        self.currentPos = curX, curY
        return self.getRect()
    

class HandWIDGET(pygame.Surface):
    def __init__(self, seatLabel, hand):

        self.parentRect = RECT_LOOKUP[('TopLevel', ('Hand', seatLabel))]
        pygame.Surface.__init__(self, self.parentRect.size)
        self.fill(SCR_ATTR['tableTopColor'])

        self.hand = hand 
        self.cardWIDGETS = pygame.sprite.LayeredUpdates()
        self.seatLabel = seatLabel
        self.selectedCards = []

        self._changed = False        
        self._passedCards = []
        
    def draw(self):
        
        print('ReceivedCard: %d' % len(self.hand.receivedCards))
        if self.hasChanged():
            rect = RECT_LOOKUP[(('Hand', self.seatLabel), 'Rectangle')]
            pygame.draw.rect(self, SCR_ATTR['rectangleColor'], rect, 1)

            spacing = self._getCardSpacing(self._getSpanRange(), len(self.hand.cards))        
            notSelectedRect = RECT_LOOKUP[(('Hand', self.seatLabel), 'CardNotSelected')]
            selectedRect = RECT_LOOKUP[(('Hand', self.seatLabel), 'CardSelected')]
        
            for i, card in enumerate(self.cardWIDGETS):
                cardRect = self._getCardRect(card, i, spacing, selectedRect, notSelectedRect)
                image = self._applyCardColor(card)
                self.blit(image, cardRect)
                
                #Functionality added to support mouse clicks on sprites
                card.setRect(get_absolute_rect(cardRect, self.parentRect))
                card.setRelativeRect(cardRect)
            
            self._setChanged(False)

    def getCardWIDGET(self, card):
        for cardWIDGET in self.cardWIDGETS:
            if cardWIDGET.card == card:
                return cardWIDGET
        return None

    def getSelectedCards(self):
        return self.selectedCards

    def hasChanged(self):
        return self._changed

    def notifyCardChange(self):
        self._setChanged(True)
        self._buildCards()
        
    def notifyCardPlayed(self):
        self.selectedCards.clear()
        self.notifyCardChange()
        
    def notifyCardPassLocked(self):
        self.redraw()
    
    def setPassComplete(self):
        self.selectedCards.clear()
        self.notifyCardChange()
        
    def redraw(self):
        self._setChanged(True)
        self._clearCardArea()
        
    def toggleSelectedCard(self, selectedCard, replacedCard):
        
        if replacedCard is not None:
            self.selectedCards.remove(replacedCard)
            
        if selectedCard in self.selectedCards:
            self.selectedCards.remove(selectedCard)
        else:
            self.selectedCards.append(selectedCard)

        self.redraw()

    def _applyCardColor(self, card):
        if ((self.hand.passStatus == 'Submitted' and card.card in self.selectedCards) or 
            (self.hand.passStatus == 'Submitted' and card.card in self.hand.getReceivedCards())):
            image = card.image.copy()
            image.fill((60, 60, 0, 0), special_flags=pygame.BLEND_SUB)
        else:
            image = card.image
        return image

    def _buildCards(self):
        #cleanup for removed widgets
        self._clearCardArea()

        self.cardWIDGETS.empty()
        rotation = self._getCardRotation()
        for card in self.hand.cards:
            cardWIDGET = CardWIDGET(card, rotation)
            self.cardWIDGETS.add(cardWIDGET)

    def _clearCardArea(self):
        background = SURFACE_LOOKUP['Background']
        self.blit(background, self.get_rect())
        
    def _getCardRect(self, card, cardIndex, spacing, selectedRect, notSelectedRect):
        if card.card in self.selectedCards:
            rect = selectedRect.copy()
        else:
            rect = notSelectedRect.copy()

        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            rect.left = rect.left + cardIndex * spacing
        elif self.seatLabel == 'Left':
            rect.top = rect.top + cardIndex * spacing
        elif  self.seatLabel == 'Right':
            rect.bottom = rect.bottom - cardIndex * spacing - SCR_ATTR['cardWidth']
        return rect

    def _getCardRotation(self):
        if self.seatLabel == 'Right':
            return 90
        elif self.seatLabel == 'Left':
            return -90
        else:
            return 0

    def _getCardSpacing(self, spanRange, cardCount):
        if cardCount == 1 or spanRange > cardCount * (SCR_ATTR['cardWidth'] + SCR_ATTR['cardSpacing']):
            return SCR_ATTR['cardWidth'] + 0.5 * SCR_ATTR['cardSpacing']
        else:
            return int((spanRange - SCR_ATTR['cardWidth'] - 0.5 * SCR_ATTR['cardSpacing'])//(cardCount - 1))

    def _getSpanRange(self):
        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            return self.parentRect.width
        else:
            return self.parentRect.height

    def _setChanged(self, value):
        self._changed = value
            
class BoardWIDGET(pygame.Surface):
    def __init__(self, gui, board, seatAssignment, evManager):
        rect = RECT_LOOKUP[('TopLevel', 'Board')]
        pygame.Surface.__init__(self, rect.size)
        self.fill(SCR_ATTR['tableTopColor'])
        
        self.board = board
        self.seatAssignment = seatAssignment
        self.cardWIDGETS = []
        self.playOrder = []
        self.playCardAnimation = False

        self._changed = True
            
    def _clearBoard(self):
        background = SURFACE_LOOKUP['Background']
        self.blit(background, self.get_rect())

    def draw(self):
        
        if self.hasChanged():
            self._clearBoard()
            
            for i, (card, hand) in enumerate(zip(self.board.cards, self.playOrder)):                

                if self.playCardAnimation and i >= len(self.board.cards) - 1:
                    continue
                cardWIDGET = CardWIDGET(card)
                self.blit(cardWIDGET.image, self.getCardRect(hand))
            self._setChanged(False)

    def getCard(self, hand):
        idx = self.playOrder.index(hand)
        return self.board.cards[idx]
        
    def getCardRect(self, hand):    
        seatLabel = self.seatAssignment[hand.getName()]
        return RECT_LOOKUP[('Board', seatLabel)]
     
    def hasChanged(self):
        return self._changed
     
    def redraw(self):
        self._setChanged(True)
        
    def setPlayOrder(self, playOrder):
        self.playOrder = playOrder
        
    def _setChanged(self, value):
        self._changed = value

        
class Gui():
    def __init__(self, evManager):
        self.initializeRects()
        self.seatLabels = ['Bottom', 'Left', 'Top', 'Right']
        self.handWIDGETS = []
        self.scoreAreaWIDGETS = []
        self.animations = []
        self.evManager = evManager
        self.evManager.registerListener(self)

        #Draw initial screen
        self.initializeBackground()        
        self.preloadCardImages()
        
    def notify(self, event):

        if isinstance(event, UserEvent):
            self.notificationAreaWIDGET.clearMessage()

        if isinstance(event, UserInputErrorEvent):
            self.notificationAreaWIDGET.setMessage(event.message)

        if isinstance(event, GameInitializedEvent):
            self.initializeGame(event.hands, event.board)            
        
        elif isinstance(event, CardSelectedEvent):
            handWIDGET = self._getHandWIDGET(event.hand)
            handWIDGET.toggleSelectedCard(event.card, event.replacedCard)

        elif isinstance(event, CardPlayedEvent):
            #Board update
            self.boardWIDGET.redraw()

            #Score Area - update turn from played card
            scoreAreaWIDGET = self._getScoreAreaWIDGET(event.hand)
            scoreAreaWIDGET.setCurrentTurn(False)

            #Score Area - update turn from currentTurn
            if event.nextHand is not None:
                scoreAreaWIDGET = self._getScoreAreaWIDGET(event.nextHand)
                scoreAreaWIDGET.setCurrentTurn(True)
            
            #Trigger playcard animation
            self.animatePlayCard(event.hand, event.card)

            #Hand Area - update played card
            handWIDGET = self._getHandWIDGET(event.hand)
            handWIDGET.notifyCardPlayed()
            
        elif isinstance(event, CardPassLockEvent):
            handWIDGET = self._getHandWIDGET(event.hand)
            handWIDGET.notifyCardPassLocked()
            
        elif isinstance(event, TrickInitializedEvent):
            self.boardWIDGET.setPlayOrder(event.playOrder)
            self.boardWIDGET.redraw()

            scoreAreaWIDGET = self._getScoreAreaWIDGET(event.nextHand)
            scoreAreaWIDGET.setCurrentTurn(True)

        elif isinstance(event, TrickCompleteEvent):
            
            #Redraw to update scores
            scoreAreaWIDGET = self._getScoreAreaWIDGET(event.winner)
            scoreAreaWIDGET.redraw()
            
            #Trigger trickwinner automation
            self.animateTrickWinner(event.winner)

        elif isinstance(event, RoundInitializedEvent):
            for handWIDGET in self.handWIDGETS:
                handWIDGET.notifyCardChange()

        elif isinstance(event, RoundCompleteEvent):
            for scoreAreaWIDGET in self.scoreAreaWIDGETS:
                scoreAreaWIDGET.redraw()
                
        elif isinstance(event, PassCompleteEvent):
            handWIDGET = self.getHandWIDGET(event.hand)
            handWIDGET.setPassComplete()

        elif isinstance(event, GameInitializedEvent):
            for scoreAreaWIDGET in self.scoreAreaWIDGETS:
                scoreAreaWIDGET.redraw()
    
    def _getScoreAreaWIDGET(self, hand):
        for scoreAreaWIDGET in self.scoreAreaWIDGETS:
            if scoreAreaWIDGET.hand == hand:
                return scoreAreaWIDGET

    def _getHandWIDGET(self, hand):
        for handWIDGET in self.handWIDGETS:
            if handWIDGET.hand == hand:
                return handWIDGET


    def animatePlayCard(self, hand, card):
        
        handWIDGET = self.getHandWIDGET(hand)
        cardWIDGET = handWIDGET.getCardWIDGET(card)

        self.boardWIDGET.playCardAnimation = True
        startRect = cardWIDGET.rect
        endRect = get_absolute_rect(self.boardWIDGET.getCardRect(hand), RECT_LOOKUP[('TopLevel','Board')])
        moveSpeed = 40
        self.animations.append(Animation('PlayCard', cardWIDGET.image, moveSpeed, startRect, endRect))
    
    def animateTrickWinner(self, winner):
        card = self.boardWIDGET.getCard(winner)
        cardWIDGET = CardWIDGET(card)
        
        seatLabel = self.seatAssignment[winner.getName()]
        startRect, endRect = self.getTrickWinnerAnimationRects(seatLabel)
        moveSpeed = 40
        self.animations.append(Animation('TrickWinner', cardWIDGET.image, moveSpeed, startRect, endRect))

    def clearAnimations(self):
        for anima in self.animations:
            if anima.animationType == 'PlayCard':
                
                rect = anima.getRect()
                background = SURFACE_LOOKUP['Background']
                cardBackground = background.subsurface(rect)
                pygame.display.get_surface().blit(cardBackground, rect)
            
                for handWIDGET in self.handWIDGETS:
                    handWIDGET.redraw()
            
            if anima.animationType == 'TrickWinner':
                
                rect = anima.getRect()
                background = SURFACE_LOOKUP['Background']
                cardBackground = background.subsurface(rect)
                pygame.display.get_surface().blit(cardBackground, rect)

                for hand in self.handWIDGETS:
                    hand.redraw()
                for scoreAreaWIDGET in self.scoreAreaWIDGETS:
                    scoreAreaWIDGET.redraw()
                    
    def draw(self):
        self.setAnimationRedraws()
        self.clearAnimations()
        self.drawBoard()        
        self.drawHands()
        self.drawScoreArea()
        self.drawNotification()
        self.drawAnimations()
        
        
        pygame.display.flip()

    def drawAnimations(self):
        for anima in self.animations:

            rect = anima.move()
            if not anima.isMoveComplete():
                pygame.display.get_surface().blit(anima.WIDGET, rect)
            else:
                self.animations.remove(anima)
                self.postAnimationProcessing(anima)


    def drawBoard(self):
        if self.boardWIDGET.hasChanged():
            self.boardWIDGET.draw()
            rect = RECT_LOOKUP[('TopLevel', 'Board')]
            pygame.display.get_surface().blit(self.boardWIDGET, rect)
        
    def drawHands(self):
        for hand in self.handWIDGETS:
            if hand.hasChanged():
                rect = RECT_LOOKUP[('TopLevel', ('Hand', hand.seatLabel))]
                hand.draw()
                pygame.display.get_surface().blit(hand, rect)
        
    def drawNotification(self):
        if self.notificationAreaWIDGET.hasChanged():
            self.notificationAreaWIDGET.draw()
            rect = RECT_LOOKUP[('TopLevel', 'NotificationArea')]
            pygame.display.get_surface().blit(self.notificationAreaWIDGET, rect)

    
    def drawScoreArea(self):
        for scoreArea in self.scoreAreaWIDGETS:
            if scoreArea.hasChanged():
                rect = RECT_LOOKUP[('TopLevel', ('ScoreArea', scoreArea.seatLabel))]        
                scoreArea.draw()
                pygame.display.get_surface().blit(scoreArea, rect)
        
    def getCardAreaHeight(self):
        return SCR_ATTR['cardHeight'] + SCR_ATTR['cardSpacing']
        
    def getHandWIDGET(self, hand):
        seatLabel = self.seatAssignment[hand.getName()]
        return self.handWIDGETS[self.seatLabels.index(seatLabel)]

    def getPadding(self):
        return self.getCardAreaHeight() + SCR_ATTR['scoreAreaHeight']
    
    def getTrickWinnerAnimationRects(self, seatLabel):
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

    def initializeBackground(self):
        
        #Open window and title
        rect = RECT_LOOKUP['TopLevel', 'TopLevel'] 
        screen = pygame.display.set_mode((rect.size))
        pygame.display.set_caption('Hearts')

        #Setup background
        background = pygame.Surface(rect.size)
        background.fill((SCR_ATTR['tableTopColor']))        
        SURFACE_LOOKUP['Background'] = background
        
        #Setup notification area
        self.notificationAreaWIDGET = NotificationWIDGET()
                
        screen.blit(background, rect)
        pygame.display.flip()

    def initializeGame(self, hands, board):
        
        self.seatAssignment = self.mapSeatAssignment(hands)

        for hand, seatLabel in zip(hands, self.seatLabels):
            handWIDGET = HandWIDGET(seatLabel, hand)
            self.handWIDGETS.append(handWIDGET)
            
            scoreAreaWIDGET = ScoreAreaWIDGET(seatLabel, hand)
            self.scoreAreaWIDGETS.append(scoreAreaWIDGET)
        
        self.boardWIDGET = BoardWIDGET(self, board, self.seatAssignment, self.evManager)

    def initializeRects(self):

        width = SCR_ATTR['topLevelWidth']
        height = SCR_ATTR['topLevelHeight']
        RECT_LOOKUP[('TopLevel', 'TopLevel')] = Rect(0, 0, width, height)

        x = self.getPadding()
        y = SCR_ATTR['scoreAreaHeight']
        width = SCR_ATTR['topLevelWidth'] - 2 * self.getPadding()
        height = self.getCardAreaHeight() + SCR_ATTR['cardSelectionSpacing']
        RECT_LOOKUP[('TopLevel', ('Hand', 'Top'))] = Rect(x, y, width, height)

        y = SCR_ATTR['topLevelHeight'] - self.getPadding() - SCR_ATTR['cardSelectionSpacing']
        RECT_LOOKUP[('TopLevel', ('Hand', 'Bottom'))] = Rect(x, y, width, height)

        y = 0
        height = SCR_ATTR['scoreAreaHeight']
        RECT_LOOKUP[('TopLevel', ('ScoreArea', 'Top'))] = Rect(x, y, width, height)
        
        y = SCR_ATTR['topLevelHeight'] - SCR_ATTR['scoreAreaHeight']
        RECT_LOOKUP[('TopLevel', ('ScoreArea', 'Bottom'))] = Rect(x, y, width, height)

        x = 0
        y = 0
        height = self.getCardAreaHeight()
        RECT_LOOKUP[(('Hand', 'Top'), 'Rectangle')] = Rect(x, y, width, height)
        
        y = SCR_ATTR['cardSelectionSpacing']
        RECT_LOOKUP[(('Hand', 'Bottom'), 'Rectangle')] = Rect(x, y, width, height)

        x = SCR_ATTR['scoreAreaHeight']
        y = self.getPadding()
        width = self.getCardAreaHeight() + SCR_ATTR['cardSelectionSpacing']
        height = SCR_ATTR['topLevelHeight'] - 2 * self.getPadding()         
        RECT_LOOKUP[('TopLevel', ('Hand', 'Left'))] = Rect(x, y, width, height)
        
        x = SCR_ATTR['topLevelWidth'] - self.getPadding() - SCR_ATTR['cardSelectionSpacing']
        RECT_LOOKUP[('TopLevel', ('Hand', 'Right'))] = Rect(x, y, width, height)

        x = 0
        width = SCR_ATTR['scoreAreaHeight']
        RECT_LOOKUP[('TopLevel', ('ScoreArea', 'Left'))] = Rect(x, y, width, height)
        
        x = SCR_ATTR['topLevelWidth'] - SCR_ATTR['scoreAreaHeight']
        RECT_LOOKUP[('TopLevel', ('ScoreArea', 'Right'))] = Rect(x, y, width, height)

        x = 0
        y = 0
        width = self.getCardAreaHeight()
        RECT_LOOKUP[(('Hand', 'Left'), 'Rectangle')] = Rect(x, y, width, height)

        x = SCR_ATTR['cardSelectionSpacing']
        RECT_LOOKUP[(('Hand', 'Right'), 'Rectangle')] = Rect(x, y, width, height)

        x = self.getPadding()
        y = x
        width = SCR_ATTR['topLevelWidth'] - 2*x
        height = SCR_ATTR['topLevelHeight'] - 2*y
        RECT_LOOKUP[('TopLevel','Board')] = Rect(x, y, width, height)


        cardWidth = SCR_ATTR['cardWidth']
        cardHeight = SCR_ATTR['cardHeight']
        cardSpaceHalf = SCR_ATTR['cardSpacing']/2
        cardSelectionOffset = cardSpaceHalf + SCR_ATTR['cardSelectionSpacing']
        
        RECT_LOOKUP[(('Hand', 'Top'), 'CardNotSelected')] = Rect(cardSpaceHalf, cardSpaceHalf, cardWidth, cardHeight)
        RECT_LOOKUP[(('Hand', 'Top'), 'CardSelected')] = Rect(cardSpaceHalf, cardSelectionOffset, cardWidth, cardHeight)
        RECT_LOOKUP[(('Hand', 'Bottom'), 'CardNotSelected')] = Rect(cardSpaceHalf, cardSelectionOffset, cardWidth, cardHeight)
        RECT_LOOKUP[(('Hand', 'Bottom'), 'CardSelected')] = Rect(cardSpaceHalf, cardSpaceHalf, cardWidth, cardHeight)
        RECT_LOOKUP[(('Hand', 'Left'), 'CardNotSelected')] = Rect(cardSpaceHalf, cardSpaceHalf, cardHeight, cardWidth)
        RECT_LOOKUP[(('Hand', 'Left'), 'CardSelected')] = Rect(cardSelectionOffset, cardSpaceHalf, cardHeight, cardWidth)
        y = SCR_ATTR['topLevelHeight'] - 2 * self.getPadding() - cardSpaceHalf
        RECT_LOOKUP[(('Hand', 'Right'), 'CardSelected')] = Rect(cardSpaceHalf, y, cardHeight, cardWidth)
        RECT_LOOKUP[(('Hand', 'Right'), 'CardNotSelected')] = Rect(cardSelectionOffset, y, cardHeight, cardWidth)
      
        boardWidth = SCR_ATTR['topLevelWidth'] - 2 * self.getPadding()
        boardHeight = SCR_ATTR['topLevelHeight'] - 2 * self.getPadding()      
        x = boardWidth/2 - cardWidth/2
        y = boardHeight/2 - cardHeight/2 - cardHeight/2 - 2 * cardSpaceHalf
        RECT_LOOKUP[('Board', 'Top')] = Rect(x, y, cardWidth, cardHeight)
        
        y = boardHeight/2 - cardHeight/2 + cardHeight/2 + 2 * cardSpaceHalf
        RECT_LOOKUP[('Board', 'Bottom')] = Rect(x, y, cardWidth, cardHeight)

        x =  boardWidth/2 - cardWidth/2 - cardWidth - 2*cardSpaceHalf
        y = boardHeight/2 - cardHeight/2
        RECT_LOOKUP[('Board', 'Left')] = Rect(x, y, cardWidth, cardHeight)
        
        x = boardWidth/2 - cardWidth/2 + cardWidth + 2*cardSpaceHalf        
        RECT_LOOKUP[('Board', 'Right')] = Rect(x, y, cardWidth, cardHeight)
        
        notifx, notify = SCR_ATTR['notificationPadding']
        x, y = self.getPadding() + notifx, self.getPadding() + notify
        width = SCR_ATTR['topLevelWidth'] - 2 * notifx - 2 * self.getPadding()
        height = SCR_ATTR['notificationHeight']
        RECT_LOOKUP[('TopLevel','NotificationArea')] = Rect(x, y, width, height)
        
    def mapSeatAssignment(self, hands):
        
        seatAssignment = {}
        for hand,seatLabel in zip(hands, self.seatLabels):
            seatAssignment[hand.getName()] = seatLabel
        return seatAssignment

    def postAnimationProcessing(self, anima):

        if anima.animationType == 'PlayCard':
            
            self.boardWIDGET.playCardAnimation = False
            self.boardWIDGET.redraw()

        if anima.animationType == 'TrickWinner':

            for HandWIDGET in self.handWIDGETS:
                HandWIDGET.changed = True
            for scoreAreaWIDGET in self.scoreAreaWIDGETS:
                scoreAreaWIDGET.changed = True

    def preloadCardImages(self):
        for suit in Card.SUIT:  
            for value in Card.VALUE:
                load_image('%s%s.png' % (suit, value))

    def setAnimationRedraws(self):
        for anima in self.animations:
            if anima.animationType == 'PlayCard':
                for handWIDGET in self.handWIDGETS:
                    handWIDGET.changed = True
                self.boardWIDGET.changed = True
            
            if anima.animationType == 'TrickWinner':
                
                for hand in self.handWIDGETS:
                    hand.changed = True
                for scoreAreaWIDGET in self.scoreAreaWIDGETS:
                    scoreAreaWIDGET.changed = True

    def update(self):
        pass



def main():
    """this function is called when the program starts.
       it initializes everything it needs, then runs in
       a loop until the function returns."""

    pygame.init()

    players = ['Al', 'Bob', 'Carol', 'Doug']
    evManager = EventManager()
    gui = Gui(evManager)
    hearts = Hearts(players, evManager)
    controller = UIGameController(hearts, gui, evManager)
    
    # Prepare Game Objects
    clock = pygame.time.Clock()
    # Main Loop
    going = True
    while going:
        clock.tick(30)
        going = controller.processGUIEvents(pygame.event.get())
        gui.draw()

    pygame.quit()







# this calls the 'main' function when this script is executed
if __name__ == '__main__':
    main()
