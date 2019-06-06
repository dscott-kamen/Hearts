
# Import Modules
import os, pygame
from Hearts import Hearts
from Hand import Hand
from pygame.locals import *
from pygame import mouse
import importlib
from GameController import *
import time
from Deck import Card


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
SURFACE_LOOKUP = {}
BLIT_IMAGES = []

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
    
#    image = CACHED_IMAGES.get(name, None)
#    if image == None:
        fullname = os.path.join(getDataDir(), name)
        try:
            image = pygame.image.load(fullname).convert_alpha()
        except pygame.error as message:
            print('Cannot load image:', name)
            raise SystemExit(message)
        image = image.convert()
#        CACHED_IMAGES[name] = image    
        return image

def mouse_get_items(objects, mousePosition, topOnly=False):
    rect = Rect(mousePosition, (0,0))
    itemsFound = rect.collidelistall(objects)
    if itemsFound and topOnly:
        return [objects[itemsFound[-1]]]
    
    return itemsFound






class HandWIDGET(pygame.Surface):    

    def __init__(self, seatLabel, hand, evManager):
        #Call parent with size
        rect = RECT_LOOKUP[('TopLevel', seatLabel)]
        pygame.Surface.__init__(self, rect.size)
        
        self.hand = hand
        self.cardWIDGETS = []
        self.seatLabel = seatLabel
        self.changed = False
        self.evManager = evManager
        evManager.registerListener(self)
        
        self.initialize()

    def initialize(self):
        
        self.changed = True
                
        #Initialize Score Area
        rect = RECT_LOOKUP[(self.seatLabel, 'ScoreArea')]
        scoreArea = self.subsurface(rect)
        scoreArea.fill((0, 64, 255))
        
    def rebuildCardWIDGETS(self):
        
        #cleanup cards
