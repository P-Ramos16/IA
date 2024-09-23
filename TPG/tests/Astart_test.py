import asyncio
import getpass
import json
import os
import websockets
import random
import heapq

# Next 4 lines are not needed for AI agents, please remove them from your code!
import websockets

import random
from datetime import datetime

#Implementação do algoritmo A*
def astar(start, goal, obstacles):
    open_list = []
    heapq.heappush(open_list, (0, start))
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while open_list:
        _, current = heapq.heappop(open_list)
        if current == goal:
            path = []
            while current:
                path.append(current)
                current = came_from[current]
            return list(reversed(path))

        for next_pos in get_neighbors(current, obstacles):
            new_cost = cost_so_far[current] + 1  #Assuming each move cost is 1
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost + heuristic(goal, next_pos)
                heapq.heappush(open_list, (priority, next_pos))
                came_from[next_pos] = current

    return None

def get_neighbors(pos, obstacles):
    x, y = pos
    neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    return [neighbor for neighbor in neighbors if neighbor not in obstacles]

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

async def agent_loop(server_address="localhost:8000", agent_name="AI Agent"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        while True:
            try:
                state = json.loads(await websocket.recv())
                print(state)

                player_pos = state.get('player_pos')
                enemies = state.get('enemies', [])

                if player_pos is not None and enemies:
                    closest_enemy = min(enemies, key=lambda enemy: abs(enemy['pos'][0] - player_pos[0]) + abs(enemy['pos'][1] - player_pos[1]))
                    enemy_pos = closest_enemy['pos']

                    obstacles = state.get('obstacles', [])  #Assuming you have obstacle positions

                    #Encontrar o caminho usando A*
                    path = astar(player_pos, enemy_pos, obstacles)

                    if path and len(path) > 1:
                        next_pos = path[1]
                        dx = next_pos[0] - player_pos[0]
                        dy = next_pos[1] - player_pos[1]

                        if dx > 0:
                            key = "d"
                        elif dx < 0:
                            key = "a"
                        elif dy > 0:
                            key = "s"
                        else:
                            key = "w"

                        await websocket.send(json.dumps({"cmd": "key", "key": key}))
                    else:
                        await websocket.send(json.dumps({"cmd": "key", "key": " "}))  #Ataque se o inimigo estiver adjacente

                else:
                    key = random.choice(["w", "a", "s", "d", " "])
                    await websocket.send(json.dumps({"cmd": "key", "key": key}))

                await asyncio.sleep(0.1)

            except websockets.exceptions.ConnectionClosedOK:
                return

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
