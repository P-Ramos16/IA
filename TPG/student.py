"""Student client."""
import asyncio
import json
import os
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
# and the diagonal angle (same as normal 0, 1, 2 and 3 angles but turned 45deg clockwise)
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

#  See if the tiles between us and a given distance with a predifined direction are cleared or not 
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

    #  Check the tiles    
    for tile in range(1, distance + 1):
        xTiles = playerCoords[0] + xDistance * tile
        yTiles = playerCoords[1] + yDistance * tile 
        
        #  Out of game bounds
        if xTiles > mapSize[0]-1 or xTiles < 0:
            continue
        if yTiles > mapSize[1]-1 or yTiles < 0:
            continue
            
        if (gamemap[xTiles][yTiles] == 1):
            return False
        
    return True

#  Return the direction of the enemy if he is in either in the same X or Y from us
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
#  Also predict where the enemies could go and don't go there
def checkIfValidPosition(xPos, yPos, gamestate, mapSize, forAStar=False):
    global step
    position = [xPos, yPos]
    
    #  Out of bounds
    if (xPos < 0 or yPos < 0):
        return False
    if (xPos > mapSize[0] - 1 or yPos > mapSize[1] - 1):
        return False        
    
    #  Avoid rocks and the block below them (edge case)
    for rock in gamestate["rocks"]:
        if rock["pos"] == position:
            return False
        if rock["pos"][0] == position[0] and rock["pos"][1] + 1 == position[1]:
            return False
        
    #  For every enemy
    for enemy in gamestate["enemies"]:
        enemyXPos =enemy["pos"][0]
        enemyYPos = enemy["pos"][1]
        
        #  For A* to reach the target, the enemies actual position must be valid.
        #  For close quarters general moving don't go to the same tile as the enemy.
        if not forAStar:
            if enemy["pos"] == position:
                return False
            
        #  Never walk to 2 steps in front or behind of a Pooka, they can "jump" some times
        if enemy["name"] == "Pooka":
            #  Inside "jump" range
            if enemyYPos == yPos and enemyXPos != xPos and enemy["dir"] % 2 == 1:
                if enemyXPos < xPos and xPos <= enemyXPos + 2:
                    return False
                if enemyXPos - 2 <= xPos and xPos < enemyXPos: 
                    return False
            elif enemyXPos == xPos and enemyYPos != yPos and enemy["dir"] % 2 == 0:
                if enemyYPos < yPos and yPos <= enemyYPos + 2:
                    return False
                if enemyYPos - 2 <= yPos and yPos < enemyYPos: 
                    return False
                
        #  Check if we are going to the next predicted enemu position
        nextEnemyPos = getNextPosByDirection(enemyXPos, enemyYPos, enemy["dir"])
        if nextEnemyPos[0] == xPos and nextEnemyPos[1] == yPos:
            return False
        
        #  Never be 4 steps in front or behind a Fygar ()they can run and shoot)
        #  Also avoid the predicted tile's 4 blocks (ex: they go up and shoot at the same time)
        if enemy["name"] == "Fygar":
            behindEnemyPos = getNextPosByDirection(enemyXPos, enemyYPos, (enemy["dir"] + 2) % 4)
            if behindEnemyPos[0] == xPos and behindEnemyPos[1] == yPos and step < 2000 and not forAStar:
                return False
            
            if enemyYPos == yPos or (nextEnemyPos[1] == yPos and step < 2500):
                #  Inside fire range
                if enemyXPos - 4 <= xPos and xPos < enemyXPos: 
                    return False
                if enemyXPos < xPos and xPos <= enemyXPos + 4: 
                    return False
                
        #  Avoid fire, basically unnecessary here
        if "fire" in enemy:
            if position in enemy["fire"]:
                return False
    
    #  If the checks pass, the block is safe!
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

    #  Loop principal do A*
    while open_list:
        _, current = heapq.heappop(open_list)
        
        #  Caso tenha chegado ao objetivo
        if current == goal:
            path = []
            while current:
                path.append(current)
                current = came_from[current[0], current[1]]
            return list(reversed(path))

        #  Abrir o nó atual
        for next_pos in get_neighbors(current, gamestate, mapSize):
            new_cost = cost_so_far[start[0], start[1]] + blockCost(next_pos[0], next_pos[1], currentMap)
            
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost + heuristic(goal, next_pos)
                heapq.heappush(open_list, (priority, next_pos))
                came_from[next_pos] = current

    return None