#         background = SURFACE_LOOKUP['Background']
#         for card in self.cardWIDGETS:
#             self.blit(background, card.image.get_rect())
#         self.cardWIDGETS.clear()
        
        #recreate cards
        rotation = self.getRotation()
        for card in self.hand.cards:
            cardWIDGET = CardWIDGET(card, rotation, self.seatLabel)
            self.cardWIDGETS.append(cardWIDGET)

    def notify(self, event):
   
        if isinstance(event, CardSelectedEvent):
            if event.hand == self.hand:
                self.changed = True

        if isinstance(event, CardPlayedEvent):
            if event.hand == self.hand:
                self.changed = True

        if isinstance(event, PassCompleteEvent):
            self.changed = True
            
        if isinstance(event, TrickCompleteEvent):
            #animate trick completion
            self.changed = True
            
        if isinstance(event, TrickInitializedEvent):
            self.changed = True
                                        
        if isinstance(event, RoundCompleteEvent):
            self.changed = True
            
        if isinstance(event, RoundInitializedEvent):
            self.changed = True
            self.rebuildCardWIDGETS()
            
        if isinstance(event, GameInitializedEvent):
            self.changed = True
            self.rebuildCardWIDGETS()
              
    def getCardSpacing(self, spanRange, cardCount):
        if cardCount == 1 or spanRange > cardCount * (SCR_ATTR['cardWidth'] + SCR_ATTR['cardSpacing']):
            return SCR_ATTR['cardWidth'] + 0.5 * SCR_ATTR['cardSpacing']
        else:
            return int((spanRange - SCR_ATTR['cardWidth'] - 0.5 * SCR_ATTR['cardSpacing'])//(cardCount - 1))

    def getRotation(self):
        if self.seatLabel == 'Right':
            return 90
        elif self.seatLabel == 'Left':
            return -90
        else:
            return 0
        
    def draw(self):
        if self.changed:
            #Draw rectangle
            rect = RECT_LOOKUP[(self.seatLabel,'Rectangle')]
            pygame.draw.rect(self, SCR_ATTR['red'], rect, 1)

            self.drawCardArea()
            self.drawScoreArea()
            
            self.changed = False
    
    def getCardOffsetRect(self, rect, cardIndex, spacing):
        rect = rect.copy()
        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            rect.left = rect.left + cardIndex * spacing
        elif self.seatLabel == 'Left':
            rect.top = rect.top + cardIndex * spacing
        elif  self.seatLabel == 'Right':
            rect.bottom = rect.bottom - cardIndex * spacing
        return rect

    def drawCardArea(self):
        
        rect = RECT_LOOKUP[('TopLevel', self.seatLabel)]
        if self.seatLabel == 'Top' or self.seatLabel == 'Bottom':
            spanRange = rect.width
        else:
            spanRange = rect.height
        spacing = self.getCardSpacing(spanRange, len(self.hand.cards))
        
        cardAreaRect = RECT_LOOKUP[(self.seatLabel, 'Rectangle')]
        cardArea = self.subsurface(cardAreaRect)
        rect = RECT_LOOKUP[(self.seatLabel, 'CardNotSelected')]
        for i, cardWIDGET in enumerate(self.cardWIDGETS):
            cardRect = self.getCardOffsetRect(rect, i, spacing)
            cardArea.blit(cardWIDGET.image, cardRect)

    def drawScoreArea(self):
        
        rect = RECT_LOOKUP[(self.seatLabel, 'ScoreArea')]
        scoreArea = self.subsurface(rect)
        #create the score area surface
        scoreArea.fill((0, 64, 255))
        
        #Create rectangle
        pygame.draw.rect(scoreArea, SCR_ATTR['red'], scoreArea.get_rect(), 1)
        
        #create name text    
        font = pygame.font.Font(None, 36)
        text = font.render(self.hand.getName(), 1, (10, 10, 10))
#        nameText, textPos = self.handLocation.transformNameText(scoreArea, text)
#        scoreArea.blit(nameText, textPos)
        
        #create score text            
        font = pygame.font.Font(None, 24)
        text = font.render('Score: %d (%d)' % (self.hand.score.gameScore ,self.hand.score.roundScore), 1, (10, 10, 10))
#        scoreText, textPos = self.handLocation.transformScoreText(scoreArea, text)
#        scoreArea.blit(scoreText, textPos)
                                 
 
class BoardWIDGET(pygame.Surface):
    def __init__(self, board, seatAssignment, evManager):
        rect = RECT_LOOKUP[('TopLevel', 'Board')]
        pygame.Surface.__init__(self, rect.size)
        self.board = board
        self.seatAssignment = seatAssignment
        self.evManager = evManager
        self.evManager.registerListener(self)
        self.changed = True
        self.cardWIDGETS = []
        self.playOrder = []

    def notify(self, event):

        if isinstance(event, CardPlayedEvent):
            self.changed = True
            self.rebuildCardWIDGETS()

        if isinstance(event, TrickCompleteEvent):
            self.changed = True

        if isinstance(event, TrickInitializedEvent):
            self.changed = True
            self.setPlayOrder(event.playOrder)
            self.rebuildCardWIDGETS()

        if isinstance(event, GameInitializedEvent):
            self.changed = True
            
    def setPlayOrder(self, playOrder):
        self.playOrder = playOrder

    def rebuildCardWIDGETS(self):
        #cleanup and add new cards if number of cards has changed
        if len(self.cardWIDGETS) != len(self.board.cards):
            background = SURFACE_LOOKUP['Background']
            for card, hand  in zip(self.cardWIDGETS, self.playOrder):
                seatLabel = self.seatAssigment[hand.getName()]
#                self.blit(background, card.image.get_rect())
        
            for card in self.board.cards:
                cardWIDGET = CardWIDGET(card, 0, seatLabel)
                self.cardWIDGETS.append(cardWIDGET)
        
    def draw(self):
        pass
#         for card in self.cardWIDGETS:
#             rect = RECT_LOOKUP[('Board', card.seatLabel)]
#             self.blit(card, rect)

    
                            
class CardWIDGET(pygame.sprite.Sprite):

    def __init__(self, card, rotation, seatLabel):
        pygame.sprite.Sprite.__init__(self) 

        #Set local variables
        self.card = card
        self.seatLabel = seatLabel
        
        #Draw card
        self.image= load_image(card.getSuit() + card.getValue() + '.png', 1)
        self.image = pygame.transform.scale(self.image, (SCR_ATTR['cardWidth'], SCR_ATTR['cardHeight']))
        self.image = pygame.transform.rotate(self.image, rotation)
            

                
class Gui():
    def __init__(self, evManager):
        self.initializeRects()
        self.seatLabels = ['Bottom', 'Left', 'Top', 'Right']
        self.handWIDGETS = []
        self.evManager = evManager
        self.evManager.registerListener(self)
        
        
        #Draw initial screen
        self.initializeBackground()
        self.preloadCardImages()

        
    def initializeBackground(self):
            rect = RECT_LOOKUP['TopLevel', 'TopLevel']
            screen = pygame.display.set_mode(rect.size)
            pygame.display.set_caption('Hearts')
            background = pygame.Surface(rect.size)
            background.fill((SCR_ATTR['tableTop']))
            SURFACE_LOOKUP['Background'] = background        
        
            screen.blit(background, rect)
            pygame.display.flip()

    def notify(self,event):

        if isinstance(event, GameInitializedEvent):
            self.initializeGame(event.hands, event.board)            
        

    def initializeRects(self):
        RECT_LOOKUP[('TopLevel', 'TopLevel')] = Rect(0, 0, 900, 600)
        RECT_LOOKUP[('TopLevel', 'Top')] = Rect(190, 0, 520, 230)
        RECT_LOOKUP[('Top', 'ScoreArea')] = Rect(0, 0, 520, 60)
        RECT_LOOKUP[('Top', 'Rectangle')] = Rect(0, 60, 520, 130)
        RECT_LOOKUP[('Top', 'CardNotSelected')] = Rect(5, 65, 80, 120)
        RECT_LOOKUP[('Top', 'CardSelected')] = Rect(5, 100, 80, 120)
        RECT_LOOKUP[('TopLevel','Bottom')] = Rect(190, 370, 520, 230)
        RECT_LOOKUP[('Bottom', 'ScoreArea')] = Rect(0, 170, 520, 60)
        RECT_LOOKUP[('Bottom', 'Rectangle')] = Rect(0, 40, 520, 130)
        RECT_LOOKUP[('Bottom', 'CardSelected')] = Rect(5, 5, 80, 120)
        RECT_LOOKUP[('Bottom', 'CardNotSelected')] = Rect(5, 45, 80, 120)
        RECT_LOOKUP[('TopLevel','Left')] = Rect(0, 190, 230, 220)
        RECT_LOOKUP[('Left', 'ScoreArea')] = Rect(0, 0, 60, 220)
        RECT_LOOKUP[('Left', 'Rectangle')] = Rect(60, 0, 130, 220)
        RECT_LOOKUP[('Left', 'CardSelected')] = Rect(65, 5, 80, 120)
        RECT_LOOKUP[('Left', 'CardNotSelected')] = Rect(100, 5, 80, 120)
        RECT_LOOKUP[('TopLevel','Right')] = Rect(670, 190, 230, 220)
        RECT_LOOKUP[('Right', 'ScoreArea')] = Rect(170, 0, 60, 220)
        RECT_LOOKUP[('Right', 'Rectangle')] = Rect(40, 0, 130, 220)
        RECT_LOOKUP[('Right', 'CardSelected')] = Rect(45, 315, 80, 120)
        RECT_LOOKUP[('Right', 'CardNotSelected')] = Rect(5, 315, 80, 120)

        RECT_LOOKUP[('TopLevel','Board')] = Rect(190, 190, 520, 220)
        RECT_LOOKUP[('Board', 'Top')] = Rect(5, 315, 80, 120)
        RECT_LOOKUP[('Board', 'Right')] = Rect(5, 315, 80, 120)
        RECT_LOOKUP[('Board', 'Bottom')] = Rect(5, 315, 80, 120)
        RECT_LOOKUP[('Board', 'Left')] = Rect(5, 315, 80, 120)

    def preloadCardImages(self):
        for suit in Card.SUIT:
            for value in Card.VALUE:
                load_image('%s%s.png' % (suit, value))
                
        
    def initializeGame(self, hands, board):
        
        self.seatAssignment = self.mapSeatAssignment(hands)

        for seatLabel, hand in zip(self.seatLabels, hands):
            handWIDGET = HandWIDGET(seatLabel, hand, self.evManager)
            self.handWIDGETS.append(handWIDGET)
        
        boardWIDGET = BoardWIDGET(board, self.seatAssignment, self.evManager)
        self.board = boardWIDGET

    def draw(self):
        self.board.draw()
        rect = RECT_LOOKUP[('TopLevel', 'Board')]
        pygame.display.get_surface().blit(self.board, rect)
        
        
        for hand in self.handWIDGETS:
            hand.draw()
            rect = RECT_LOOKUP[('TopLevel', hand.seatLabel)]
            pygame.display.get_surface().blit(hand, rect)
            
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
        print('main loop')
        # Handle Input Events
#       going = controller.processGUIEvents(pygame.event.get())

        # Draw Everything
#        gui.update()
        gui.draw()
 #       pygame.display.flip()


    pygame.quit()

# Game Over


# this calls the 'main' function when this script is executed
if __name__ == '__main__':
    main()
