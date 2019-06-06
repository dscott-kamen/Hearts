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
            'cardHeight' : 105,
            'cardWidth' : 70,
            'handSpacing' : 40,
            'cardSpacing' : 10,
            'scoreAreaHeight' : 40,
            'topLevelWidth' : 800,
            'topLevelHeight' : 600,
            'cardSelectionSpacing' : 30}

RECT_LOOKUP = {}
SURFACE_LOOKUP = {}

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
    def __init__(self, seatLabel, hand, evManager):
        rect = RECT_LOOKUP['TopLevel', ('ScoreArea', seatLabel)]
        pygame.Surface.__init__(self, rect.size)
        
        self.seatLabel = seatLabel
        self.hand = hand
        self.evManager = evManager
        self.evManager.registerListener(self)
        self.changed = True
        self.currentTurn = False
    
    def notify(self, event):

        if isinstance(event, CardPlayedEvent):
            self.currentTurn = (event.nextHand == self.hand)
            self.changed = True

        if isinstance(event, TrickInitializedEvent):
            self.currentTurn = (event.nextHand == self.hand)
            self.changed = True

        if isinstance(event, TrickCompleteEvent):
            self.changed = True
            
        if isinstance(event, RoundCompleteEvent):
            self.changed = True
            
        if isinstance(event, GameInitializedEvent):
            self.changed = True
    
    def createNameText(self):
        font = pygame.font.Font(None, 36)
        text = font.render(self.hand.getName(), 1, (10, 10, 10))
        return self.transformNameText(text)
    
    def createScoreText(self):
        font = pygame.font.Font(None, 24)
        text = font.render('Score: %d (%d)' % (self.hand.score.gameScore ,self.hand.score.roundScore), 1, (10, 10, 10))
        return self.transformScoreText(text)
    
    def draw(self):
        if self.changed:
            self.fill((self.getScoreAreaColor()))
            
            rect = RECT_LOOKUP[('TopLevel', ('ScoreArea', self.seatLabel))]
            pygame.draw.rect(self, SCR_ATTR['rectangleColor'], self.get_rect(), 1)
        
            #create name text
            text, rect = self.createNameText()    
            self.blit(text, rect)
        
            #create score text
            text, rect = self.createScoreText()            
            self.blit(text, rect)

    def getCardRotation(self):
        if self.seatLabel == 'Right':
            return 90
        elif self.seatLabel == 'Left':
            return -90
        else:
            return 0

    def getScoreAreaColor(self):
            if self.currentTurn:
                return SCR_ATTR['scoreAreaCurrentTurnColor']
            else:
                return SCR_ATTR['scoreAreaColor']
        
    def transformNameText(self, text):
        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            return text, text.get_rect(midleft=(5,self.get_rect().height/2))
        elif self.seatLabel == 'Left':
            text = pygame.transform.rotate(text, self.getCardRotation())
            return text, text.get_rect(midtop=(self.get_rect().width/2, 5))
        elif self.seatLabel == 'Right':
            text = pygame.transform.rotate(text, self.getCardRotation())
            return text, text.get_rect(midbottom=(self.get_rect().width/2, self.get_rect().height - 5))

    def transformScoreText(self, text):
        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            return text, text.get_rect(midright=(self.get_rect().width - 5, self.get_rect().height/2))
        elif self.seatLabel == 'Right':
            text = pygame.transform.rotate(text, self.getCardRotation())
            return text, text.get_rect(midtop=(self.get_rect().width/2, 5))
        elif self.seatLabel == 'Left':
            text = pygame.transform.rotate(text, self.getCardRotation())
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
    def __init__(self, seatLabel, hand, evManager):

        self.parentRect = RECT_LOOKUP[('TopLevel', ('Hand', seatLabel))]

        pygame.Surface.__init__(self, self.parentRect.size)
        self.hand = hand 
        self.cardWIDGETS = pygame.sprite.LayeredUpdates()
        self.seatLabel = seatLabel
        self.changed = False
        self.selectedCards = []
        self.evManager = evManager
        self.evManager.registerListener(self)
        
        self.initialize()
        
    def notify(self, event):
        
        if isinstance(event, CardSelectedEvent):
            if event.hand == self.hand:
                self.toggleSelectedCard(event.card, event.replacedCard)
                self.changed = True
                self.clearCardArea()

        elif isinstance(event, CardPlayedEvent):
            self.currentTurn = (event.nextHand == self.hand)
            if event.hand == self.hand:
                self.changed = True
                self.selectedCards.clear()
                self.buildCards()

        elif isinstance(event, PassCompleteEvent):
            self.changed = True
            self.selectedCards.clear()
            self.buildCards()
                        
        elif isinstance(event, RoundInitializedEvent):
            self.changed = True
            self.buildCards()

        elif isinstance(event, TrickInitializedEvent):
            self.currentTurn = (event.nextHand == self.hand)
            
    def buildCards(self):
        #cleanup for removed widgets
        self.clearCardArea()

        self.cardWIDGETS.empty()
        rotation = self.getCardRotation()
        for card in self.hand.cards:
            cardWIDGET = CardWIDGET(card, rotation)
            self.cardWIDGETS.add(cardWIDGET)

    def clearCardArea(self):
        background = SURFACE_LOOKUP['Background']
        self.blit(background, self.get_rect())
        
    def draw(self):
        
        if self.changed:
            rect = RECT_LOOKUP[(('Hand', self.seatLabel), 'Rectangle')]
            pygame.draw.rect(self, SCR_ATTR['rectangleColor'], rect, 1)

            spacing = self.getCardSpacing(self.getSpanRange(), len(self.hand.cards))        
            notSelectedRect = RECT_LOOKUP[(('Hand', self.seatLabel), 'CardNotSelected')]
            selectedRect = RECT_LOOKUP[(('Hand', self.seatLabel), 'CardSelected')]
        
            for i, card in enumerate(self.cardWIDGETS):
                cardRect = self.getCardRect(card, i, spacing, selectedRect, notSelectedRect)
                self.blit(card.image, cardRect)
                
                #Functionality added to support mouse clicks on sprites
                card.setRect(get_absolute_rect(cardRect, self.parentRect))
                card.setRelativeRect(cardRect)

    def getCardRect(self, card, cardIndex, spacing, selectedRect, notSelectedRect):
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

    def getCardRotation(self):
        if self.seatLabel == 'Right':
            return 90
        elif self.seatLabel == 'Left':
            return -90
        else:
            return 0

    def getCardSpacing(self, spanRange, cardCount):
        if cardCount == 1 or spanRange > cardCount * (SCR_ATTR['cardWidth'] + SCR_ATTR['cardSpacing']):
            return SCR_ATTR['cardWidth'] + 0.5 * SCR_ATTR['cardSpacing']
        else:
            return int((spanRange - SCR_ATTR['cardWidth'] - 0.5 * SCR_ATTR['cardSpacing'])//(cardCount - 1))

    def getCardWIDGET(self, card):
        for cardWIDGET in self.cardWIDGETS:
            if cardWIDGET.card == card:
                return cardWIDGET
        return None

    def getSelectedCards(self):
        return self.selectedCards

    def getSpanRange(self):
        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            return self.parentRect.width
        else:
            return self.parentRect.height

    def initialize(self):
 
        self.changed = True
        self.fill(SCR_ATTR['tableTopColor'])
         
    def toggleSelectedCard(self, selectedCard, replacedCard):
        
        if replacedCard is not None:
            self.selectedCards.remove(replacedCard)
            
        if selectedCard in self.selectedCards:
            self.selectedCards.remove(selectedCard)
        else:
            self.selectedCards.append(selectedCard)

            
class BoardWIDGET(pygame.Surface):
    def __init__(self, gui, board, seatAssignment, evManager):
        rect = RECT_LOOKUP[('TopLevel', 'Board')]
        pygame.Surface.__init__(self, rect.size)
        self.fill(SCR_ATTR['tableTopColor'])
        
        self.gui = gui
        self.board = board
        self.seatAssignment = seatAssignment
        self.changed = True
        self.cardWIDGETS = []
        self.playOrder = []
        self.evManager = evManager
        self.evManager.registerListener(self)
        self.playCardAnimation = False
            
    def notify(self, event):

        if isinstance(event, TrickCompleteEvent):
            self.changed = True
                        
        elif isinstance(event, TrickInitializedEvent):
            self.setPlayOrder(event.playOrder)
            self.changed = True

    def clearBoard(self):
        background = SURFACE_LOOKUP['Background']
        self.blit(background, self.get_rect())

    def draw(self):
        
        if self.changed:
            self.clearBoard()
            
            for i, (card, hand) in enumerate(zip(self.board.cards, self.playOrder)):                

                if self.playCardAnimation and i >= len(self.board.cards) - 1:
                    continue
                cardWIDGET = CardWIDGET(card)
                self.blit(cardWIDGET.image, self.getCardRect(hand))

    def getCard(self, hand):
        idx = self.playOrder.index(hand)
        return self.board.cards[idx]
        
    def getCardRect(self, hand):    
        seatLabel = self.seatAssignment[hand.getName()]
        return RECT_LOOKUP[('Board', seatLabel)]
     
    def setPlayOrder(self, playOrder):
        self.playOrder = playOrder
        
        
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

        if isinstance(event, GameInitializedEvent):
            self.initializeGame(event.hands, event.board)            
        
        if isinstance(event, CardPlayedEvent):
            self.animatePlayCard(event.hand, event.card)

        if isinstance(event, TrickCompleteEvent):
            self.animateTrickWinner(event.winner)
            
    def animatePlayCard(self, hand, card):
        
        handWIDGET = self.getHandWIDGET(hand)
        cardWIDGET = handWIDGET.getCardWIDGET(handWIDGET.getSelectedCards()[0])

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
                    handWIDGET.changed = True
                self.boardWIDGET.changed = True
            
            if anima.animationType == 'TrickWinner':
                
                rect = anima.getRect()
                background = SURFACE_LOOKUP['Background']
                cardBackground = background.subsurface(rect)
                pygame.display.get_surface().blit(cardBackground, rect)

                for hand in self.handWIDGETS:
                    hand.changed = True
                for scoreAreaWIDGET in self.scoreAreaWIDGETS:
                    scoreAreaWIDGET.changed = True
                    
    def draw(self):
        self.setAnimationRedraws()
        self.clearAnimations()
        self.drawBoard()        
        self.drawHands()
        self.drawScoreArea()
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
        if self.boardWIDGET.changed:
            self.boardWIDGET.draw()
            rect = RECT_LOOKUP[('TopLevel', 'Board')]
            pygame.display.get_surface().blit(self.boardWIDGET, rect)
            self.boardWIDGET.changed = False
        
    def drawHands(self):
        for hand in self.handWIDGETS:
            if hand.changed:
                rect = RECT_LOOKUP[('TopLevel', ('Hand', hand.seatLabel))]
                hand.draw()
                pygame.display.get_surface().blit(hand, rect)
                hand.changed = False
        
    def drawScoreArea(self):
        for scoreArea in self.scoreAreaWIDGETS:
            if scoreArea.changed:
                rect = RECT_LOOKUP[('TopLevel', ('ScoreArea', scoreArea.seatLabel))]        
                scoreArea.draw()
                pygame.display.get_surface().blit(scoreArea, rect)
                scoreArea.changed = False
        
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
                
        screen.blit(background, rect)
        pygame.display.flip()

    def initializeGame(self, hands, board):
        
        self.seatAssignment = self.mapSeatAssignment(hands)

        for hand, seatLabel in zip(hands, self.seatLabels):
            handWIDGET = HandWIDGET(seatLabel, hand, self.evManager)
            self.handWIDGETS.append(handWIDGET)
            
            scoreAreaWIDGET = ScoreAreaWIDGET(seatLabel, hand, self.evManager)
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

    def mapSeatAssignment(self, hands):
        
        seatAssignment = {}
        for hand,seatLabel in zip(hands, self.seatLabels):
            seatAssignment[hand.getName()] = seatLabel
        return seatAssignment

    def postAnimationProcessing(self, anima):

        if anima.animationType == 'PlayCard':
            
            self.boardWIDGET.playCardAnimation = False
            self.boardWIDGET.changed = True

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