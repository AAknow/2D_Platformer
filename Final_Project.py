import pygame, sys
from pygame.locals import *
import random
import os
import sys

pygame.init()
pygame.display.toggle_fullscreen

# -------------------------
# Initializing Variables
# -------------------------

# Function to get the correct path for resources if run on different OS
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running in development mode (not bundled)
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Window name
pygame.display.set_caption("Final Project")

# Flags for fullscreen and doublebuffering
flags = FULLSCREEN | DOUBLEBUF

# Screen 
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
DISPLAYSURF = pygame.display.set_mode((1600, 900), flags)

# Physics
vec = pygame.math.Vector2
ACC = 1
FRIC = -0.12

# Framerate
FPS = 60
FramePerSec = pygame.time.Clock()

# Background
BACKGROUND = pygame.image.load(resource_path("Background.png"))
BACKGROUND = pygame.transform.scale(BACKGROUND, (1600, 900))

# shooting action variable
shoot = False

# load bullet image
bullet_img = pygame.image.load(resource_path("Bullet.png")).convert_alpha()

# Scoreboard variable
SCOREBOARD = 0

# Scoreboardn font and color
font = pygame.font.Font(None, 74)
textColor = (255, 255, 255)

# Game over text
GAME_OVER = "Game Over"

# -------------------------
# Game Classes
# -------------------------

# Player Class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # player health
        self.health = 5
        # check if player is jumping
        self.jumping = False
        # cooldowns
        self.shoot_cooldown = 0
        # get sprite image
        self.alive = True
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # loop through animation folders
        temp_list = []
        for i in range(1):
            img = pygame.image.load(resource_path(f'Player_Idle/{i}.png')).convert_alpha()
            temp_list.append(img)
        self.animation_list.append(temp_list)
        temp_list = []
        for i in range(5):
            img = pygame.image.load(resource_path(f'Player_Walking/{i}.png')).convert_alpha()
            temp_list.append(img)
        self.animation_list.append(temp_list)
        temp_list = []
        for i in range(1):
            img = pygame.image.load(resource_path(f'Player_Jumping/{i}.png')).convert_alpha()
            temp_list.append(img)
        self.animation_list.append(temp_list)
        # set image to current frame of current action
        self.image = self.animation_list[self.action][self.frame_index]

        # set player rectangle
        self.rect = self.image.get_rect()
        
        # direction of sprite
        self.direction = 1
        self.flip = False
        
        # Physics
        self.pos = vec((SCREEN_WIDTH/2, SCREEN_HEIGHT))
        self.vel = vec(0,0)
        self.acc = vec(0,0)
        
    def move(self):
        # Player Gravity
        self.acc = vec(0,.6)
        # Left and Right movement
        pressed_keys = pygame.key.get_pressed()
        if self.alive:
            if pressed_keys[K_a]:
                self.acc.x = -ACC + .4
                # flip sprite to face the left
                self.flip = False
                self.direction = 1
            if pressed_keys[K_d]:
                self.acc.x = ACC - .4
                # flip sprite to face the left
                self.flip = True
                self.direction = -1
        # calculate physics
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc
        # Screen warping (left to right and vice versa)
        if self.pos.x > SCREEN_WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = SCREEN_WIDTH
        self.rect.midbottom = self.pos

    # Jumping
    def jump(self):
        self.jumping = True
        # if on platform
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits:
            self.vel.y = -19

    def shoot(self):
        if self.alive:
            if self.shoot_cooldown == 0:
                self.shoot_cooldown = 20
                bullet = Bullet(self.rect.centerx - (.7 * self.rect.size[0] * self.direction), \
                        self.rect.centery - (self.rect.size[1] / 4.5), self.direction)
                if self.direction < 0:
                    bullet.image = pygame.transform.flip(bullet.image, self.flip, False)
                bullet_group.add(bullet)

    # checks if player is alive
    def check_alive(self):
        if self.health <= 0:
            self.alive = False
            self.kill()

    # Collision rectangle for Player
    def draw(self, surface):
        surface.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

    def update_ground_collision(self):
        hits = pygame.sprite.spritecollide(P1 , platforms, False)
        if self.vel.y > 0:
            self.jumping = True
            try:
                if hits[0].rect.top < self.rect.bottom:
                    self.pos.y = hits[0].rect.top
                    self.vel.y = 0
                    self.jumping = False
            except IndexError:
                pass

    def update(self):
       # update player state
        self.check_alive()
        # call animation method
        self.update_animation()
        # call ground collision method
        self.update_ground_collision()
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
    # Changes player image to animate actions 
    def update_animation(self):
        # update animation
        ANIMATION_COOLDOWN = 100
        # update animation depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        # check time
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # if the animation runs out then start over
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

    def update_action(self, new_action):
        # check if new action is different than previous action
        if new_action != self.action:
            self.action = new_action
            # update the animation setting
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
        
