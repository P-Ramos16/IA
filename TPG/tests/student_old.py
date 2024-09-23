"""Student client."""
import asyncio
import getpass
import json
import os
import time
import heapq
import math

# Next 4 lines are not needed for AI agents, please remove them from your code!
import websockets

#  Calculate the distance to the given coords in X or Y orientation (vertically or horizontally, never diagonally)
def enemyXYTilesAway(playerCoords, newCoords):
    if (playerCoords[1] == newCoords[1]):
        return abs(playerCoords[0] - newCoords[0]) 
    
    if (playerCoords[0] == newCoords[0]):
        return abs(playerCoords[1] - newCoords[1]) 
    
    return None

#  Calculate the distance to the given coords in X or Y orientation (vertically or horizontally, never diagonally)
#  a is us, b is enemy
def distanceDiagonally(a, b):
    if (a[0] == b[0] or a[1] == b[1]):
        return [None, None, None]
    
    angle = 0
    if a[0] < b[0]:
        if a[1] > b[1]:
            angle = 0
        else:
            angle = 1
    else:
        if a[1] > b[1]:
            angle = 3
        else:
            angle = 2
        
    
    return [math.sqrt(abs(a[0] - b[0])**2 + abs(a[1] - b[1])**2), abs(a[0] - b[0]) + abs(a[1] - b[1]), angle]

def xTilesInDirectionAreCleared(playerCoords, directionToEnemy, gamemap, mapSize, distance):
    if directionToEnemy == 0:
        xDistance = 0
        yDistance = -1
    elif directionToEnemy == 1:
        xDistance = 1
        yDistance = 0
    elif directionToEnemy == 2:
        xDistance = 0
        yDistance = 1
    elif directionToEnemy == 3:
        xDistance = -1
        yDistance = 0
    
    
    for tile in range(1, distance + 1):
        xTiles = playerCoords[0] + xDistance * tile
        yTiles = playerCoords[1] + yDistance * tile 
        
        if xTiles > mapSize[0]-1 or xTiles < 0:
            continue
        if yTiles > mapSize[1]-1 or yTiles < 0:
            continue
            
        if (gamemap[xTiles][yTiles] == 1):
            return False
        
    return True

#  Return the direction of the enemy and he is in either the same X or Y from us
def directionTo(playerCoords, enemy):
    #  Both in the same X
    if playerCoords[0] == enemy["pos"][0]:
        #  Enemy on the up
        if playerCoords[1] < enemy["pos"][1]:
            return 2
        #  Enemy on the down
        if playerCoords[1] > enemy["pos"][1]:
            return 0
            
    #  Both in the same Y
    if playerCoords[1] == enemy["pos"][1]:
        #  Enemy on the right
        if playerCoords[0] < enemy["pos"][0]:
            return 1
            
        #  Enemy on the left
        if playerCoords[0] > enemy["pos"][0]:
            return 3
            
    #  Enemy is diagonally from us
    return False

#  Check if the given position is ocupied with an enemy, a rock or a piece of fire  
def checkIfValidPosition(xPos, yPos, gamestate, mapSize, forAStar=False):
    position = [xPos, yPos]
    
    if (xPos < 0 or yPos < 0):
        return False
        
    if (xPos > mapSize[0] - 1 or yPos > mapSize[1] - 1):
        return False        
    
        
    for rock in gamestate["rocks"]:
        if rock["pos"] == position:
            return False
        
    for enemy in gamestate["enemies"]:
        if not forAStar:
            if enemy["pos"] == position:
                return False
        # WORK HERE AGAINST FIRE
        #  Never walk to 2 steps in front of a Pooka, they can "jump" some times
        if enemy["name"] == "Pooka":
            #  Inside "jump" range
            if enemy["pos"][1] == yPos and enemy["pos"][0] != xPos:
                if enemy["dir"] == 1 and enemy["pos"][0] < xPos and xPos <= enemy["pos"][0] + 2: 
                    return False
                if enemy["dir"] == 3 and enemy["pos"][0] - 2 <= xPos and xPos < enemy["pos"][0]: 
                    return False
            elif enemy["pos"][0] == xPos and enemy["pos"][1] != yPos:
                if enemy["dir"] == 2 and enemy["pos"][1] < yPos and yPos <= enemy["pos"][1] + 2: 
                    return False
                if enemy["dir"] == 0 and enemy["pos"][1] - 2 <= yPos and yPos < enemy["pos"][1]: 
                    return False
                
        if enemy["name"] == "Fygar" and enemy["pos"][1] == yPos:
            #  Inside fire range
            if enemy["dir"] == 3 and enemy["pos"][0] - 3 <= xPos and xPos < enemy["pos"][0]: 
                return False
            if enemy["dir"] == 1 and enemy["pos"][0] < xPos and xPos <= enemy["pos"][0] + 3: 
                return False

        if "fire" in enemy:
            if position in enemy["fire"]:
                return False
    
    return True