#  Get adjacent available (safe) blocks to travel to
def get_neighbors(pos, gamestate, mapSize):
    x, y = pos
    neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    possibleNeighbours = [n for n in neighbors if checkIfValidPosition(n[0], n[1], gamestate, mapSize, forAStar=True)]
    return possibleNeighbours

#  Heuristic for the algorithm
def heuristic(a, b):
    diffX = abs(a[0] - b[0])
    diffY = abs(a[1] - b[1])
    minDif = min(diffX, diffY)
    maxDif = max(diffX, diffY)
    
    #  Prefer straight paths and not wavy or diagonal paths
    if (minDif == 1 and maxDif <= 3):
        return minDif
    else:
        return diffX + diffY + maxDif
    
#  Cost for a move
def blockCost(posX, posY, map):
    #  Prefer empty blocks to avoid building too many paths for enemies to use
    block = map[posX][posY]
    heightCost = 0
    
    #  Prefer lower blocks (more points)
    if posY < 6:
        heightCost = 1
    elif posY < 11:
        heightCost = 0.75
    elif posY < 17:
        heightCost = 0.5
    elif posY <= 24:
        heightCost = 0
    
    return block + heightCost
    
#  Get the next position by direction (adjacent)
def getNextPosByDirection(posX, posY, direction):    
    if direction == 0:
        return [posX, posY-1]
    if direction == 1:
        return [posX+1, posY]
    if direction == 2:
        return [posX, posY+1]
    if direction == 3:
        return [posX-1, posY]

#  Perform a move action to a new block
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
    
    #  Update the new block with 0
    gamemap[ourPosition[0]][ourPosition[1]] = 0
    #  Reset attacking since we moved
    attacking = 0

    return

#  Run from a direction, ex: If the direction is 0 (up), try going down, if impossible try going left or right (if possible)
async def runFromDirection(direction, gamestate):
    global ourPosition
    global mapSize

    if (direction == 0):
        #  Go to right if possible, else go to left, in a last resort, go right
        if (checkIfValidPosition(ourPosition[0], ourPosition[1]+1, gamestate, mapSize)):
            await move(2)
        elif (checkIfValidPosition(ourPosition[0]-1, ourPosition[1], gamestate, mapSize)):
            await move(3)
            return
        elif (checkIfValidPosition(ourPosition[0]+1, ourPosition[1], gamestate, mapSize)):
            await move(1)
            return
        
    elif (direction == 1):
        #  Go left if possible, else go up, in a last resort, go down
        if (checkIfValidPosition(ourPosition[0]-1, ourPosition[1], gamestate, mapSize)):
            await move(3)
            return
        elif (checkIfValidPosition(ourPosition[0], ourPosition[1]-1, gamestate, mapSize)):
            await move(0)
            return
        elif (checkIfValidPosition(ourPosition[0], ourPosition[1]+1, gamestate, mapSize)):
            await move(2)
            return
            
    elif (direction == 2):
        #  Go to up if possible, else go to right, in a last resort, go left
        if (checkIfValidPosition(ourPosition[0], ourPosition[1]-1, gamestate, mapSize)):
            await move(0)
            return
        elif (checkIfValidPosition(ourPosition[0]+1, ourPosition[1], gamestate, mapSize)):
            await move(1)
            return
        elif (checkIfValidPosition(ourPosition[0]-1, ourPosition[1], gamestate, mapSize)):
            await move(3)
            return
        
    else:
        #  Go right if possible, else go down, in a last resort, go up
        if (checkIfValidPosition(ourPosition[0]+1, ourPosition[1], gamestate, mapSize)):
            await move(1)
            return      
        elif (checkIfValidPosition(ourPosition[0], ourPosition[1]+1, gamestate, mapSize)):
            await move(2)
            return     
        elif (checkIfValidPosition(ourPosition[0], ourPosition[1]-1, gamestate, mapSize)):
            await move(0)
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
global step


