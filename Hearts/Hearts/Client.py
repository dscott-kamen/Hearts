import os, pygame
from Hearts import *
from GameController import *
from resource import *
#from Game import Player
import threading


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

SURFACE_LOOKUP = {}

class NotificationWIDGET(pygame.Surface):
    def __init__(self):
        rect = RECT_LOOKUP[('TopLevel', 'NotificationArea')]
        pygame.Surface.__init__(self, rect.size)
        self.fill(SCR_ATTR['notificationAreaColor'])

        
        self._message = ''
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
        self._changed = value
    

        
class CardWIDGET(pygame.sprite.Sprite):
   
    def __init__(self, card, frontImageFileName, showFront=True, visible=True, highlighted=False, selected=False, rotation=0):
        pygame.sprite.Sprite.__init__(self)

        self.card = card
        self._visible = visible
        self._showFront = showFront
        self._rotation = rotation
        self._selected = selected
        self._highlighted = highlighted
        self.rect = Rect(0,0,0,0)
        self.relativeRect = Rect(0,0,0,0)

        self._frontImageFileName = frontImageFileName 
        self._backImageFileName = 'red_back.png'
        self._getImage()
        
    
    @property
    def cardLabel(self): return self._card
    @property        
    def highlighted(self): return self._highlighted    
    @property
    def rotation(self): return self._rotation    
    @property   
    def selected(self): return self._selected    
    @property
    def showFront(self): return self._showFront    
    @property
    def visible(self): return self._visible    
    
    @highlighted.setter
    def highlighted(self, flag):
        self._highlighted = flag
        if self.highlighted and self.showFront:
            self.image = self._applyColor(self.image)

    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        if self.rotation != 0:
            self.image = self._applyRotation(self.image)

    @selected.setter
    def selected(self, flag):
        self._selected = flag

    @showFront.setter
    def showFront(self, flag):
        self._showFront = flag

    @visible.setter
    def visible(self, flag):
        self._visible = flag

    def getRelativeRect(self):
        return self.relativeRect

    def setRect(self, rect):
        self.rect = rect
        
    def setRelativeRect(self, rect):
        self.relativeRect = rect

    def _applyColor(self, image):
        image = image.copy()
        image.fill((60, 60, 0, 0), special_flags=pygame.BLEND_SUB)
        return image
    
    def _applyRotation(self, image):
        image = image.copy()
        return pygame.transform.rotate(image, self.rotation)
        
    def _getImage(self):
            
        if self.showFront:
            self.image = load_image(self._frontImageFileName, size=(SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight']))    
        else:
            self.image = load_image(self._backImageFileName, size=(SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight']))    
        
        if self.rotation != 0:
            self.image = self._applyRotation(self.image)

        if self.highlighted:
            self.image = self._applyColor(self.image) 


        
class ScoreAreaWIDGET(pygame.Surface):
    def __init__(self, seatLabel, rotation):
        self._seatLabel = seatLabel
        self._colorLabel = 'scoreAreaColor'
        self._changed = True
        self._rotation = rotation
        self._nameText = ''
        self._scoreText = ''

        rect = RECT_LOOKUP['TopLevel', ('ScoreArea', seatLabel)]
        pygame.Surface.__init__(self, rect.size)

        self.fill(SCR_ATTR[self.colorLabel])
            
        rect = RECT_LOOKUP[('TopLevel', ('ScoreArea', self.seatLabel))]
        pygame.draw.rect(self, SCR_ATTR['rectangleColor'], self.get_rect(), 1)
        
    @property 
    def changed(self): return self._changed
    @property
    def colorLabel(self): return self._colorLabel 
    @property
    def nameText(self): return self._nameText
    @property
    def rotation(self): return self._rotation
    @property
    def scoreText(self): return self._scoreText
    @property
    def seatLabel(self): return self._seatLabel
                    
    @colorLabel.setter
    def colorLabel(self, colorLabel):
        self._colorLabel = colorLabel   
        self._changed = True
        
    @nameText.setter
    def nameText(self, text):
        self._nameText = text
        self._changed = True
        
    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        
    @scoreText.setter
    def scoreText(self, text):
        self._scoreText = text
        self._changed = True
        
    def draw(self):
        if self._changed:
            self.fill(SCR_ATTR[self.colorLabel])
            
            rect = RECT_LOOKUP[('TopLevel', ('ScoreArea', self.seatLabel))]
            pygame.draw.rect(self, SCR_ATTR['rectangleColor'], self.get_rect(), 1)
        
            #create name text
            text, rect = self._createNameText()    
            self.blit(text, rect)
        
            #create score text
            text, rect = self._createScoreText()            
            self.blit(text, rect)

        self._changed = False

    def redraw(self):
        self._changed = True

    def _createNameText(self):
        font = pygame.font.SysFont(SCR_ATTR['font'], 24)
        text = font.render(self.nameText, 1, (10, 10, 10))
        return self._transformNameText(text)
    
    def _createScoreText(self):
        font = pygame.font.SysFont(SCR_ATTR['font'], 18)
        text = font.render(self.scoreText, 1, (10, 10, 10))
        return self._transformScoreText(text)
    
    def _transformNameText(self, text):
        if self.rotation==0: #top/bottom
            return text, text.get_rect(midleft=(5,self.get_rect().height/2))
        elif self.rotation == -90: #left
            text = pygame.transform.rotate(text, self.rotation)
            return text, text.get_rect(midtop=(self.get_rect().width/2, 5))
        elif self.rotation == 90: #right
            text = pygame.transform.rotate(text, self.rotation)
            return text, text.get_rect(midbottom=(self.get_rect().width/2, self.get_rect().height - 5))

    def _transformScoreText(self, text):
        if self.rotation==0: #top/bottom
            return text, text.get_rect(midright=(self.get_rect().width - 5, self.get_rect().height/2))
        elif self.rotation == 90: #right
            text = pygame.transform.rotate(text, self.rotation)
            return text, text.get_rect(midtop=(self.get_rect().width/2, 5))
        elif self.rotation == -90: #left
            text = pygame.transform.rotate(text, self.rotation)
            return text, text.get_rect(midbottom=(self.get_rect().width/2, self.get_rect().height - 5))
 

class Animation():
    def __init__(self, animationType, widget, moveSpeed, startRect, endRect=None, redrawWIDGETS=None, callback=None):
        self.animationType = animationType
        self.WIDGET = widget
        self.currentPos = startRect.topleft  
        self.startPos = startRect.topleft
        self.endPos = endRect.topleft
        self.redrawWIDGETS = redrawWIDGETS
        self.moveXY = calculateMoveXY(startRect, endRect, moveSpeed)
        self.callback = callback
    
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
    def __init__(self, seatLabel, rotation=0):

        self._cardWIDGETS = pygame.sprite.LayeredUpdates()
        self._seatLabel = seatLabel
        self._rotation = rotation

        self._setChanged(True)        

        self.parentRect = RECT_LOOKUP[('TopLevel', ('Hand', seatLabel))]
        pygame.Surface.__init__(self, self.parentRect.size)
        self.fill(SCR_ATTR['tableTopColor'])

        rect = RECT_LOOKUP[(('Hand', self.seatLabel), 'Rectangle')]
        pygame.draw.rect(self, SCR_ATTR['rectangleColor'], rect, 1)
        
    
    @property
    def changed(self): return self._changed  #no setter
    @property
    def cardsChanged(self): return self._changed
    @property
    def cardWIDGETS(self): return self._cardWIDGETS
    @property 
    def rotation(self): return self._rotation
    @property
    def seatLabel(self): return self._seatLabel
        
    @cardWIDGETS.setter
    def cardWIDGETS(self, cardWIDGETS):
        self._clearCardArea()
        self._setChanged(True)
        self._cardWIDGETS.empty()
        for cardWIDGET in cardWIDGETS:
            self._cardWIDGETS.add(cardWIDGET)
            
    @rotation.setter
    def rotation(self, value):
        self._rotation = value

    @seatLabel.setter
    def seatLabel(self, label):
        self._seatLabel = label
        
    def draw(self):
        
        if self.changed:
            rect = RECT_LOOKUP[(('Hand', self.seatLabel), 'Rectangle')]
            pygame.draw.rect(self, SCR_ATTR['rectangleColor'], rect, 1)

            spacing = self._getCardSpacing(self._getSpanRange(), len(self.cardWIDGETS))        
            notSelectedRect = RECT_LOOKUP[(('Hand', self.seatLabel), 'CardNotSelected')]
            selectedRect = RECT_LOOKUP[(('Hand', self.seatLabel), 'CardSelected')]
        
            for i, card in enumerate(self.cardWIDGETS):
                cardRect = self._getCardRect(card, i, spacing, selectedRect, notSelectedRect)
                self.blit(card.image, cardRect)
                
                #Functionality added to support mouse clicks on sprites
                card.setRect(get_absolute_rect(cardRect, self.parentRect))
                card.setRelativeRect(cardRect)
            
            self._setChanged(False)

    def redraw(self):
        self._setChanged(True)
        self._clearCardArea()
        
    def _clearCardArea(self):
        background = SURFACE_LOOKUP['Background']
        self.blit(background, self.get_rect())
        
    def _getCardRect(self, card, cardIndex, spacing, selectedRect, notSelectedRect):
        if card.selected:
            rect = selectedRect.copy()
        else:
            rect = notSelectedRect.copy()

        if self.rotation == 0: #top/bottom
            rect.left = rect.left + cardIndex * spacing
        elif self.rotation == -90: #left
            rect.top = rect.top + cardIndex * spacing
        elif self.rotation == 90: #right
            rect.bottom = rect.bottom - cardIndex * spacing - SCR_ATTR['cardWidth']
        return rect

    def _getCardSpacing(self, spanRange, cardCount):
        if cardCount == 1 or spanRange > cardCount * (SCR_ATTR['cardWidth'] + SCR_ATTR['cardSpacing']):
            return SCR_ATTR['cardWidth'] + 0.5 * SCR_ATTR['cardSpacing']
        else:
            return int((spanRange - SCR_ATTR['cardWidth'] - 0.5 * SCR_ATTR['cardSpacing'])//(cardCount - 1))

    def _getSpanRange(self):
        if self.rotation == 0: #top/bottom
            return self.parentRect.width
        else:
            return self.parentRect.height
    
    def _setChanged(self, value):
        self._changed = value
            
class BoardWIDGET(pygame.Surface):
    def __init__(self):
        self._changed = True
        self._cardWIDGETS = []
        self._playOrder = []  #based on seatLabel
        
        rect = RECT_LOOKUP[('TopLevel', 'Board')]
        pygame.Surface.__init__(self, rect.size)
        self.fill(SCR_ATTR['tableTopColor'])
        
            
    @property
    def cardWIDGETS(self): return self._cardWIDGETS
    @property
    def changed(self): return self._changed
    @property
    def playOrder(self): return self._playOrder
    
    @cardWIDGETS.setter
    def cardWIDGETS(self, cardWIDGETS):
        self._clearBoard()
        self._setChanged(True)
        
        self.cardWIDGETS.clear()
        for cardWIDGET in cardWIDGETS:
            self._cardWIDGETS.append(cardWIDGET)
      
    def clearCards(self):
        self._setChanged(True)
        self.cardWIDGETS.clear()
        self._clearBoard()
                
    def draw(self):
        if self.changed:
            for cardWIDGET, seatLabel in zip(self.cardWIDGETS, self.playOrder):
                if cardWIDGET.visible:
                    self.blit(cardWIDGET.image, self._getCardRect(seatLabel))
            self._setChanged(False)
                    
    def redraw(self):
        self._setChanged(True)
    
    def setPlayOrder(self, seatLabels):
        self._setChanged(True)
        self._playOrder = seatLabels
        
    def _clearBoard(self):
        background = SURFACE_LOOKUP['Background']
        self.blit(background, self.get_rect())

    def _getCard(self, seatLabel):
        return self.cardWIDGETS[self._playOrder.index(seatLabel)]

    def _getCardRect(self, seatLabel):    
        return RECT_LOOKUP[('Board', seatLabel)]
     
    def _setChanged(self, value):
        self._changed = value

        
class Gui():
    def __init__(self, player):

        self.seatLabels = ['Bottom', 'Left', 'Top', 'Right']
        self.rotation = [0, -90, 0, 90]
        self._animations =  []
        self._handWIDGETS = []
        self._scoreAreaWIDGETS = []
        self.currentPosition = -1
        self.player = player
        self.gameInitialized = False

        #Draw initial screen
        DataPrep()
        self._initialize()
        threading.Thread(target=DataPrep()._preloadCardImages)        

        

    @property
    def animations(self): return self._animations
    @property
    def board(self): return self._board
    @property
    def handWIDGETS(self): return self._handWIDGETS
    @property
    def scoreAreaWIDGETS(self): return self._scoreAreaWIDGETS

    @animations.setter
    def animations(self, animations):
        self._animations = animations

    @board.setter
    def board(self, board):
        self._board = board

    @handWIDGETS.setter
    def handWIDGETS(self, handWIDGETS):
        self._handWIDGETS = handWIDGETS
        
    @scoreAreaWIDGETS.setter
    def scoreAreaWIDGETS(self, scoreAreaWIDGET):
        self._scoreAreaWIDGETS = scoreAreaWIDGET
        

        
        
    def draw(self):
        self._setAnimationRedraws()
        self._clearAnimations()
        self._drawBoard()        
        self._drawHands()
        self._drawScoreArea()
        self._drawNotification()
        self._drawAnimations()
        
        
        pygame.display.flip()

    def redraw(self):
        for handWIDGET, scoreAreaWIDGET in zip(self.handWIDGETS, self.scoreAreaWIDGETS):
            handWIDGET.redraw()
            scoreAreaWIDGET.redraw()
        self.boardWIDGET.redraw()
        self.notificationAreaWIDGET.redraw()
        

    def _clearAnimations(self):
        for anima in self.animations:    
            rect = anima.getRect()
            background = SURFACE_LOOKUP['Background']
            cardBackground = background.subsurface(rect)
            pygame.display.get_surface().blit(cardBackground, rect)
                    
    def _drawAnimations(self):
        for anima in self.animations:
            rect = anima.move()
            if not anima.isMoveComplete():
                pygame.display.get_surface().blit(anima.WIDGET, rect)
            else:
                self.animations.remove(anima)
                if anima.callback is not None:
                    anima.callback(anima)

    def _drawBoard(self):
        if self.boardWIDGET.changed:
            self.boardWIDGET.draw()
            rect = RECT_LOOKUP[('TopLevel', 'Board')]
            pygame.display.get_surface().blit(self.boardWIDGET, rect)

        
    def _drawHands(self):
        for handWIDGET in self.handWIDGETS[::-1]:
            if handWIDGET.changed:
                rect = RECT_LOOKUP[('TopLevel', ('Hand', handWIDGET.seatLabel))]
                handWIDGET.draw()
                pygame.display.get_surface().blit(handWIDGET, rect)
        
    def _drawNotification(self):
#        if self.notificationAreaWIDGET.hasChanged():
            self.notificationAreaWIDGET.draw()
            rect = RECT_LOOKUP[('TopLevel', 'NotificationArea')]
            pygame.display.get_surface().blit(self.notificationAreaWIDGET, rect)
    
    def _drawScoreArea(self):
        for scoreArea in self.scoreAreaWIDGETS:
            if scoreArea.changed:
                rect = RECT_LOOKUP[('TopLevel', ('ScoreArea', scoreArea.seatLabel))]        
                scoreArea.draw()
                pygame.display.get_surface().blit(scoreArea, rect)
        
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

    def _initialize(self):
        
        #Open window and title
        rect = RECT_LOOKUP['TopLevel', 'TopLevel'] 
        screen = pygame.display.set_mode((rect.size))
        pygame.display.set_caption('Hearts')

        #Setup background
        background = pygame.Surface(rect.size)
        background.fill((SCR_ATTR['tableTopColor']))        
        SURFACE_LOOKUP['Background'] = background
        screen.blit(background, rect)
        
        #Hand
        for seatLabel, rotation in zip(self.seatLabels, self.rotation):
            handWIDGET = HandWIDGET(seatLabel, rotation)
            self.handWIDGETS.append(handWIDGET)
            
            scoreAreaWIDGET = ScoreAreaWIDGET(seatLabel, rotation)
            self.scoreAreaWIDGETS.append(scoreAreaWIDGET)
        
        self.boardWIDGET = BoardWIDGET()
        self.boardWIDGET.setPlayOrder(self.seatLabels) 

        #Setup notification area
        self.notificationAreaWIDGET = NotificationWIDGET()

        self.draw()
        pygame.display.flip()
        
    def _setAnimationRedraws(self):
        for anima in self.animations:
            for WIDGET in anima.redrawWIDGETS:
                WIDGET.redraw()

class DataPrep():
    def __init__(self):
        pass
    
    def _getCardAreaHeight(self):
        return SCR_ATTR['cardHeight'] + SCR_ATTR['cardSpacing']

    def _getPadding(self):
        return self._getCardAreaHeight() + SCR_ATTR['scoreAreaHeight']
    
    def getRects(self):

        rect = {}
        
        width = SCR_ATTR['topLevelWidth']
        height = SCR_ATTR['topLevelHeight']
        rect[('TopLevel', 'TopLevel')] = Rect(0, 0, width, height)

        x = self._getPadding()
        y = SCR_ATTR['scoreAreaHeight']
        width = SCR_ATTR['topLevelWidth'] - 2 * self._getPadding()
        height = self._getCardAreaHeight() + SCR_ATTR['cardSelectionSpacing']
        rect[('TopLevel', ('Hand', 'Top'))] = Rect(x, y, width, height)

        y = SCR_ATTR['topLevelHeight'] - self._getPadding() - SCR_ATTR['cardSelectionSpacing']
        rect[('TopLevel', ('Hand', 'Bottom'))] = Rect(x, y, width, height)

        y = 0
        height = SCR_ATTR['scoreAreaHeight']
        rect[('TopLevel', ('ScoreArea', 'Top'))] = Rect(x, y, width, height)
        
        y = SCR_ATTR['topLevelHeight'] - SCR_ATTR['scoreAreaHeight']
        rect[('TopLevel', ('ScoreArea', 'Bottom'))] = Rect(x, y, width, height)

        x = 0
        y = 0
        height = self._getCardAreaHeight()
        rect[(('Hand', 'Top'), 'Rectangle')] = Rect(x, y, width, height)
        
        y = SCR_ATTR['cardSelectionSpacing']
        rect[(('Hand', 'Bottom'), 'Rectangle')] = Rect(x, y, width, height)

        x = SCR_ATTR['scoreAreaHeight']
        y = self._getPadding()
        width = self._getCardAreaHeight() + SCR_ATTR['cardSelectionSpacing']
        height = SCR_ATTR['topLevelHeight'] - 2 * self._getPadding()         
        rect[('TopLevel', ('Hand', 'Left'))] = Rect(x, y, width, height)
        
        x = SCR_ATTR['topLevelWidth'] - self._getPadding() - SCR_ATTR['cardSelectionSpacing']
        rect[('TopLevel', ('Hand', 'Right'))] = Rect(x, y, width, height)

        x = 0
        width = SCR_ATTR['scoreAreaHeight']
        rect[('TopLevel', ('ScoreArea', 'Left'))] = Rect(x, y, width, height)
        
        x = SCR_ATTR['topLevelWidth'] - SCR_ATTR['scoreAreaHeight']
        rect[('TopLevel', ('ScoreArea', 'Right'))] = Rect(x, y, width, height)

        x = 0
        y = 0
        width = self._getCardAreaHeight()
        rect[(('Hand', 'Left'), 'Rectangle')] = Rect(x, y, width, height)

        x = SCR_ATTR['cardSelectionSpacing']
        rect[(('Hand', 'Right'), 'Rectangle')] = Rect(x, y, width, height)

        x = self._getPadding()
        y = x
        width = SCR_ATTR['topLevelWidth'] - 2*x
        height = SCR_ATTR['topLevelHeight'] - 2*y
        rect[('TopLevel','Board')] = Rect(x, y, width, height)


        cardWidth = SCR_ATTR['cardWidth']
        cardHeight = SCR_ATTR['cardHeight']
        cardSpaceHalf = SCR_ATTR['cardSpacing']/2
        cardSelectionOffset = cardSpaceHalf + SCR_ATTR['cardSelectionSpacing']
        
        rect[(('Hand', 'Top'), 'CardNotSelected')] = Rect(cardSpaceHalf, cardSpaceHalf, cardWidth, cardHeight)
        rect[(('Hand', 'Top'), 'CardSelected')] = Rect(cardSpaceHalf, cardSelectionOffset, cardWidth, cardHeight)
        rect[(('Hand', 'Bottom'), 'CardNotSelected')] = Rect(cardSpaceHalf, cardSelectionOffset, cardWidth, cardHeight)
        rect[(('Hand', 'Bottom'), 'CardSelected')] = Rect(cardSpaceHalf, cardSpaceHalf, cardWidth, cardHeight)
        rect[(('Hand', 'Left'), 'CardNotSelected')] = Rect(cardSpaceHalf, cardSpaceHalf, cardHeight, cardWidth)
        rect[(('Hand', 'Left'), 'CardSelected')] = Rect(cardSelectionOffset, cardSpaceHalf, cardHeight, cardWidth)
        y = SCR_ATTR['topLevelHeight'] - 2 * self._getPadding() - cardSpaceHalf
        rect[(('Hand', 'Right'), 'CardSelected')] = Rect(cardSpaceHalf, y, cardHeight, cardWidth)
        rect[(('Hand', 'Right'), 'CardNotSelected')] = Rect(cardSelectionOffset, y, cardHeight, cardWidth)
      
        boardWidth = SCR_ATTR['topLevelWidth'] - 2 * self._getPadding()
        boardHeight = SCR_ATTR['topLevelHeight'] - 2 * self._getPadding()      
        x = boardWidth/2 - cardWidth/2
        y = boardHeight/2 - cardHeight/2 - cardHeight/2 - 2 * cardSpaceHalf
        rect[('Board', 'Top')] = Rect(x, y, cardWidth, cardHeight)
        
        y = boardHeight/2 - cardHeight/2 + cardHeight/2 + 2 * cardSpaceHalf
        rect[('Board', 'Bottom')] = Rect(x, y, cardWidth, cardHeight)

        x =  boardWidth/2 - cardWidth/2 - cardWidth - 2*cardSpaceHalf
        y = boardHeight/2 - cardHeight/2
        rect[('Board', 'Left')] = Rect(x, y, cardWidth, cardHeight)
        
        x = boardWidth/2 - cardWidth/2 + cardWidth + 2*cardSpaceHalf        
        rect[('Board', 'Right')] = Rect(x, y, cardWidth, cardHeight)
        
        notifx, notify = SCR_ATTR['notificationPadding']
        x, y = self._getPadding() + notifx, self._getPadding() + notify
        width = SCR_ATTR['topLevelWidth'] - 2 * notifx - 2 * self._getPadding()
        height = SCR_ATTR['notificationHeight']
        rect[('TopLevel','NotificationArea')] = Rect(x, y, width, height)
        
        return rect

    def _preloadCardImages(self):
        for suit in Card.SUIT:  
            for value in Card.VALUE:
                load_image('%s%s.png' % (suit, value), size=(SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight']))

    
RECT_LOOKUP = DataPrep().getRects()





def main():
    """this function is called when the program starts.
       it initializes everything it needs, then runs in
       a loop until the function returns."""

    pygame.init()

    players = ['Player1', 'Player2', 'Player3', 'Player4']
    evManager = EventManager()
    hearts = Hearts(players, evManager)
    player = Player('Al')
    position = hearts.requestHand(player)
    player.position = position
    gui = Gui(player)
    
    gameController = GameController(hearts, gui, evManager)
    hearts.startGame()
    gui.draw()
    
    # Prepare Game Objects
    clock = pygame.time.Clock()

    x = threading.Thread(name='EventManager', target=evManager.processEvents)
    x.start()
    
    # Main Loop
    going = True
    while going:
        clock.tick(30)
#        evManager.processEvents()
        going = gameController.processGUIEvents(pygame.event.get())
        gui.draw()

    evManager.shutdown()
    pygame.quit()







# this calls the 'main' function when this script is executed
if __name__ == '__main__':
    main()