#Implementação do algoritmo A*
def astar(start, goal, gamestate, mapSize, currentMap):
    open_list = []
    heapq.heappush(open_list, (0, start))
    came_from = {}
    cost_so_far = {}
    came_from[start[0], start[1]] = None
    cost_so_far[start[0], start[1]] = 0
    goal = (goal[0], goal[1])

    while open_list:
        _, current = heapq.heappop(open_list)
        
        if current == goal:
            path = []
            while current:
                path.append(current)
                current = came_from[current[0], current[1]]
            return list(reversed(path))

        for next_pos in get_neighbors(current, gamestate, mapSize):
            new_cost = cost_so_far[start[0], start[1]] + blockCost(next_pos[0], next_pos[1], currentMap)
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost + heuristic(goal, next_pos)
                heapq.heappush(open_list, (priority, next_pos))
                came_from[next_pos] = current

    return None

def get_neighbors(pos, gamestate, mapSize):
    x, y = pos
    neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    possibleNeighbours = [n for n in neighbors if checkIfValidPosition(n[0], n[1], gamestate, mapSize, forAStar=True)]
    return possibleNeighbours

def heuristic(a, b):
    diffX = abs(a[0] - b[0])
    diffY = abs(a[1] - b[1])
    return diffX + diffY + max(diffX, diffY)
    #return math.sqrt(abs(a[0] - b[0])**2 + abs(a[1] - b[1])**2)
    

def blockCost(posX, posY, map):
    block = map[posX][posY]
    heightCost = 0
    
    if posY < 6:
        heightCost = 1
    elif posY < 11:
        heightCost = 0.75
    elif posY < 17:
        heightCost = 0.5
    elif posY <= 24:
        heightCost = 0
    
    return block + heightCost
    

def getNextPosByDirection(posX, posY, direction):    
    if direction == 0:
        return [posX, posY-1]
    if direction == 1:
        return [posX+1, posY]
    if direction == 2:
        return [posX, posY+1]
    if direction == 3:
        return [posX-1, posY]


async def move(direction):
    global websocket
    global ourPosition
    global ourDirection
    global gamemap
    global attacking
    
    ourDirection = direction
    if (direction == 0):
        await websocket.send(json.dumps({"cmd": "key", "key": "w"}))
        ourPosition[1] -= 1
        print("GO UP\n") 

    elif (direction == 1):
        await websocket.send(json.dumps({"cmd": "key", "key": "d"}))
        ourPosition[0] += 1
        print("GO RIGHT\n") 

    elif (direction == 2):
        await websocket.send(json.dumps({"cmd": "key", "key": "s"}))
        ourPosition[1] += 1
        print("GO DOWN\n") 

    elif (direction == 3):
        await websocket.send(json.dumps({"cmd": "key", "key": "a"}))
        ourPosition[0] -= 1
        print("GO LEFT\n") 
    else:
        print("???????????? > ", direction)
    
    gamemap[ourPosition[0]][ourPosition[1]] = 0
    attacking = 0

    return