#  QUEUE PRIORITIES:
#   - 0 (Top): Avoid enemy (run out of the away)
#   - 1: Attack
#   - 2: Leave (less priority run)
#   - 3: Move closer
#   - 4: Change direction to prepare attack
#   - 5 (Bottom): Wait move

#  If no action is performed after iterating all enemy conditions on a frame, go to the closest using A*
#  If an A* path is not available and we are in a safe block, wait a turn
async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Main client loop."""
    global websocket
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        initialInfo = json.loads(await websocket.recv())
        
        """
        {'size': [48, 24], 'map': [[0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], ... ], 
         'fps': 10, 'timeout': 3000, 'lives': 3, 'score': 3300, 'level': 1}
        """
        
        #  Pre-game variables
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
        global level
        level = initialInfo["level"]
        global step
        step = 0
        
        print("---------- ---------- ----------")
        
                #  Loop runs once every frame
        while (True):
            try:
                await playFrame(websocket)
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

            if gameEnded:
                print("GG")
                return


#  Play one game frame
async def playFrame(websocket):
    #  Get data from the server
    gamestate = json.loads(await websocket.recv())
    
    #  Receive game update, this must be called timely or your game will get out of sync with the server
    """
    {'level': 1, 'step': 4, 'timeout': 3000, 'player': 'frostywolf', 'score': 0, 'lives': 3, 'digdug': [1, 2], 
     'enemies': [{'name': 'Fygar', 'id': 'efe136b7-30f2-496a-9b5e-de0482df3aa0', 'pos': [6, 0], 'dir': 1}, 
                 {'name': 'Pooka', 'id': '9fd65914-ecf1-424e-b40c-104f2f7da7e9', 'pos': [18, 6], 'dir': 2}, 
                 {'name': 'Pooka', 'id': '438212f2-9248-41ab-a3ce-0f9b330eb7c6', 'pos': [29, 19], 'dir': 1}], 
     'rocks': [{'id': '473d04b7-57a1-4eb1-93e1-ca97608fe03f', 'pos': [23, 9]}]}
    """
    
    #  Global variables
    global currLives
    global mapSize
    global gamemap
    global actionQueue
    global gameEnded
    global ourDirection
    global ourPosition
    global attacking
    global level
    global step
    
    step += 1
    maniacMode = (step > 2000)
    
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
        
            return
        
    #  New level was generated
    if "map" in gamestate:
        print("New Level!")
        
        step = 0    
        attacking = 0    
        currLives == gamestate["lives"]
        gamemap = gamestate["map"]
        mapSize = gamestate["size"]
        level = gamestate["level"]
                
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
    
    
    #  Sort the list of material (normal) and traverse (ghost) enemies
    traverseEnemies = [enemy for enemy in enemies if "traverse" in enemy]
    if traverseEnemies != []:
        traverseEnemies = sorted(traverseEnemies, key=lambda x: math.sqrt(abs(x['pos'][0] - ourPosition[0])**2 + abs(x['pos'][1] - ourPosition[1])**2))
    materialEnemies = [enemy for enemy in enemies if "traverse" not in enemy]
    if materialEnemies != []:
        materialEnemies = sorted(materialEnemies, key=lambda x: math.sqrt(abs(x['pos'][0] - ourPosition[0])**2 + abs(x['pos'][1] - ourPosition[1])**2))
    
    #  For every ghost enemy
    for enemy in traverseEnemies:
        #  Calculate the distance to it and if he is vertically/horizontally away from us or diagonally
        distanceToEnemy = enemyXYTilesAway(ourPosition, enemy["pos"])
        directionToEnemy = directionTo(ourPosition, enemy)
        
        enemyDirection = enemy["dir"]
        [diagDistance, blockDistance, diagAngle] = distanceDiagonally(ourPosition, enemy["pos"])
        
        #  Ghost enemy close in the X or Y axis, run!
        if (distanceToEnemy and distanceToEnemy <= 2):
            actionQueue.append((0, directionToEnemy))
            continue
        
        #  Ghost enemy diagonally (1 block one direction and 2 in another) close, run!
        if (diagDistance and blockDistance <= 2.4):
            #  Run from the potential angles
            if enemyDirection % 2 == 0:
                actionQueue.append((0, (diagAngle + 1) % 4))
                continue
            if enemyDirection % 2 == 1:
                actionQueue.append((0, diagAngle))
                continue
            
            
    #  For every normal "material" enemy
    for enemy in materialEnemies:
        #  Calculate the distance to it and if he is vertically/horizontally away from us or diagonally
        distanceToEnemy = enemyXYTilesAway(ourPosition, enemy["pos"])
        directionToEnemy = directionTo(ourPosition, enemy)
        
        enemyDirection = enemy["dir"]
        
        #  Remove this block in the map, usefull for some bugs where a non-ghost enemy passes inside an existing block (very rare)
        gamemap[enemy["pos"][0]][enemy["pos"][1]] = 0
        
        #  Diag pos is also [0 - 3] but every number is incremented 45deg (Vertical North = 0 = Diagonal NorthEast)
        [diagDistance, blockDistance, diagAngle] = distanceDiagonally(ourPosition, enemy["pos"])
        
        #  Enemy in a diagonal distance from us
        #  If we are in maniac mode or following a Fygar after level 10, skip and go A* to prevent loops
        if (diagDistance and not maniacMode and not (enemy["name"] == "Fygar" and level >= 10 and step >= 1500)):
            
            #  If the diagonal distance is less than (one block away in both directions)
            if (diagDistance <= 2 and not maniacMode and not (enemy["name"] == "Fygar" and level >= 10 and step >= 1000)):
                
                #  If we are looking at where the enemy will go to    
                if (ourDirection == diagAngle):
                    #  Check if we are looking at where the enemy will come out from
                    posHeAreLookingAt = getNextPosByDirection(ourPosition[0], ourPosition[1], ourDirection)
                    if gamemap[posHeAreLookingAt[0]][posHeAreLookingAt[1]] == 0:
                        #  Wait (camp) for the enemy to move
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
                        #  Wait (camp) for the enemy to move
                        if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                            actionQueue.append((5, "WaitTurn"))
                            continue
                        #  Another enemy is close, forget about this one
                        else:
                            continue
                
                
                #  We are looking at the wrong direction, start preparing the right direction by stepping away
                #  These numbers were pre-calculated by us
                nextAngle = diagAngle
                if (diagAngle % 2 == 0):
                    if enemyDirection == 0: 
                        nextAngle = 1
                    elif enemyDirection == 1: 
                        nextAngle = 0
                    elif enemyDirection == 2:
                        nextAngle = 3
                    else:
                        nextAngle = 2
                        
                if (diagAngle % 2 == 1):
                    if enemyDirection == 0: 
                        nextAngle = 3
                    elif enemyDirection == 1: 
                        nextAngle = 2
                    elif enemyDirection == 2:
                        nextAngle = 1
                    else:
                        nextAngle = 0
                        
                #  Go to the new block if safe
                nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], nextAngle)
                if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                    actionQueue.append((4, nextAngle))
                    continue
                else:
                    #  If not safe, go to another alternative
                    nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (nextAngle + 1) % 4)
                    if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                        actionQueue.append((4, (nextAngle + 1) % 4))
                        continue
                    else:
                        continue
                        
                        
            #  Enemy is an "L" away from us (1 step in a direction and 2 in another) 
            elif (diagDistance <= 2.4 and not maniacMode and not (enemy["name"] == "Fygar" and level >= 10 and step >= 750)):
                #  Try moving to the direction that will make us paralel with the enemy (just two blocks away, verticaly or horizontaly)
                #  Move up or down            
                nextEnemyPos = getNextPosByDirection(enemy["pos"][0], enemy["pos"][1], enemy["dir"])
                distanceToNextEnemyPos = enemyXYTilesAway(ourPosition, nextEnemyPos)
                directionToNextEnemyPos = directionTo(ourPosition, {"pos":nextEnemyPos})
                
                #  Enemy will walk toward one of our horizontal or vertical directions
                if distanceToNextEnemyPos:
                    #  If we are looking at that position and our current block is safe, wait
                    if ourDirection == directionToNextEnemyPos:
                        posHeAreLookingAt = getNextPosByDirection(ourPosition[0], ourPosition[1], ourDirection)
                        if gamemap[posHeAreLookingAt[0]][posHeAreLookingAt[1]] == 0:
                            if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                                actionQueue.append((5, "WaitTurn"))
                                continue
                            #  Another enemy is close, forget about this one
                            else:
                                continue
                            
                    #  If we are looking somewhere else, advance one block to look at where enemy will be next 
                    nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], directionToNextEnemyPos)
                    if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                        actionQueue.append((4, directionToNextEnemyPos))
                        continue
                    
                #  Enemy will walk away from us and we can get on the same X direction
                elif abs(nextEnemyPos[1] - ourPosition[1]) == 1:
                    if diagAngle == 0 or diagAngle == 3:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], 0)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, 0))
                            continue
                    if diagAngle == 1 or diagAngle == 2:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], 2)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, 2))
                            continue
                        
                #  Enemy will walk away from us and we can get on the same Y direction
                elif abs(nextEnemyPos[0] - ourPosition[0]) == 1:
                    if diagAngle == 0 or diagAngle == 1:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], 1)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, 1))
                            continue
                    if diagAngle == 2 or diagAngle == 3:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], 3)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, 3))
                            continue
                
                #  Enemy will move away to either a 3x3 distance from us or to a 1x1 distance from us (next to us diagonally)
                else: 
                    [diagDistance, blockDistance, diagAngle] = distanceDiagonally(ourPosition, nextEnemyPos)
                    #  If he is moving closer, run a bit
                    if diagDistance <= 2:
                        nextPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (diagAngle + 2) % 4)
                        if checkIfValidPosition(nextPos[0], nextPos[1], gamestate, mapSize):
                            actionQueue.append((4, (diagAngle + 2) % 4))
                            continue
                    #  If he is moving away, follow with A*
                    else:
                            continue
                        
                                                
        #  Enemy is not in the same X or Y coordinates or is too far away
        if not distanceToEnemy or distanceToEnemy > 3:
            continue
        
        #  Enemy within 3 horizontal or vertical tiles
        if distanceToEnemy <= 3:
            #  Enemy horizontally or vertically next to us
            if (distanceToEnemy <= 1):
                #  We are not looking at him
                if (ourDirection != directionToEnemy):
                    #  Enemy usually walks in our direction 
                    if ((enemyDirection) % 2 == (directionToEnemy) % 2):
                        #  Run!
                        actionQueue.append((0, directionToEnemy))
                        continue
                    else:
                        newPos = getNextPosByDirection(ourPosition[0], ourPosition[1], (enemyDirection + 2) % 4)
                        #  Move back to prepare for new direction (if safe)
                        if checkIfValidPosition(newPos[0], newPos[1], gamestate, mapSize):
                            actionQueue.append((4, (enemyDirection + 2) % 4))
                            continue
                        else:
                            #  Else, run away for the closes possible block
                            actionQueue.append((0, directionToEnemy))
                            continue
                            
                #  We are next to the enemy and looking at him
                else:
                    #  Enemy usually looks at us
                    if ((enemyDirection) % 2 == (directionToEnemy) % 2):
                        #  Enemy not stunned, Run!
                        if (attacking < 2 and not maniacMode):
                            actionQueue.append((0, directionToEnemy))
                            continue
                        else:
                            #  If we are safe, Attack!
                            if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                                actionQueue.append((1, "Attack"))
                                continue
                            #  Else, another enemy is endangering us, forget about this one
                            else:
                                continue
                            
                    #  Enemy not looking at us
                    else:
                        #  If we are safe, Attack!
                        if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                            actionQueue.append((1, "Attack"))
                            continue
                        #  Else, another enemy is endangering us, forget about this one
                        else:
                            continue
                    
            #  Enemy either 2 or 3 blocks away vertically OR horizontally
            else:
                #  The tiles are cleared between us are cleared
                if (xTilesInDirectionAreCleared(ourPosition, directionToEnemy, gamemap, mapSize, distanceToEnemy)):
                    #  If we are looking at him
                    if (ourDirection == directionToEnemy):
                        #  If we are safe, Attack!
                        if checkIfValidPosition(ourPosition[0], ourPosition[1], gamestate, mapSize):
                            actionQueue.append((1, "Attack"))
                            continue
                        #  Else, another enemy is endangering us, forget about this one
                        else:
                            continue
                    #  Try looking at him
                    else:
                        newPos = getNextPosByDirection(ourPosition[0], ourPosition[1], directionToEnemy)
                        #  If we can get closer
                        if checkIfValidPosition(newPos[0], newPos[1], gamestate, mapSize):
                            actionQueue.append((4, directionToEnemy))
                            continue
                        #  Else, another enemy is endangering us, forget about this one
                        else:
                            continue
                        
                #  We can't shoot but we can get closer to the enemy, try looking at him
                elif distanceToEnemy == 3:
                    newPos = getNextPosByDirection(ourPosition[0], ourPosition[1], directionToEnemy)
                    #  If we can get closer
                    if checkIfValidPosition(newPos[0], newPos[1], gamestate, mapSize):
                        actionQueue.append((4, directionToEnemy))
                        continue
                
                #  One filled tile in between us and the enemy
                elif distanceToEnemy == 2:
                    #  Check if enemy (usually) walks in the same directio we are entering from
                    #  Wait for the enemy to leave so it's safer to break the block between us
                    if (enemyDirection + 2) % 2 == directionToEnemy % 2:
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
                        #  Else, another enemy is endangering us, forget about this one
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
        
    #  If the Queue as any action inside, do the top priority one
    #  QUEUE PRIORITIES:
    #   - 0 (Top): Avoid enemy (run out of the away)
    #   - 1: Attack
    #   - 2: Leave (less priority run)
    #   - 3: Move closer
    #   - 4: Change direction to prepare attack
    #   - 5 (Bottom): Wait move

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
            print("CHANGE DIRECTION!")
            await move(actionParam)  
            return

        #  Wait
        elif nextAction == 5:
            print("WAIT!")
            attacking = 0
            return
    
    
    #  Prioritize the closes material enemies sorted by distance and then the ghost enemies sorted by distance
    closest_enemies = materialEnemies + traverseEnemies
        
    for i in range(0, len(closest_enemies)):
        closest_enemy = closest_enemies[i]
            
        #  Move to the enemy using the A* algorithm
        path = astar(ourPosition, closest_enemy['pos'], gamestate, mapSize, gamemap)
        
        if path:
            #  Get the first action of the path
            next_pos = path[1]
            
            #  If we cant move there, run from the direction
            if not checkIfValidPosition(next_pos[0], next_pos[1], gamestate, mapSize):
                directionToEnemy = directionTo(ourPosition, enemy)
                await runFromDirection(directionToEnemy, gamestate)
                return
            
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

    print("No good path found, waiting")

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", "PRamos")
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