# Enemy Class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # enemy health
        self.health = 2
        # cooldowns
        self.walk_cooldown = 0
        self.shoot_cooldown = 0
        # check if enemy is jumping
        self.jumping = False
        # direction of sprite
        self.direction = 1
        self.flip = True
        # get sprite image
        self.alive = True
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # loop through animation folders
        temp_list = []
        for i in range(1):
            img = pygame.image.load(resource_path(f'Enemy_Idle/{i}.png')).convert_alpha()
            temp_list.append(img)
        self.animation_list.append(temp_list)
        temp_list = []
        for i in range(5):
            img = pygame.image.load(resource_path(f'Enemy_Walking/{i}.png')).convert_alpha()
            temp_list.append(img)
        self.animation_list.append(temp_list)
        temp_list = []
        for i in range(1):
            img = pygame.image.load(resource_path(f'Enemy_Jumping/{i}.png')).convert_alpha()
            temp_list.append(img)
        self.animation_list.append(temp_list)
        # set image to current frame of current action
        self.image = self.animation_list[self.action][self.frame_index]
        # set player rectangle
        self.rect = self.image.get_rect()
        # direction of sprite
        self.direction = 1
        self.flip = False
        # Physics
        self.pos = vec((x, y))
        self.vel = vec(0,0)
        self.acc = vec(0,0)
        
    def move(self, surface):
        # Enemy Gravity
        self.acc = vec(0,.6)
        # Enemy movement behavior
        if self.alive:
            if self.walk_cooldown > 800:
                self.walk_cooldown = 0
            if self.walk_cooldown < 350:
                # move right
                self.acc.x = ACC - .4
            else:
                # move left
                self.acc.x = -ACC + .4
            if str(self.walk_cooldown).endswith("00"):
                self.jump()
        # increase walk cooldown with every game loop
        self.walk_cooldown += 1
        # calculate physics
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc
        # update enemy action
        if self.acc.x != 0:
            self.update_action(1) # 1 is walking
        else:
            self.update_action(0) # 0 is Idle
        # sprite direction
        if self.acc.x < 0:
            # flip sprite to face the right
            self.flip = False
            self.direction = 1
        else:
            # flip sprite to face the left
            self.flip = True
            self.direction = -1
        # Screen warping (left to right and vice versa)
        if self.pos.x > SCREEN_WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = SCREEN_WIDTH
        self.rect.midbottom = self.pos

    # Jumping
    def jump(self):
        self.jumping = True
        # if on platform
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits:
            self.vel.y = -19

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 80
            bullet = Bullet(self.rect.centerx - (.7 * self.rect.size[0] \
                            * self.direction),self.rect.centery \
                            - (self.rect.size[1] / 4.5), self.direction)
            if self.direction < 0:
                bullet.image = pygame.transform.flip(bullet.image, self.flip, False)
            bullet_group.add(bullet)

    # checks if enemy is alive
    def check_alive(self):
        # if the enemy is dead, remove it
        if self.health <= 0:
            self.alive = False
            self.kill()

    # Collision Rectangle for Enemy
    def draw(self, surface):
        surface.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

    # Changes player image to animate actions 
    def update_animation(self):
        # update animation
        ANIMATION_COOLDOWN = 100
        # update animation depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        # check time
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # if the animation runs out then start over
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

    def update_action(self, new_action):
        # check if new action is different than previous action
        if new_action != self.action:
            self.action = new_action
            # update the animation setting
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def update(self):
        # update enemy stae
        self.check_alive()
        # shoot if alive
        if self.alive:
            self.shoot()
        # call ground collision method
        self.update_ground_collision()
        # check if enemy is jumping
        if self.jumping:
            self.update_action(2) # 2 is jumping 
        # check for platform collision
        hits = pygame.sprite.spritecollide(self , platforms, False)
        if self.vel.y > 0:
            if hits:
                self.pos.y = hits[0].rect.top + 1
                self.vel.y = 0
        # update cooldown
        self.update_animation()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def update_ground_collision(self):
        hits = pygame.sprite.spritecollide(self , platforms, False)
        if self.vel.y > 0:
            self.jumping = True
            try:
                if hits[0].rect.top < self.rect.bottom:
                    self.pos.y = hits[0].rect.top
                    self.vel.y = 0
                    self.jumping = False
            except IndexError:
                pass
        
# Bullet Class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 12
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # move bullet
        self.rect.x += ((-1 * self.direction) * self.speed)
        # check if bullet exits the scren
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        # check if bullet collides with sprite
        if pygame.sprite.spritecollide(P1, bullet_group, False):
            if P1.alive:
                self.kill()
                P1.health -= 1
        for enemy in enemy_sprites:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    self.kill()
                    enemy.health -= 1