#  Run from a direction, ex: If the direction is 0 (up), try going down, if impossible try going left or right (if possible)
async def runFromDirection(direction, gamestate):
    global ourPosition
    global mapSize

    if (direction == 0):
        #  Go to left if possible, else go to right, in a last resort, go down
        if (checkIfValidPosition(ourPosition[0]-1, ourPosition[1], gamestate, mapSize)):
            await move(3)
            return
        elif (checkIfValidPosition(ourPosition[0]+1, ourPosition[1], gamestate, mapSize)):
            await move(1)
            return
        elif (checkIfValidPosition(ourPosition[0], ourPosition[1]+1, gamestate, mapSize)):
            await move(2)
            return
    elif (direction == 1):
        #  Go down if possible, else up down, in a last resort, go left
        if (checkIfValidPosition(ourPosition[0], ourPosition[1]+1, gamestate, mapSize)):
            await move(2)
            return
        elif (checkIfValidPosition(ourPosition[0], ourPosition[1]-1, gamestate, mapSize)):
            await move(0)
            return
        elif (checkIfValidPosition(ourPosition[0]-1, ourPosition[1], gamestate, mapSize)):
            await move(3)
            return
            
    elif (direction == 2):
        #  Go to right if possible, else go to left, in a last resort, go up
        if (checkIfValidPosition(ourPosition[0]+1, ourPosition[1], gamestate, mapSize)):
            await move(1)
            return
        elif (checkIfValidPosition(ourPosition[0]-1, ourPosition[1], gamestate, mapSize)):
            await move(3)
            return
        elif (checkIfValidPosition(ourPosition[0], ourPosition[1]-1, gamestate, mapSize)):
            await move(0)
            return
        
    else:
        #  Go up if possible, else go down, in a last resort, go right
        if (checkIfValidPosition(ourPosition[0], ourPosition[1]-1, gamestate, mapSize)):
            await move(0)
            return
        elif (checkIfValidPosition(ourPosition[0], ourPosition[1]+1, gamestate, mapSize)):
            await move(2)
            return     
        elif (checkIfValidPosition(ourPosition[0]+1, ourPosition[1], gamestate, mapSize)):
            await move(1)
            return      

    return

global gamemap
global mapSize
global currLives
global actionQueue
global ourDirection
global ourPosition
global gameEnded
global passedLevel
global websocket
global attacking


#  QUEUE PRIORITIES:
#   - 0 (Top): Avoid enemy (run out of the away)
#   - 1: Attack
#   - 2: Leave (less priority run)
#   - 3: Move closer
#   - 4: Change direction to prepare attack
#   - 5 (Bottom): Wait move

