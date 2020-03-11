import tcod.event
import random
import time
from random import randint

"""
This class depicts any object on the game map; in our case, a door, a key or a player.
It stores the coordinates, the symbol for the object,
whether the player had a chance to notice it (for doors and keys), and whether player has picked it up (for keys).
"""
class Entity:
    def __init__(self, x, y, char, colour, visible=True, picked=False):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
        self.visible = visible
        self.picked = picked

#This places the object on the game map
    def draw(self):
        tcod.console_put_char_ex(con, self.x, self.y, self.char, self.colour, tcod.black)

#This moves the object (only applicable to player)
    def move(self, dx, dy):
        if not dungeon[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy

#This erases the object from the map by replacing it with a floor tile
    def remove(self):
        tcod.console_put_char_ex(con, self.x, self.y, ".", tcod.dark_gray, tcod.black)


"""
This class is for walls and floors: if it's blocked, it's a wall tile, a floor tile otherwise
"""
class Block:
    def __init__(self, blocked):
        self.blocked = blocked


#This is used in cutscenes to allow game quit
def await_cutscene_controls():
    tcod.console_wait_for_keypress(True)
    if tcod.console_is_key_pressed(tcod.KEY_ESCAPE):
        exit()


#This is used in the credits
def await_ending_controls():
    tcod.console_wait_for_keypress(True)
    exit()


#This processes the arrow input from the player, moving the character
def await_keyboard_input():
    tcod.console_wait_for_keypress(True)
    if tcod.console_is_key_pressed(tcod.KEY_ESCAPE):
        exit()
    if tcod.console_is_key_pressed(tcod.KEY_LEFT):
        Player.move(-1, 0)
    if tcod.console_is_key_pressed(tcod.KEY_RIGHT):
        Player.move(1, 0)
    if tcod.console_is_key_pressed(tcod.KEY_UP):
        Player.move(0, -1)
    if tcod.console_is_key_pressed(tcod.KEY_DOWN):
        Player.move(0, 1)


#This function creates a 2D array of coordinates which will be the map and "fills" it with wall tiles
def map_create():
    global dungeon
    dungeon = [[Block(True) for y in range(DungeonHeight)] for x in range(DungeonWidth + 1)]


#This function generates a randomly sized room and connects in with the previous one with a corridor n times
def gen_rooms_n_corridors():
    n = 80
#It chooses the random starting position and size of a room
    dx1 = randint(10, 30)
    dy1 = randint(10, 30)
    x1 = randint(1, DungeonWidth - dx1 - 3)
    y1 = randint(1, DungeonHeight - dy1 - 3)
    Occupied = 0
#This loop checks if there already are floor tiles within the chosen coordinates; if so, the room will not be generated
    for CheckerX in range(x1, x1 + dx1):
        for CheckerY in range(y1, y1 + dy1):
            if not dungeon[CheckerX][CheckerY].blocked:
                Occupied += 1
#But if the space is free, this bit of code will "carve" the floor tiles
    if Occupied == 0:
        for CheckerX in range(x1, x1 + dx1 + 1):
            for CheckerY in range(y1, y1 + dy1 + 1):
                dungeon[CheckerX][CheckerY] = Block(False)


#As you might have noticed, the block above only generates one room - the first room.
#The rest is done by the code below, and the reason behind that is that
#this way we store the coordinates of the first room (x1, y1, dx1 and dy1) in order to connect it with the new room.

    for CounterRooms in range(n - 1):
        dx2 = randint(10, 30)
        dy2 = randint(10, 30)
        x2 = randint(1, DungeonWidth - dx2 - 2)
        y2 = randint(1, DungeonHeight - dy2 - 2)
        Occupied = 0
        for CheckerX in range(x2, x2 + dx2):
            for CheckerY in range(y2, y2 + dy2):
                if not dungeon[CheckerX][CheckerY].blocked:
                    Occupied += 1
        if Occupied == 0:
            for CheckerX in range(x2, x2 + dx2 + 1):
                for CheckerY in range(y2, y2 + dy2 + 1):
                    dungeon[CheckerX][CheckerY] = Block(False)

#The code above does the same, but with a separate set of coordinates
#The code below, however, picks a random coordinate of the rooms' border tiles...
            CorridorStartX = x2 + int(dx2 / randint(7, 20))
            CorridorStartY = y2 + int(dy2 / randint(7, 20))
            CorridorEndX = x1 + int(dx1 / randint(7, 20))
            CorridorEndY = y1 + int(dy1 / randint(7, 20))
#And connects them with a corridor, "carving" through walls the same way the room generator did
#First on X axis
            for IteratorX in range(min(CorridorStartX, CorridorEndX), max(CorridorStartX, CorridorEndX)):
                dungeon[IteratorX][CorridorStartY].blocked = False
#Then on Y axis
            for IteratorY in range(min(CorridorStartY, CorridorEndY), max(CorridorStartY, CorridorEndY)):
                dungeon[CorridorEndX][IteratorY].blocked = False
#The coords of the "new" room then become ones of the "old" room, and a new room is generated.
            dy1 = dy2
            dx1 = dx2
            x1 = x2
            y1 = y2


#This function renders the tiles, drawing walls as hashes and floors as dots
def render_dungeon():
    for CheckerX in range(DungeonWidth + 1):
        for CheckerY in range(DungeonHeight):
            if dungeon[CheckerX][CheckerY].blocked:
                tcod.console_put_char_ex(con, CheckerX, CheckerY, "#", tcod.light_gray, tcod.black)
            if not dungeon[CheckerX][CheckerY].blocked:
                tcod.console_put_char_ex(con, CheckerX, CheckerY, ".", tcod.dark_gray, tcod.black)


"""
This one is interesting. Since we only carved the rooms and corridors, they will still be "buried"
in walls instead of having one-layer-thick walls. This function erases the walls that are not connected to
floor tiles from any side.
Oh, and it also creates a solid line which separates the HUD from the map.
This is the most resource-intensive function in the script.
"""
def clear_walls():
    for CheckerX in range(DungeonWidth):
        for CheckerY in range(DungeonHeight - 1):
            if dungeon[CheckerX - 1][CheckerY + 1].blocked:
                if dungeon[CheckerX - 1][CheckerY - 1].blocked:
                    if dungeon[CheckerX - 1][CheckerY].blocked:
                        if dungeon[CheckerX][CheckerY].blocked:
                            if dungeon[CheckerX][CheckerY - 1].blocked:
                                if dungeon[CheckerX][CheckerY + 1].blocked:
                                    if dungeon[CheckerX + 1][CheckerY].blocked:
                                        if dungeon[CheckerX + 1][CheckerY - 1].blocked:
                                            if dungeon[CheckerX + 1][CheckerY + 1].blocked:
                                                tcod.console_put_char_ex(con, CheckerX, CheckerY, " ", tcod.black,
                                                                         tcod.black)
        tcod.console_put_char_ex(con, CheckerX, DungeonHeight, "-", tcod.white, tcod.black)


#Well, this is to make it even prettier-looking
def generate_terrain():
    map_create()
    gen_rooms_n_corridors()
    render_dungeon()
    clear_walls()


"""
This one is also called each turn.
What it does for doors is it checks if the player is close enough and makes the player "notice" them when it is so.
For keys it also checks if it's possible to connect the key and the player with two lines: one vertical and one horizontal;
it's basically a pathfinding system in order to not allow the player to see through walls.
The same thing for doors is not implemented because the storyline builds around you hearing them.
"""
def process_fov():
    if not Door.visible:
        DoorWalled = True
        for CheckerX in range(-10, 11):
            for CheckerY in range(-10, 11):
                if Player.x + CheckerX == Door.x and Player.y + CheckerY == Door.y:
                    DoorWalled = False
        if not DoorWalled:
            Door.visible = True

#If the key has not already been discovered...
    if not Key.visible:
        #The key cannot be discovered at first
        KeyWalled = True
#...it checks if it's within range
        for CheckerX in range(-15, 16):
            for CheckerY in range(-15, 16):
                if Player.x + CheckerX == Key.x and Player.y + CheckerY == Key.y:
                    KeyWalled = False
#If it is, it makes the key be allowed to be discovered and checks if it can be accessed
                    for IteratorX in range(min(Player.x, Key.x), max(Player.x, Key.x)):
#If it can't be accessed, i.e. there are walls in the way, then it forbids the key to be discovered
                        if dungeon[IteratorX][Player.y].blocked:
                            KeyWalled = True
                    for IteratorY in range(min(Player.y, Key.y), max(Player.y, Key.y)):
                        if dungeon[Player.x + CheckerX][IteratorY].blocked:
                            KeyWalled = True
#If the key is not blocked by walls, but is within range, discover the key
        if not KeyWalled:
            Key.visible = True


#This function prints text in the bottom message box depending on the player's progression. As simple as can be.
def draw_gui():
    gui.clear()
#We render the GUI in a separate console...
    if Level == 2:
        gui.print(2, 1, "You wake up in one of the administrative buildings of the Chernobyl power plant.", tcod.white)
        gui.print(2, 3, "Former power plant, it seems.", tcod.white)
        gui.print(2, 5, "Your workspace is in ruins, the fire alarm is blaring in the distance, and the only light sources are the emergency lights.", tcod.white)
        gui.print(2, 7, "There are 5 emergency staircases in this facility; luckily, you'll only have to use three of them to reach ground level", tcod.white)
        gui.print(2, 9, "You've never used them, however, so you have no idea where they are.", tcod.white)
        gui.print(2, 11, "They also require a keycard to access. Whoever built this certainly valued data security more than the security of the personnel.", tcod.white)
        gui.print(2, 13, "You need to find both the exit and the key to escape.", tcod.red)
        gui.print(56, 13, "They will be marked golden on your map once you get close enough.", tcod.gold)
        if Key.picked:
            gui.print(2, 17, "You have the key!", tcod.white)
        if Door.visible:
            gui.print(2, 15, "You hear the fire alarm getting louder. This must be the exit.", tcod.white)

    if Level == 1:
        gui.print(2, 1, "You've reached the end of this staircase. Two more to go...", tcod.white)
        gui.print(2, 3, "You notice the ceiling has collapsed in some of the corridors following the explosion.", tcod.white)
        gui.print(2, 5, "The quicker you leave, the better.", tcod.white)
        if Key.picked:
            gui.print(2, 9, "You have the key!", tcod.white)
        if Door.visible:
            gui.print(2, 7, "You hear the fire alarm getting louder. This must be the exit.", tcod.white)

    if Level == 0:
        gui.print(2, 1, "Almost there. It's still too high to jump out of the window, though.", tcod.white)
        gui.print(2, 3, "One last push. To safety.", tcod.white)
        if Key.picked:
            gui.print(2, 7, "You have the key!", tcod.white)
        if Door.visible:
            gui.print(2, 5, "You hear the fire alarm getting louder. This must be the exit.", tcod.white)

#...which is then copied to the main display
    gui.blit(root, 0, 105)


#If the player steps on the key, pick it up
def process_pickups():
    if Player.x == Key.x and Player.y == Key.y:
        Key.picked = True


#The rest of the functions are just printing text, so I won't describe them
def startscreen():
    root.print(99, 60, "Press any key to start", tcod.white)
    root.print(56, 62, 'You can press ESC to exit the game during the cutscenes whenever the "Press any key to continue" is present', tcod.white)
    root.print(91, 64, "and at any time outside the cutscenes", tcod.white)
    root.print(97, 123, "Chernobyl: Escape the Fate", tcod.gray)
    root.print(107, 124, "v. 0.1", tcod.gray)
    tcod.console_flush()
    await_cutscene_controls()
    root.clear()
    tcod.console_flush()
    time.sleep(2)


def intro():
    int1 = open("int1.txt")
    Intro1 = int1.read()
    int1.close()
    int2 = open("int2.txt")
    Intro2 = int2.read()
    int2.close()
    int3 = open("int3.txt")
    Intro3 = int3.read()
    int3.close()

    root.print(0, 25, Intro1, tcod.gray)
    tcod.console_flush()
    time.sleep(1)
    root.print(0, 25, Intro1, tcod.white)
    tcod.console_flush()
    time.sleep(1.5)

    root.print(99, 105, "You were one of them.", tcod.white)
    tcod.console_flush()
    time.sleep(2)
    root.print(94, 107, "Just a part of a huge enterprise", tcod.white)
    tcod.console_flush()
    time.sleep(2)
    root.print(94, 109, "that promised to be one of those", tcod.white)
    tcod.console_flush()
    time.sleep(2)
    root.print(94, 111, "pushing the Soviet Union forward.", tcod.white)
    tcod.console_flush()
    time.sleep(2)
    root.print(104, 113, "A tiny part.", tcod.white)
    tcod.console_flush()
    time.sleep(3)
    root.print(97, 120, "Press any key to continue", tcod.white)
    tcod.console_flush()
    await_cutscene_controls()

    root.print(0, 25, Intro1, tcod.gray)
    root.print(99, 105, "You were one of them.", tcod.gray)
    root.print(94, 107, "Just a part of a huge enterprise", tcod.gray)
    root.print(94, 109, "that promised to be one of those", tcod.gray)
    root.print(94, 111, "pushing the Soviet Union forward.", tcod.gray)
    root.print(104, 113, "A tiny part.", tcod.gray)
    root.print(97, 120, "Press any key to continue", tcod.gray)
    tcod.console_flush()
    time.sleep(1)
    root.clear()
    tcod.console_flush()
    time.sleep(1)

    root.print(0, 21, Intro2, tcod.gray)
    tcod.console_flush()
    time.sleep(1)
    root.print(0, 21, Intro2, tcod.white)
    tcod.console_flush()
    time.sleep(1.5)

    root.print(101, 105, "Endless consoles.", tcod.white)
    tcod.console_flush()
    time.sleep(2)
    root.print(100, 107, "Neverending buttons.", tcod.white)
    tcod.console_flush()
    time.sleep(2)
    root.print(97, 109, "One might say it's boring.", tcod.white)
    tcod.console_flush()
    time.sleep(2)
    root.print(93, 111, "But it was an honour to work here.", tcod.silver)
    tcod.console_flush()
    time.sleep(2)
    root.print(85, 113, "It almost looked like fate has brought you here...", tcod.white)
    tcod.console_flush()
    time.sleep(3)
    root.print(97, 120, "Press any key to continue", tcod.white)
    tcod.console_flush()
    await_cutscene_controls()
    root.print(0, 21, Intro2, tcod.gray)
    root.print(101, 105, "Endless consoles.", tcod.gray)
    root.print(100, 107, "Neverending buttons.", tcod.gray)
    root.print(97, 109, "One might say it's boring.", tcod.gray)
    root.print(85, 113, "It almost looked like fate has brought you here...", tcod.gray)
    root.print(97, 120, "Press any key to continue", tcod.gray)
    tcod.console_flush()
    time.sleep(1)
    root.clear()
    tcod.console_flush()
    time.sleep(1)

    root.print(0, 25, Intro3, tcod.gray)
    tcod.console_flush()
    time.sleep(1)
    root.print(0, 25, Intro3, tcod.white)
    tcod.console_flush()
    time.sleep(1.5)

    root.print(106, 109, "Until now.", tcod.white)
    tcod.console_flush()
    time.sleep(3)
    root.print(0, 25, Intro3, tcod.gray)
    root.print(106, 109, "Until now.", tcod.gray)
    tcod.console_flush()
    time.sleep(1)
    root.clear()
    tcod.console_flush()
    time.sleep(1)


def outro():
    out1 = open("out1.txt")
    Outro1 = out1.read()
    out1.close()

    root.clear()
    tcod.console_flush()
    time.sleep(2.5)
    root.print(0, 31, Outro1, tcod.gray)
    tcod.console_flush()
    time.sleep(1)
    root.print(0, 31, Outro1, tcod.white)
    tcod.console_flush()
    time.sleep(1.5)

    root.print(104, 100, "You made it.", tcod.white)
    tcod.console_flush()
    time.sleep(2)
    root.print(91, 102, "You managed to escape the power plant.", tcod.white)
    tcod.console_flush()
    time.sleep(3)
    root.print(0, 31, Outro1, tcod.gray)
    root.print(91, 102, "You managed to escape the power plant.", tcod.gray)
    root.print(104, 100, "You made it.", tcod.gray)
    tcod.console_flush()
    time.sleep(1)
    root.clear()
    tcod.console_flush()
    time.sleep(1)
    root.print(89, 62, "But was it the power plant you've escaped?")
    tcod.console_flush()
    time.sleep(4)
    root.clear()
    tcod.console_flush()
    time.sleep(3)


def credits_titles():
    root.clear()
    root.print(87, 57, "Thanks for playing Chernobyl: Escape the Fate!", tcod.white)
    root.print(72, 59, "If you enjoyed the game (or not D: ), feel free to email me at cr929@aol.com", tcod.white)
    root.print(93, 61, "I'm open for suggestions 24/7/365!", tcod.white)
    root.print(86, 63, "Found a bug not mentioned in the known bugs list?", tcod.white)
    root.print(85, 65, "Report it and I'll do my best to fix it in v. 0.2!", tcod.white)
    root.print(90, 67, "Pressing any key now will exit the game.", tcod.white)
    tcod.console_flush()
    await_ending_controls()


#These are for tcod to initialize the window
WindowWidth = 220
WindowHeight = 125
DungeonWidth = WindowWidth
DungeonHeight = WindowHeight - 21

#root is the main screen, con is for the dungeon map, and gui is, well, for GUI
#The last two are copied to root which then prints itself on the screen using tcod.console_flush()
root = tcod.console_init_root(WindowWidth, WindowHeight, "Chernobyl: Escape the Fate", False, 1, vsync=True)
con = tcod.console.Console(WindowWidth, DungeonHeight + 1)
gui = tcod.console.Console(WindowWidth, 20)

#Level defines what level the player is currently on
Level = 3
startscreen()
intro()

#Once the player finishes the last level, the loop will be broken and the outro will be triggered
while Level != 0:
    Level -= 1
#The map is generated
    generate_terrain()

#This code looks for any floor tile and spawns a player on it with 1% chance
    Player = Entity(1, 1, ord("@"), tcod.white)
    PlayerSpawned = False
    while not PlayerSpawned:
        for CheckerX in range(DungeonWidth):
            for CheckerY in range(DungeonHeight):
                if not dungeon[CheckerX][CheckerY].blocked:
                    if random.SystemRandom().randint(0, 100) == 75:
                        Player = Entity(CheckerX, CheckerY, ord("@"), tcod.white)
                        PlayerSpawned = True

#Same with the key
    Key = Entity(2, 2, ord("*"), tcod.gold, False)
    KeySpawned = False
    while not KeySpawned:
        for CheckerX in range(int(DungeonWidth / random.SystemRandom().randint(2, 5))):
            for CheckerY in range(int(DungeonHeight)):
                if not dungeon[CheckerX][CheckerY].blocked:
                    if random.SystemRandom().randint(0, 100) == 50:
                        Key = Entity(CheckerX, CheckerY, ord("*"), tcod.gold, False)
                        KeySpawned = True

#The door is a bit more complicated. The code checks for any wall with adjacent floor tile and makes it a door with 1% chance
    Door = Entity(3, 3, ord("#"), tcod.gold, False)
    DoorSpawned = False
    while not DoorSpawned:
#You might be asking why do I divide the X coordinate. This is to ensure keys and doors spawn far away from the player
        for CheckerX in range(int(DungeonWidth / random.SystemRandom().randint(2, 5))):
            for CheckerY in range(int(DungeonHeight - 1)):
                if dungeon[CheckerX][CheckerY].blocked and (
                        not dungeon[CheckerX + 1][CheckerY].blocked or not dungeon[CheckerX - 1][
                    CheckerY].blocked or not dungeon[CheckerX][CheckerY + 1].blocked or not dungeon[CheckerX][
                    CheckerY - 1].blocked):
                    if random.SystemRandom().randint(0, 100) == 25:
                        Door = Entity(CheckerX, CheckerY, ord("#"), tcod.gold, False)
                        DoorSpawned = True

#This loop launches every turn
    while True:
#The code processes the FOV to check for nearby items
        process_fov()
#Then picks the key up if we're in the same tile
        process_pickups()
#Prints text
        draw_gui()
#Draws the golden asterisk if we noticed the key but haven't picked it up yet
        if Key.visible and not Key.picked:
            Key.draw()
#Draws the player
        Player.draw()
#Draws the door if we heard the fire alarm
        if Door.visible:
            Door.draw()

#As all of the above was done in con and gui consoles, which cannot be printed on the screen,
#we paste both to root (the gui is pasted in draw_gui())...
        con.blit(root)
#Then print the result on the screen
        tcod.console_flush()
#And remove the key and the player in order for them to be redrawn (since the player can move and the key can be picked up) 
        Player.remove()
        Key.remove()
        await_keyboard_input()

#This piece of code checks if the player is next to a door holding a key
#If so, the code breaks the while True loop, regenerating the level (thus progressing to a new one)
        if Player.x + 1 == Door.x and Player.y == Door.y and Key.picked:
            break
        if Player.x - 1 == Door.x and Player.y == Door.y and Key.picked:
            break
        if Player.x == Door.x and Player.y + 1 == Door.y and Key.picked:
            break
        if Player.x == Door.x and Player.y - 1 == Door.y and Key.picked:
            break

#Once the last level is completed, trigger the outro
outro()
credits_titles()
