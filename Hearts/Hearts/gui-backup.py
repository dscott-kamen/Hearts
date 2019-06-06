
# Import Modules
import os, pygame
from Hearts import Hearts
from Hand import Hand
from pygame.locals import *
from pygame import mouse
import importlib
from GameController import *



if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')
SCR_ATTR = {
            'tableTop': (55, 166, 51),
            'red' : (255, 0, 0),
            'cardHeight' : 120,
            'cardWidth' : 80,
            'handSpacing' : 40,
            'cardSpacing' : 10,
            'cardSelectionSpacing' : 40}

RECT_LOOKUP = {}
CACHED_IMAGES = {}

def getDataDir():
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    return os.path.join(main_dir, 'data')

def rot_center(image, rect, angle):
        """rotate an image while keeping its center"""
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = rot_image.get_rect(center=rect.center)
        return rot_image,rot_rect

# functions to create our resources
def load_image(name, colorkey=None):
    
    image = CACHED_IMAGES.get(name, None)
    if image == None:
        fullname = os.path.join(getDataDir(), name)
        try:
            image = pygame.image.load(fullname).convert()
        except pygame.error as message:
            print('Cannot load image:', name)
            raise SystemExit(message)
        image = image.convert()
        CACHED_IMAGES[name] = image
    
    
#         if colorkey is not None:
#             if colorkey is -1:
#                 colorkey = image.get_at((0, 0))
#                 image.set_colorkey(colorkey, RLEACCEL)
    
    return image, image.get_rect()
def mouse_get_items(objects, mousePosition, topOnly=False):
    rect = Rect(mousePosition, (0,0))
    itemsFound = rect.collidelistall(objects)
    if itemsFound and topOnly:
        return [objects[itemsFound[-1]]]
    
    return itemsFound
#        s =     


class HandLocationFactory():
    def __init__(self, seatLabel):
        self.seatLabel = seatLabel
        
    def create(self):
        if self.seatLabel == 'Top':
            return TopHand()
        elif self.seatLabel == 'Bottom':
            return BottomHand()
        elif self.seatLabel == 'Left':
            return LeftHand()
        elif self.seatLabel == 'Right':
            return RightHand()
        elif self.seatLabel == 'Board':
            return Board()

class HandLocation():
    def __init__(self):
        pass

    def getSpanPadding(self):
        return self.getScoreAreaHeight() + self.getCardAreaHeight()

    def getCardAreaHeight(self):
        return SCR_ATTR['cardHeight'] + SCR_ATTR['cardSpacing']
    
    def getSelectionAreaHeight(self):
        return SCR_ATTR['cardSelectionSpacing']
    
    def getScoreAreaHeight(self):
        return 1.5 * SCR_ATTR['handSpacing']
    
    def getAreaOffset(self, areaName, height):
        if areaName == 'HandArea':
            return height/2
        elif areaName == 'CardArea':
            return height/2 + self.getScoreAreaHeight()
        elif areaName == 'CardAreaExtended':
            return height/2 + self.getScoreAreaHeight()
        elif areaName == 'ScoreArea':
            return height/2
        
    def getAreaWidth(self, areaName, width):
        if areaName == "HandArea":
            return width - 2 * self.getSpanPadding()
        else:
            return width
        
    def getAreaHeight(self, areaName):
        if areaName == 'HandArea':
            return self.getCardAreaHeight() + self.getScoreAreaHeight() + self.getSelectionAreaHeight()
        elif areaName == 'CardArea':
            return self.getCardAreaHeight()
        elif areaName == 'CardAreaExtended':
            return self.getCardAreaHeight() + self.getSelectionAreaHeight()
        elif areaName == 'ScoreArea':
            return self.getScoreAreaHeight()
            
    def populateRectLookup(self, parent, seatLabels):
        
        areaNames = ['HandArea', 'CardArea', 'CardAreaExtended', 'ScoreArea']
        
        for seatLabel in seatLabels:
            for areaName in areaNames:
                if areaName == 'HandArea':
                    parentRect = parent.get_rect()
                else:
                    parentRect = RECT_LOOKUP[('HandArea', seatLabel)]
                
                if seatLabel == 'Top' or seatLabel == 'Bottom':      
                    height = self.getAreaHeight(areaName)
                    width = self.getAreaWidth(areaName, parentRect.width)
                    rect = Rect(0, 0, width, height)
                    if areaName == 'HandArea':
                        xOffset = parentRect.centerx
                    else:
                        xOffset = width/2
                    yOffset = self.getAreaOffset(areaName, height)
                else:
                    height = self.getAreaWidth(areaName, parentRect.height)
                    width = self.getAreaHeight(areaName)
                    rect = Rect(0, 0, width, height)
                    xOffset = self.getAreaOffset(areaName, width)
                    if areaName == 'HandArea':
                        yOffset = parentRect.centery
                    else:
                        yOffset = height/2
                rect = self.centerRect(seatLabel, rect, parentRect, xOffset, yOffset)
                RECT_LOOKUP[(areaName, seatLabel)] = rect

    def centerRect(self, seatLabel, rect, parentRect, xOffset, yOffset):

        if seatLabel == 'Top' or seatLabel == 'Left':
            rect.center = xOffset, yOffset
        elif seatLabel == 'Right':
            rect.center = parentRect.width - xOffset, yOffset
        elif seatLabel == 'Bottom':
            rect.center = xOffset, parentRect.height - yOffset 
        return rect
        
    