#  If no action is performed after iterating all enemy conditions on a frame, go to the closest using A*

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Main client loop."""
    global websocket
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        initialInfo = json.loads(await websocket.recv())
        
        """{'size': [48, 24], 'map': [[0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], ... ], 
            'fps': 10, 'timeout': 3000, 'lives': 3, 'score': 3300, 'level': 1}
        """
        
        websocket = websocket
        global gamemap
        gamemap = initialInfo["map"]
        global mapSize
        mapSize = initialInfo["size"]
        global currLives
        currLives = initialInfo["lives"]
        global actionQueue
        actionQueue = []
        global gameEnded
        gameEnded = False
        global ourPosition
        ourPosition = [1, 1]
        global attacking
        attacking = 0
        global ourDirection
        ourDirection = 3
        print("---------- ---------- ----------")
        
        
        #  Loop runs once every 100ms (10fps)
        while (True):
            
            try:
                await playFrame(websocket)
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

            if gameEnded:
                print("GG")

async def playFrame(websocket):
    gamestate = json.loads(await websocket.recv())  
    
    # receive game update, this must be called timely or your game will get out of sync with the server
    """{'level': 1, 'step': 4, 'timeout': 3000, 'player': 'frostywolf', 'score': 0, 'lives': 3, 'digdug': [1, 2], 
        'enemies': [{'name': 'Fygar', 'id': 'efe136b7-30f2-496a-9b5e-de0482df3aa0', 'pos': [6, 0], 'dir': 1}, 
                    {'name': 'Pooka', 'id': '9fd65914-ecf1-424e-b40c-104f2f7da7e9', 'pos': [18, 6], 'dir': 2}, 
                    {'name': 'Pooka', 'id': '438212f2-9248-41ab-a3ce-0f9b330eb7c6', 'pos': [29, 19], 'dir': 1}], 
        'rocks': [{'id': '473d04b7-57a1-4eb1-93e1-ca97608fe03f', 'pos': [23, 9]}]}
    """
    
    global currLives
    global mapSize
    global gamemap
    global actionQueue
    global gameEnded
    global ourDirection
    global ourPosition
    global attacking
    
    #  Clear the action queue
    actionQueue = []
        
    #  We lost a life
    if (gamestate["lives"] < currLives):
        currLives = gamestate["lives"]
        ourPosition = gamestate["digdug"]
        print("Lost a life!")
        
        #  We lost all lives
        if (gamestate["lives"] < 1):
            print("We lost the game :(")
            gameEnded = True
        
    #  New level was generated
    if "map" in gamestate:
        print("New Level!")
        currLives == gamestate["lives"]
        gamemap = gamestate["map"]
        mapSize = gamestate["size"]
        #  Wait one frame
        return
    
    #  Enemies were not generated yet
    if "enemies" not in gamestate or gamestate["enemies"] == []:
        print("Wait for enemy generation")
        ourPosition = gamestate["digdug"]
        ourDirection = 3
        #  Wait one frame
        return
    
    enemies = gamestate["enemies"]
    ourPosition = gamestate["digdug"]
    
    traverseEnemies = [enemy for enemy in enemies if "traverse" in enemy]
    materialEnemies = [enemy for enemy in enemies if "traverse" not in enemy]
    
    for enemy in traverseEnemies:
        distanceToEnemy = enemyXYTilesAway(ourPosition, enemy["pos"])
        directionToEnemy = directionTo(ourPosition, enemy)
        [diagDistance, blockDistance, diagAngle] = distanceDiagonally(ourPosition, enemy["pos"])
        
        #  Ghost enemy close, run!
        if (distanceToEnemy and distanceToEnemy <= 2):
            if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                actionQueue.append((0, directionToEnemy))
                continue
            else:
                continue
        if (diagDistance and blockDistance <= 2.3):
            if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                actionQueue.append((0, diagAngle))
                continue
            else:
                continue
        

    #  Check if an enemy is close in the X or Y axis
    for enemy in materialEnemies:
        distanceToEnemy = enemyXYTilesAway(ourPosition, enemy["pos"])
        directionToEnemy = directionTo(ourPosition, enemy)
        enemyDirection = enemy["dir"]
        gamemap[enemy["pos"][0]][enemy["pos"][1]] = 0
        
        #Diag pos is also [0 - 3] but every number is incremented 45deg (Vertical North = 0 = Diagonal NorthEast)
        [diagDistance, blockDistance, diagAngle] = distanceDiagonally(ourPosition, enemy["pos"])
        
        #  Enemy in a diagonal 1 block distance from us
        if (diagDistance):
            if (diagDistance <= 2):
                if (ourDirection == diagAngle):
                    #  Check if we are looking at where the enemy will come out fr
                    posHeAreLookingAt = getNextPosByDirection(ourPosition[0], ourPosition[1], ourDirection)
                    if gamemap[posHeAreLookingAt[0]][posHeAreLookingAt[1]] == 0:
                        if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                            actionQueue.append((5, "WaitTurn"))
                            continue
                        #  Another enemy is close, forget about this one
                        else:
                            continue
                        
                if (ourDirection == (diagAngle + 1) % 4):
                    #  Check if we are looking at where the enemy will come out from
                    posHeAreLookingAt = getNextPosByDirection(ourPosition[0], ourPosition[1], ourDirection)
                    if gamemap[posHeAreLookingAt[0]][posHeAreLookingAt[1]] == 0:
                        if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                            actionQueue.append((5, "WaitTurn"))
                            continue
                        #  Another enemy is close, forget about this one
                        else:
                            continue
                
                #  MAIN FOCUS
                #  We are looking at the wrong direction, start preparing the right direction by stepping away
                if (enemyDirection % 2 == 0):
                    nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (diagAngle + 2) % 4)
                    if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                        actionQueue.append((4, (diagAngle + 2) % 4))
                        print("CHANGEDIR > -2")
                        continue
                    else:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (diagAngle + 3) % 4)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, (diagAngle + 3) % 4))
                            print("CHANGEDIR > -1")
                            continue
                        else:
                            continue
                if (enemyDirection % 2 == 1):
                    nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (diagAngle) % 4)
                    if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                        actionQueue.append((4, (diagAngle) % 4))
                        print("CHANGEDIR > 0")
                        continue
                    else:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (diagAngle + 3) % 4)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, (diagAngle + 3) % 4))
                            print("CHANGEDIR > 1")
                            continue
                        else:
                            continue
                        
            #  Enemy is an "L" away from us (1 step in a direction and two in another) 
            elif (diagDistance <= 2.4):
                #  Try moving to the direction that will make us paralel with the enemy (just two blocks away, verticaly or horizontaly)
                #  Move up or down
                if abs(ourPosition[0] - enemy["pos"][0]) <= 1:
                    nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], diagAngle)
                    if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                        actionQueue.append((4, diagAngle))
                        print("CHANGEDIR > 2")
                        continue
                    else:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (diagAngle + 1) % 4)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, (diagAngle + 1) % 4))
                            print("CHANGEDIR > 3")
                            continue
                        else:
                            continue
                        
                else:
                    nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (diagAngle + 1) % 4)
                    if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                        actionQueue.append((4, (diagAngle + 1) % 4))
                        print("CHANGEDIR > 4")
                        continue
                    else:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], diagAngle)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, diagAngle))
                            print("CHANGEDIR > 5")
                            continue
                        else:
                            continue
                        
        #  Enemy is not in the same X or Y coordinates or is too far away
        if not distanceToEnemy or distanceToEnemy > 3:
            continue
        
        #  Enemy within 3 horizontal or vertical tiles
        if distanceToEnemy <= 3:
            #if enemy["name"] == "Pooka":            
            #  Enemy horizontally or vertically next to us
            if (distanceToEnemy <= 1):
                #  We are not looking at him
                if (ourDirection != directionToEnemy):
                    #  Enemy usually walks in our direction 
                    #  Run!
                    actionQueue.append((0, directionToEnemy))
                    continue
                            
                #  We are next to the enemy and looking at him
                else:
                    #  Enemy usually looks at us
                    if ((enemyDirection) % 2 == (directionToEnemy) % 2):
                        #  Enemy not stunned, Run!
                        if (attacking < 1):
                            actionQueue.append((0, directionToEnemy))
                            continue
                        else:
                            #  If we are safe, Attack!
                            if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                                actionQueue.append((1, "Attack"))
                                continue
                            else:
                                continue
                    #  Enemy not looking at us
                    else:
                        #  If we are safe, Attack!
                        if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                            actionQueue.append((1, "Attack"))
                            continue
                        #  Run away!
                        else:
                            continue
                    
            #  Enemy either 2 or 3 blocks away vertically OR horizontally
            else:
                #  The tiles are cleared between us are cleared
                if (xTilesInDirectionAreCleared(ourPosition, ourDirection, gamemap, mapSize, distanceToEnemy)):
                    #  If we are looking at him
                    if (ourDirection == directionToEnemy):
                        #  If we are safe, Attack!
                        if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                            actionQueue.append((1, "Attack"))
                            continue
                        #  Run away!
                        else:
                            continue
                    #  We can't shoot but we can get closer to the enemy, try looking at him
                    elif distanceToEnemy == 3:
                        newPos = getNextPosByDirection(ourPosition[0], ourPosition[1], directionToEnemy)
                        #  If we can get closer
                        if checkIfValidPosition(newPos[0], newPos[1], gamestate, mapSize):
                            actionQueue.append((4, directionToEnemy))
                            print("CHANGEDIR > 6")
                            continue
                        else:
                            continue
                    #  Else, go in the oposite direction if possible and give more space to work with
                    else:
                        newPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (directionToEnemy + 2) % 4)
                        #  If we can get closer
                        if checkIfValidPosition(newPos[0], newPos[1], gamestate, mapSize):
                            actionQueue.append((3, (directionToEnemy + 2) % 4))
                            continue
                        else:
                            continue
                
                #  One filled tile in between us and the enemy
                elif distanceToEnemy == 2:
                    #  Check if enemy (usually) walks in the same directio we are entering from
                    #  Wait for the enemy to leave so it's safer to break the block between us
                    if (enemyDirection + 2) % 4 == directionToEnemy:
                        #  Wait one turn
                        if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                            actionQueue.append((5, "WaitTurn"))
                            continue
                        #  Another enemy is close, forget about this one
                        else:
                            continue
                    else:
                        newPos = getNextPosByDirection(ourPosition[0], ourPosition[1], directionToEnemy)
                        #  If we can get closer
                        if checkIfValidPosition(newPos[0], newPos[1], gamestate, mapSize):
                            actionQueue.append((3, directionToEnemy))
                            continue
                        else:
                            continue
                        
                    
                #  Move closer to the enemy (blocks between us filled and distance of 3)
                else:
                    newPos = getNextPosByDirection(ourPosition[0], ourPosition[1], directionToEnemy)
                    #  If we can get closer
                    if checkIfValidPosition(newPos[0], newPos[1], gamestate, mapSize):
                        actionQueue.append((3, directionToEnemy))
                        continue
                    #  If not, cancel the attack preparations
                    else:
                        continue
        
    if len(actionQueue) > 0:
        #  Get the action with the lowest priority
        action = actionQueue[min(range(len(actionQueue)), key=lambda i: actionQueue[i][0])]

        nextAction = action[0]
        actionParam = action[1]
        
        #  Avoid enemy
        if nextAction == 0:
            print("RUN!")
            await runFromDirection(actionParam, gamestate)
            return
        
        #  Attack
        elif nextAction == 1:
            print("ATTACK!")
            attacking += 1
            await websocket.send(json.dumps({"cmd": "key", "key": "A"}))
            return
            
        #  Leave
        elif nextAction == 2:
            attacking += 1
            print("LEAVE!")
            await move(actionParam)
            return
            
        #  Move Closer
        elif nextAction == 3:
            print("GET CLOSER!")
            await move(actionParam) 
            return 

        #  Change Direction
        elif nextAction == 4:
            print("CHANGE DIRECTIO!")
            await move(actionParam)  
            return

        #  Wait
        elif nextAction == 5:
            print("WAIT!")
            return
    

    
    lastTriedEnemy = None
    
    while True:
        if materialEnemies == []:
            traverseEnemies = [enemy for enemy in traverseEnemies if enemy != lastTriedEnemy]
            closest_enemy = min(traverseEnemies, key=lambda enemy: math.sqrt(abs(enemy['pos'][0] - ourPosition[0])**2 + abs(enemy['pos'][1] - ourPosition[1])**2))
        else:
            traverseEnemies = [enemy for enemy in traverseEnemies if enemy != lastTriedEnemy]
            closest_enemy = min(materialEnemies, key=lambda enemy: math.sqrt(abs(enemy['pos'][0] - ourPosition[0])**2 + abs(enemy['pos'][1] - ourPosition[1])**2))

            
        #  No Enemies close, move to them using the A* algorithm
        # random rn
        path = astar(ourPosition, closest_enemy['pos'], gamestate, mapSize, gamemap)
        
        if path:
            next_pos = path[1]
            
            dx = next_pos[0] - ourPosition[0]
            dy = next_pos[1] - ourPosition[1]

            if dx > 0:
                await move(1)
            elif dx < 0:
                await move(3)
            elif dy > 0:
                await move(2)
            else:
                await move(0)
                
            return
        else:
            lastTriedEnemy = closest_enemy
            return

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", "PRamos")
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