# Platform Class
class Platform(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((SCREEN_WIDTH, 20))
        self.surf.fill((255,0,0))
        self.rect = self.surf.get_rect(center = (SCREEN_WIDTH/2, SCREEN_HEIGHT - 40))

# -------------------------
# Objects and Sprites
# -------------------------

# Sprite Groups
all_sprites = pygame.sprite.Group()
enemy_sprites = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
platforms = pygame.sprite.Group()

# Player and Platform variables
P1 = Player()
PT1 = Platform()
PT2 = Platform()
PT3 = Platform()
PT4 = Platform()
PT5 = Platform()

# Add objects to sprite groups
all_sprites.add(P1)
for i in range(5):
    # adds each platform to both sprite groups
    platform = eval(f"PT{i + 1}")
    all_sprites.add(platform)
    platforms.add(platform)

# Platform Creation and Positioning
PT1.surf = pygame.Surface((SCREEN_WIDTH, 20), pygame.SRCALPHA)
PT1.surf.fill((0,0,0,0))
PT1.rect = PT1.surf.get_rect(center = (SCREEN_WIDTH/2, SCREEN_HEIGHT - 40))

PT2.surf = pygame.Surface((640, 20), pygame.SRCALPHA)
PT2.surf.fill((0,0,0,0))
PT2.rect = PT2.surf.get_rect(center = (SCREEN_WIDTH/2 - 30, SCREEN_HEIGHT - 238))

PT3.surf = pygame.Surface((650, 20), pygame.SRCALPHA)
PT3.surf.fill((0,0,0,0))
PT3.rect = PT3.surf.get_rect(center = (SCREEN_WIDTH/SCREEN_WIDTH + 15, \
                                       SCREEN_HEIGHT - 465))

PT4.surf = pygame.Surface((670, 20), pygame.SRCALPHA)
PT4.surf.fill((0,0,0,0))
PT4.rect = PT4.surf.get_rect(center = (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 492))

PT5.surf = pygame.Surface((500, 20), pygame.SRCALPHA)
PT5.surf.fill((0,0,0,0))
PT5.rect = PT5.surf.get_rect(center = (SCREEN_WIDTH/2 + 5, SCREEN_HEIGHT - 625))

# -------------------------
# Game Loop
# -------------------------

while True:

    # updates player
    P1.update()
    P1.move()

    # updates and draws enemy
    for enemy in enemy_sprites:
        enemy.move(DISPLAYSURF)
        enemy.update()
        # adds 50 points to score when enemy is killed
        if enemy.alive == False:
            SCOREBOARD += 50
    
    # update and draw bullets
    bullet_group.update()
    
    # player shooting
    if shoot: 
        P1.shoot()
        
    # change action
    pressed_keys = pygame.key.get_pressed()
    if P1.alive:
        if P1.jumping:
            P1.update_action(2) # 2 is jumping
        elif pressed_keys[K_a] or pressed_keys[K_d]:
            P1.update_action(1) # 1 is walking
        else:
            P1.update_action(0) # 0 is Idle

    # events check
    for event in pygame.event.get():
        # exits game if user triggers QUIT event
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        # check if key is pressed
        if P1.alive:
            if event.type == pygame.KEYDOWN:    
                if event.key == pygame.K_w:
                    P1.jump()
                if event.key == pygame.K_SPACE:
                    shoot = True
            # check if button is released
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    shoot = False

    # Display images
    DISPLAYSURF.blit(BACKGROUND, (0, 0))
    if P1.alive:
        P1.draw(DISPLAYSURF)
    bullet_group.draw(DISPLAYSURF)
    DISPLAYSURF.blit(PT1.surf, PT1.rect)
    DISPLAYSURF.blit(PT2.surf, PT2.rect)
    DISPLAYSURF.blit(PT3.surf, PT3.rect)
    DISPLAYSURF.blit(PT4.surf, PT4.rect)
    DISPLAYSURF.blit(PT5.surf, PT5.rect)
    for enemy in enemy_sprites:
        enemy.draw(DISPLAYSURF)

    # When there are no enemies
    if len(enemy_sprites) == 0:
        P1.health = 5
        # create 3 to 6 enemies
        for enemy in range(random.randint(3, 6)):
            # set random starting point
            enemy = Enemy(random.randint(100, 1500), random.randint(45, 800))
            # set random stage of movement cooldown
            enemy.walk_cooldown = random.randint(1, 800)
            # add enemy to sprite groups
            all_sprites.add(enemy)
            enemy_sprites.add(enemy)

    # Display Scoreboard
    text = font.render(str(SCOREBOARD), True, textColor)
    DISPLAYSURF.blit(text, (10, SCREEN_HEIGHT - 48))

    # Display Game Over
    if P1.alive == False:
        text = font.render(str(GAME_OVER), True, textColor)
        DISPLAYSURF.blit(text, (SCREEN_WIDTH/2 - 120, SCREEN_HEIGHT/2))

    # updates game at preset FPS
    pygame.display.update()
    FramePerSec.tick(FPS)