class TopHand(HandLocation):
    
    def __init__(self):
        self.seatLabel = 'Top'
        self.rotation = 0

    def transformNameText(self, scoreArea, nameText):
        textPos = nameText.get_rect(midleft=(5, scoreArea.get_rect().centery))
        return nameText, textPos
        
    def transformScoreText(self, scoreArea, scoreText):
        textPos = scoreText.get_rect(midright=(scoreArea.get_rect().right - 5, scoreArea.get_rect().centery))
        return scoreText, textPos
    
    def getCardAreaSpanRange(self, cardArea):
        return cardArea.get_rect().width
    
    def getCardRect(self, cardAreaRect, spanningOffset):
        rect = Rect(0, 0, SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight'])
        rect.x = cardAreaRect.x + spanningOffset + SCR_ATTR['cardSpacing']/2
        rect.y = cardAreaRect.y + SCR_ATTR['cardSpacing']/2
        return rect
    
    def selectCard(self, sprite, adjustment):
        sprite.get_rect(top = sprite.get_rect().top + adjustment)
    
            
class BottomHand(HandLocation):
    def __init__(self):
        self.seatLabel = 'Bottom'
        self.rotation = 0
                

    def transformNameText(self, scoreArea, nameText):
        textPos = nameText.get_rect(midleft=(5, scoreArea.get_rect().centery))
        return nameText, textPos
        
    def transformScoreText(self, scoreArea, scoreText):
        textPos = scoreText.get_rect(midright=(scoreArea.get_rect().right - 5, scoreArea.get_rect().centery))
        return scoreText, textPos
        
    def getCardAreaSpanRange(self, cardArea):
        return cardArea.get_rect().width
    
    def getCardRect(self, cardAreaRect, spanningOffset):
        rect = Rect(0, 0, SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight'])
        rect.x = cardAreaRect.x + spanningOffset + SCR_ATTR['cardSpacing']/2
        rect.y = cardAreaRect.y + SCR_ATTR['cardSpacing']/2
        return rect

    def selectCard(self, sprite, adjustment):
        sprite.get_rect(top = sprite.get_rect().top - adjustment)

       
class LeftHand(HandLocation):
    def __init__(self):
        self.seatLabel = 'Bottom'
        self.rotation = -90
                
    def transformNameText(self, scoreArea, nameText):
        nameText = pygame.transform.rotate(nameText, self.rotation)
        textPos = nameText.get_rect(midtop=(scoreArea.get_rect().centerx, 5))
        return nameText, textPos
        
    def transformScoreText(self, scoreArea, scoreText):
        scoreText = pygame.transform.rotate(scoreText, self.rotation)
        textPos = scoreText.get_rect(midbottom=(scoreArea.get_rect().centerx, scoreArea.get_rect().bottom - 5))
        return scoreText, textPos

    def getCardAreaSpanRange(self, cardArea):
        return cardArea.get_rect().height
    
    def selectCard(self, sprite, adjustment):
        sprite.get_rect(left = sprite.get_rect().left + adjustment)


    def getCardRect(self, cardAreaRect, spanningOffset):
        rect = Rect(0, 0, SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight'])
        rect.x = cardAreaRect.x + SCR_ATTR['cardSpacing']/2
        rect.y = cardAreaRect.y + spanningOffset + SCR_ATTR['cardSpacing']/2
        return rect


class RightHand(HandLocation):

    def __init__(self):
        self.seatLabel = 'Bottom'
        self.rotation = 90
                
    def transformNameText(self, scoreArea, nameText):
        nameText = pygame.transform.rotate(nameText, self.rotation)
        textPos = nameText.get_rect(midbottom=(scoreArea.get_rect().centerx, scoreArea.get_rect().bottom - 5))
        return nameText, textPos
        
    def transformScoreText(self, scoreArea, scoreText):
        scoreText = pygame.transform.rotate(scoreText, self.rotation)
        textPos = scoreText.get_rect(midtop=(scoreArea.get_rect().centerx, 5))
        return scoreText, textPos

    def getCardAreaSpanRange(self, cardArea):
        return cardArea.get_rect().height

    def getCardRect(self, cardAreaRect, spanningOffset):
        rect = Rect(0, 0, SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight'])
        rect.x = cardAreaRect.x + SCR_ATTR['cardSpacing']/2
        rect.y = cardAreaRect.y + spanningOffset + SCR_ATTR['cardSpacing']/2
        return rect    

    def selectCard(self, sprite, adjustment):
        sprite.get_rect(left = sprite.get_rect().left - adjustment)


class Board(HandLocation):

    def __init__(self):
        self.seatLabel = 'Board'
                
    def getBoardRect(self, parent):
        spanPadding = self.getSpanPadding()
        return Rect(spanPadding, spanPadding, parent.get_rect().width - 2*spanPadding, parent.get_rect().height - 2 * spanPadding)


class HandWIDGET():    
    def __init__(self, seatLabel, rect, parent, hand, handLocation, evManager):
        self.surface = parent.subsurface(rect)
        self.subSurfaces = {}
        #Set pass local variables
        self.hand = hand
        self.seatLabel = seatLabel
        self.handLocation = handLocation
        self.changed = True

        self.evManager = evManager
        evManager.registerListener(self)
        
        self.initialize()

    def notify(self, event):
   
        if isinstance(event, CardSelectedEvent):
            if event.hand == self.hand:
                self.changed = True
                self.draw()

        if isinstance(event, CardPlayedEvent):
            if event.hand == self.hand:
                self.changed = True
                self.draw()

        if isinstance(event, PassCompleteEvent):
            self.changed = True
            self.draw()
            
        if isinstance(event, TrickCompleteEvent):
            #animate trick completion
            pass
            self.changed = True
            self.draw()
            
        if isinstance(event, TrickInitializedEvent):
            self.changed = True
            self.draw()
                
                        
        if isinstance(event, RoundCompleteEvent):
            self.changed = True
            self.draw()
            
        if isinstance(event, RoundInitializedEvent):
            self.changed = True
            self.draw()
            
        if isinstance(event, GameInitializedEvent):
            self.changed = True
            self.draw()
              
    def initialize(self):
        print(self.seatLabel)
        #Initialize cardArea
        rect = RECT_LOOKUP[('CardAreaExtended', self.seatLabel)]
        cardArea = self.surface.subsurface(rect)
        cardArea.fill(SCR_ATTR['tableTop'])
        self.subSurfaces['CardAreaExtended'] = cardArea
        
        #Initialize Score Area
        rect = RECT_LOOKUP[('ScoreArea', self.seatLabel)]
        scoreArea = self.surface.subsurface(rect)
        scoreArea.fill((0, 64, 255))
        self.subSurfaces['ScoreArea'] = scoreArea

        rect = RECT_LOOKUP[('CardArea', self.seatLabel)]
        self.subSurfaces['CardArea'] = scoreArea

        
    def getCardSpacing(self, cardArea):
        availableSpace = self.handLocation.getCardAreaSpanRange(cardArea)
        if len(self.hand.cards) == 1 or availableSpace > len(self.hand.cards) * (SCR_ATTR['cardWidth'] + 0.5 * SCR_ATTR['cardSpacing']):
            return SCR_ATTR['cardWidth'] + 0.5 * SCR_ATTR['cardSpacing']
        else:
            return int((availableSpace - SCR_ATTR['cardWidth'] - SCR_ATTR['cardSpacing'])//(len(self.hand.cards)-1))

    def draw(self):
        
        if self.changed:
            self.drawCardArea()
            self.drawScoreArea()
        self.changed = False
        pygame.display.get_surface().blit(self.surface, self.surface.get_rect())

    def drawCardArea(self):
        
        
        cardArea = self.subSurfaces['CardAreaExtended']
        pygame.draw.rect(cardArea, SCR_ATTR['red'], cardArea.get_rect(), 1)
        spacing = self.getCardSpacing(cardArea)
        for i, card in enumerate(self.hand.cards):
            rect = self.handLocation.getCardRect(cardArea.get_rect(), i * spacing)
            cardWIDGET = CardWIDGET(card, self.handLocation.rotation, self.handLocation)
            cardArea.blit(cardWIDGET.image, rect)

    def drawScoreArea(self):
        
        #create the score area surface
        scoreArea = self.subSurfaces['ScoreArea']
        scoreArea.fill((0, 64, 255))
        
        #Create rectangle
        pygame.draw.rect(scoreArea, SCR_ATTR['red'], scoreArea.get_rect(), 1)
        
        #create name text    
        font = pygame.font.Font(None, 36)
        text = font.render(self.hand.getName(), 1, (10, 10, 10))
        nameText, textPos = self.handLocation.transformNameText(scoreArea, text)
        scoreArea.blit(nameText, textPos)
        
        #create score text            
        font = pygame.font.Font(None, 24)
        text = font.render('Score: %d (%d)' % (self.hand.score.gameScore ,self.hand.score.roundScore), 1, (10, 10, 10))
        scoreText, textPos = self.handLocation.transformScoreText(scoreArea, text)
        scoreArea.blit(scoreText, textPos)
                         
 
class BoardWIDGET():
    def __init__(self, surfaceLabel, rect, parent, board, handLocation, seatAssignment, evManager):
        self.surface = parent.subsurface(rect)

        self.board = board
        self.handLocation = handLocation    
        self.seatAssignment = seatAssignment
        self.evManager = evManager
        self.evManager.registerListener(self)
        self.changed = True
        
        self.playOrder = []

    def notify(self, event):

        if isinstance(event, CardSelectedEvent):
            self.changed = True

        if isinstance(event, CardPlayedEvent):
            self.changed = True

        if isinstance(event, TrickCompleteEvent):
            self.changed = True

        if isinstance(event, TrickInitializedEvent):
            self.changed = True

        if isinstance(event, GameInitializedEvent):
            self.changed = True
            
    def setPlayOrder(self, playOrder):
        self.playOrder = playOrder
        
    def draw(self):

        if self.changed:
            for card, hand in zip(self.board.cards, self.playOrder):

                seatLabel = self.seatAssigment[hand.getName()]
                rect = self.getCardRect(seatLabel)
                cardWIDGET = CardWIDGET(self, card, None, self.handLocation.rotation)
                self.blit(cardWIDGET, rect)
            self.changed = False

    def getCardRect(self, seatLabel):
        
        maxHeightAdj = self.get_rect().height/2 - SCR_ATTR['cardHeight'] - SCR_ATTR['cardSpacing']
        maxWidthAdj = self.get_rect().width/2 - SCR_ATTR['cardHeight'] - SCR_ATTR['cardSpacing']
        heightAdj = SCR_ATTR['cardHeight']/2 + 3 * SCR_ATTR['cardSpacing']
        widthAdj =  SCR_ATTR['cardHeight']/2 + SCR_ATTR['cardSpacing']
        
        if seatLabel == 'Bottom':
            adjX, adjY = 0, min(maxHeightAdj, heightAdj)
        elif seatLabel == 'Left':
            adjX, adjY = -min(maxWidthAdj, widthAdj), 0
        if seatLabel == 'Top':
            adjX, adjY = 0, -min(maxHeightAdj, heightAdj)
        elif seatLabel == 'Right':
            adjX, adjY = min(maxWidthAdj, widthAdj), 0
            
        x, y = self.get_rect().center
        rect = Rect(0, 0, SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight'])
        rect.center = x+adjX, y+adjY
        
        return rect
    
                            
class CardWIDGET(pygame.sprite.Sprite):

    def __init__(self, card, rotation, handLocation):
        pygame.sprite.Sprite.__init__(self) 

        #Set local variables
        self.card = card
        self.handLocation = handLocation
        
        #Draw card
        self.image, x = load_image(card.getSuit() + card.getValue() + '.png', 1)
        self.image = self.image.convert()
        self.image = pygame.transform.scale(self.image, (SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight']))
        self.image = pygame.transform.rotate(self.image, rotation)
        
#             dark = pygame.Surface((self.image.get_width(), self.image.get_height()), flags=pygame.SRCALPHA)
#             dark.fill((20, 20, 20, 0))
#             self.image.blit(dark, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)        
    
    def update(self):

        #Needs hand location to determine which way to select the card
        if self.card.isSelected:
            self.handLocation.selectCard(self, SCR_ATTR['cardSelectionSpacing'])

                
class Gui(pygame.Surface):
    def __init__(self, evManager):
        self.screen = pygame.display.set_mode((900, 600))
        pygame.display.set_caption('Hearts')
        pygame.Surface.__init__(self, self.screen.get_size())
        self.fill((SCR_ATTR['tableTop']))        
        self.seatLabels = ['Bottom', 'Left', 'Top', 'Right']
        self.handWIDGETS = []
        self.evManager = evManager
        self.evManager.registerListener(self)
        HandLocation().populateRectLookup(self, self.seatLabels)
        self.initializeRects()

        
    def notify(self,event):

        if isinstance(event, GameInitializedEvent):
            self.initializeGame(event.hands, event.board)            
        

    def initializeRects(self):
        RECT_LOOKUP[('Top Level', 'Top Level')] = Rect(0, 0, 900, 600)
        RECT_LOOKUP[('Top Level', 'Top')] = Rect(190, 0, 520, 230)
        RECT_LOOKUP[('Top', 'ScoreArea')] = Rect(0, 0, 520, 60)
        RECT_LOOKUP[('Top', 'Rectangle')] = Rect(0, 60, 520, 130)
        RECT_LOOKUP[('Top', 'CardSelected')] = Rect(5, 65, 80, 120)
        RECT_LOOKUP[('Top', 'CardNotSelected')] = Rect(5, 100, 80, 120)
        RECT_LOOKUP[('Top Level','Bottom')] = Rect(190, 370, 520, 230)
        RECT_LOOKUP[('Bottom', 'ScoreArea')] = Rect(0, 170, 520, 60)
        RECT_LOOKUP[('Bottom', 'Rectangle')] = Rect(0, 40, 520, 130)
        RECT_LOOKUP[('Bottom', 'CardSelected')] = Rect(5, 45, 80, 120)
        RECT_LOOKUP[('Bottom', 'CardNotSelected')] = Rect(5, 5, 80, 120)
        RECT_LOOKUP[('Top Level','Left')] = Rect(0, 190, 230, 220)
        RECT_LOOKUP[('Left', 'ScoreArea')] = Rect(0, 0, 60, 220)
        RECT_LOOKUP[('Left', 'Rectangle')] = Rect(60, 0, 130, 220)
        RECT_LOOKUP[('Left', 'CardSelected')] = Rect(65, 5, 80, 120)
        RECT_LOOKUP[('Left', 'CardNotSelected')] = Rect(100, 5, 80, 120)
        RECT_LOOKUP[('Top Level','Right')] = Rect(670, 190, 230, 220)
        RECT_LOOKUP[('Right', 'ScoreArea')] = Rect(170, 0, 60, 220)
        RECT_LOOKUP[('Right', 'Rectangle')] = Rect(40, 0, 130, 220)
        RECT_LOOKUP[('Right', 'CardSelected')] = Rect(45, 315, 80, 120)
        RECT_LOOKUP[('Right', 'CardNotSelected')] = Rect(5, 315, 80, 120)

        RECT_LOOKUP[('Top Level','Board')] = (190, 190, 520, 220)
        RECT_LOOKUP[('Board', 'Top')] = Rect(5, 315, 80, 120)
        RECT_LOOKUP[('Board', 'Right')] = Rect(5, 315, 80, 120)
        RECT_LOOKUP[('Board', 'Bottom')] = Rect(5, 315, 80, 120)
        RECT_LOOKUP[('Board', 'Left')] = Rect(5, 315, 80, 120)

        
        
    def initializeGame(self, hands, board):
        
        self.seatAssignment = self.mapSeatAssignment(hands)
        
        for seatLabel, hand in zip(self.seatLabels, hands):
            handLocation = HandLocationFactory(seatLabel).create()
            rect = RECT_LOOKUP[('HandArea', seatLabel)]
            handWIDGET = HandWIDGET(seatLabel, rect, self, hand, handLocation, self.evManager)
            self.handWIDGETS.append(handWIDGET)
        
        seatLabel = 'Board'    
        handLocation = HandLocationFactory(seatLabel).create()
        rect = handLocation.getBoardRect(self)
        boardWIDGET = BoardWIDGET(seatLabel, rect, self, board, handLocation, self.seatAssignment, self.evManager)
        self.board = boardWIDGET
        self.draw()

    def mapSeatAssignment(self, hands):
        
        seatAssignment = {}
        for hand,seatLabel in zip(hands, self.seatLabels):
            seatAssignment[hand.getName()] = seatLabel
        return seatAssignment
            
    def draw(self):
        self.board.draw()

        for hand in self.handWIDGETS:
            hand.draw()
        rect = Rect(0,0, 900, 600)
        pygame.display.get_surface().blit(self, rect)
        pygame.display.flip()

def main():

    pygame.init()

    players = ['Al', 'Bob', 'Carol', 'Doug']
    evManager = EventManager()
    gui = Gui(evManager)
    hearts = Hearts(players, evManager)
    controller = UIGameController(hearts, None, evManager)
    
    gui.draw()

    # Prepare Game Objects
    clock = pygame.time.Clock()
    # Main Loop
    going = True
    while going:
        clock.tick(30)

        # Handle Input Events
#       going = controller.processGUIEvents(pygame.event.get())

        # Draw Everything
 #       gui.update()
#        gui.draw()
 #       pygame.display.flip()


    pygame.quit()

# Game Over


# this calls the 'main' function when this script is executed
if __name__ == '__main__':
    main()
