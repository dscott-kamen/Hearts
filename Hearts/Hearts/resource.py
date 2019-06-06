# Import Modules
import os, pygame
from pygame.locals import *
import math

if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')

IMAGE_CACHE = {}

def getDataDir():
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    return os.path.join(main_dir, 'data')

def mouse_get_items(objects, mousePosition, topOnly=False):
    rect = Rect(mousePosition, (0,0))
    itemsFound = rect.collidelistall(objects)
    if itemsFound and topOnly:
        return [objects[itemsFound[-1]]]
    
    return itemsFound

def get_absolute_rect(rect, parentRect):
    return Rect(rect.x+parentRect.x, rect.y+parentRect.y, rect.width, rect.height)

def calculateMoveXY(startRect, endRect, moveSpeed):
    angle = math.atan2(endRect.y - startRect.y, endRect.x - startRect.x)
    return moveSpeed*math.cos(angle), moveSpeed*math.sin(angle) 


def load_image(name, colorkey=None, size=None):
    
    image = IMAGE_CACHE.get((name, size), None)
    if image == None:

        fullname = os.path.join(getDataDir(), name)
        try:
            image = pygame.image.load(fullname).convert_alpha()
            if size is not None:
                image = pygame.transform.scale(image, size)
            IMAGE_CACHE[name, size] = image
#        image = pygame.transform.rotate(image, 90)
        except pygame.error as message:
            print('Cannot load image:', name)
            raise SystemExit(message)
    return image
