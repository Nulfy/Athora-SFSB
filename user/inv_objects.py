import os.path

import pygame

from world.npc import Bullet

WHITE = (255, 255, 255)


# Returns a surface with text in the game font
def render_text(text, px):
    font = pygame.font.Font(os.path.join('assets', 'fonts', 'pressstart.ttf'), px)
    return font.render(text, True, WHITE)


# An object that can be held by the player in the inventory
class InventoryObject:

    # Variables that will be assigned the name of the object and its texture file
    NAME: str
    TEXTURE_FILE: str
    TEXTURE: pygame.Surface
    TEXTURE_WIDTH, TEXTURE_HEIGHT = 80, 80

    # Initialise the name and texture of the object
    def __init__(self, name, texture):
        self.NAME = name
        self.TEXTURE_FILE = texture
        self.TEXTURE_IMG = pygame.image.load(os.path.join('assets', 'textures', 'items', texture)).convert_alpha()
        self.TEXTURE = pygame.transform.scale(self.TEXTURE_IMG, (self.TEXTURE_WIDTH, self.TEXTURE_HEIGHT))

    # Draw the texture of the object at the coordinates of the slot it is in
    def draw(self, surface, index, slot):
        surface.blit(self.TEXTURE, slot)
        if pygame.player.inventory_selected_slot == index:
            name = render_text(self.NAME, 15)
            surface.blit(name, (slot[0] + 80 / 2 - name.get_width() / 2, slot[1] - 20))

    # A method that is called when the object is used
    # Does nothing if this method isn't altered in the subclass
    def use(self):
        pass


# An extension of the InventoryObject which serves as a healing potion for the player
class Potion(InventoryObject):

    NAME = 'Potion'
    TEXTURE = 'potion.png'

    # A sound that is played when the object is used
    DRINK_SOUND = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'player', 'gulp.wav'))

    # An event that is called when the object is used, along with the amount of health points the player can gain from it
    DRINK = pygame.USEREVENT + 5
    DRINK_EVENT = pygame.event.Event(DRINK)
    hp: int

    # Initialise the health points
    def __init__(self, hp=2):
        super().__init__(self.NAME, self.TEXTURE)
        self.hp = hp

    # Post the event and play the sound when the item is used
    def use(self):
        self.DRINK_SOUND.play()
        self.DRINK_EVENT.potion = self
        pygame.event.post(self.DRINK_EVENT)


# An extension of the InventoryObject used as a way for the player to end the game
class MagentaCartridge(InventoryObject):

    NAME = 'Magenta Ink Cartridge'
    TEXTURE = 'magenta_cartridge.png'

    WIN = pygame.USEREVENT + 4
    WIN_EVENT = pygame.event.Event(WIN)

    def __init__(self):
        super().__init__(self.NAME, self.TEXTURE)

    def use(self):
        pygame.event.post(self.WIN_EVENT)


# An extension of the InventoryObject used as a placeholder for ammo
class Ammo(InventoryObject):

    NAME = 'Ammo'
    TEXTURE = 'ammo.png'

    PICKUP = pygame.USEREVENT + 9
    PICKUP_EVENT = pygame.event.Event(PICKUP)

    AMOUNT: int

    def __init__(self, amt=10):
        super().__init__(self.NAME, self.TEXTURE)
        self.AMOUNT = amt

    def use(self):
        self.PICKUP_EVENT.obj = self
        pygame.event.post(self.PICKUP_EVENT)



# An extension of the InventoryObject which serves as a weapon for the player
class Gun(InventoryObject):

    NAME = 'Pistol'
    TEXTURE = 'gun.png'

    # Text that is shown and a sound that is played when it is reloaded
    RELOAD_TEXT: str
    RELOAD_SOUND = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'player', 'reload.wav'))
    RELOAD_CHANNEL = pygame.mixer.Channel(3)

    reloading = 0

    # Stores how many bullets are in the chamber
    EMPTY = False
    chamber = 3

    def __init__(self):
        super().__init__(self.NAME, self.TEXTURE)

    # Draws the number of bullets in the chamber in the slot it is in
    def draw(self, surface, index, slot):
        super().draw(surface, index, slot)
        bullets = render_text(str(self.chamber), 15)
        surface.blit(bullets, (slot[0] + 70 - bullets.get_width(), slot[1] + 70 - bullets.get_height()))
        if self.chamber == 0:
            if pygame.player.get_ammo() > 0:
                self.RELOAD_TEXT = "'R' to reload"
            else:
                self.RELOAD_TEXT = 'No ammo'
            self.EMPTY = True
            if self.RELOAD_CHANNEL.get_busy() and not self.reloading:
                self.reloading = 1
            if self.reloading:
                if not self.RELOAD_CHANNEL.get_busy():
                    self.EMPTY = False
                    self.set_ammo()
                    self.reloading = 0

    def set_ammo(self):
        if pygame.player.ammo >= 3:
            self.chamber = 3
            pygame.player.add_ammo(-3)
            return
        if pygame.player.ammo > 0:
            self.chamber = pygame.player.ammo
            pygame.player.add_ammo(-pygame.player.ammo)
            return

    # Release a bullet and decrement the bullets in the chamber when used
    def use(self):
        if self.chamber == 0 or self.RELOAD_CHANNEL.get_busy():
            return
        x = 0
        y = pygame.player.rect.y + (pygame.player.rect.h / 2)
        direction = 0
        if pygame.player.direction[pygame.player.LEFT]:
            x = pygame.player.rect.x
            direction = pygame.player.LEFT
        if pygame.player.direction[pygame.player.RIGHT]:
            x = pygame.player.rect.x + pygame.player.rect.w
            direction = pygame.player.RIGHT
        pygame.level.level_bullets.append(Bullet(x, y, direction, pygame.player))
        self.chamber -= 1

    # Top up the chamber if it is empty, and play reload noise
    def reload(self):
        if self.chamber == 0 and not self.RELOAD_CHANNEL.get_busy() and not pygame.player.get_ammo() == 0:
            self.RELOAD_CHANNEL.play(self.RELOAD_SOUND)
