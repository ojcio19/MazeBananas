import socket
from _thread import *
import _pickle as pickle
import time
from datetime import datetime
import datetime
import random
import math

from maps import maps

Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Set constants
PORT = 5555

BALL_RADIUS = 5  # todo remove
START_RADIUS = 7

ROUND_TIME = 15
BREAK_TIME = 6
TOTAL_TIME = 2 * ROUND_TIME + BREAK_TIME

MASS_LOSS_TIME = 7  # todo remove

WINDOW_WIDTH, WINDOW_HEIGHT = 920, 620
PANEL_WIDTH = 300
WALL_SIZE = 20

HOST_NAME = socket.gethostname()
SERVER_IP = socket.gethostbyname(HOST_NAME)

try:
    Socket.bind((SERVER_IP, PORT))
except socket.error as e:
    print(str(e))
    print("[SERVER] Server could not start")
    quit()

Socket.listen()  # listen for connections

print(f"[SERVER] Server Started with local ip {SERVER_IP}")

# dynamic variables
players = {}
connections = 0
_id = 0
colors = [(0, 255, 0), (0, 255, 128), (255, 0, 0), (255, 128, 0), (255, 255, 0), (128, 255, 0), (0, 255, 255),
          (0, 128, 255), (0, 0, 255), (0, 0, 255), (128, 0, 255), (255, 0, 255), (255, 0, 128), (128, 128, 128)]
start = False
start_time = 0
stage = 0
game_time = "Starting Soon"  # todo remove
nxt = 1


def create_points(points, level, number, value):
    walls = maps[level]
    for i in range(number):
        x = random.randrange(1, 29)
        y = random.randrange(1, 29)
        while (x, y) in walls:
            x = random.randrange(1, 29)
            y = random.randrange(1, 29)

        x = x * WALL_SIZE + 10
        y = y * WALL_SIZE + 10
        print("[POINT] Created point:", (x, y))
        points.append((x, y, colors[value], value))


def get_start_location(players):
    x = 40 + 20 * len(players)
    y = 40
    return (x, y)


'''
def check_wall_collision(players, walls):
    # TODO check collsions with walls
    pass
'''


def check_point_collision(players, points):
    for player in players:
        test = players[player]
        player_x = test["x"]
        player_y = test["y"]
        for point in points:
            point_x = point[0]
            point_y = point[1]
            distance = math.sqrt((player_x - point_x) ** 2 + (player_y - point_y) ** 2)
            if distance <= 27.0:
                test["score"] += point[3]
                points.remove(point)



def addSecs(tm, secs):
    fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    fulldate = fulldate + datetime.timedelta(seconds=secs)
    return fulldate.time()


def process_stage(stage):
    if stage == 2:
        create_points(points, level, number=1, value=1)

    if stage == 3:
        create_points(points, level, number=1, value=1)
        create_points(points, level, number=1, value=2)

    if stage == 4:
        create_points(points, level, number=1, value=1)
        create_points(points, level, number=1, value=2)
        create_points(points, level, number=1, value=3)


def threaded_client(conn, _id):
    global connections, players, points, game_time, nxt, start, game_finished, level, stage

    current_id = _id

    # recieve a name from the client
    data = conn.recv(16)
    name = data.decode("utf-8")
    print("[LOG]", name, "connected to the server.")

    # Setup properties for each new player
    color = colors[current_id]
    x, y = get_start_location(players)
    players[current_id] = {"x": x, "y": y, "color": color, "score": 0, "name": name}  # x, y color, score, name
    points = []
    game_finished = False
    level = 0
    spawning = False

    # pickle data and send initial info to clients
    conn.send(str.encode(str(current_id)))

    # server will recieve basic commands from client
    # it will send back all of the other clients info
    '''
    commands start with:
    move
    get
    id - returns id of client
    '''
    while True:
        # TIME properties
        if start and not game_finished:
            time_now = datetime.datetime.now().time()

            if addSecs(start_time, 5 * ROUND_TIME / 3 + BREAK_TIME) < time_now:
                if len(points) < 3 and spawning:
                    print("changing stage", stage, "to", 4)
                    stage = 4
                    process_stage(stage)
            elif addSecs(start_time, 4 * ROUND_TIME / 3 + BREAK_TIME) < time_now:
                if stage != 3:
                    print("changing stage", stage, "to", 3)
                    stage = 3
                if spawning and len(points) < 2:
                    process_stage(stage)
            elif addSecs(start_time, ROUND_TIME + BREAK_TIME) < time_now:
                if stage != 2:
                    print("changing stage", stage, "to", 2)
                    stage = 2
                if len(points) < 1:
                    process_stage(stage)
                    spawning = True
            elif addSecs(start_time, ROUND_TIME + BREAK_TIME / 2) < time_now:
                if level != 1 and stage != 1:
                    print("changing stage", stage, "to", 1)
                    level = 1
                    stage = 1
            elif addSecs(start_time, ROUND_TIME) < time_now:
                print("changing stage", stage, "to", 6)
                stage = 6
                points = []
                spawning = False
            elif addSecs(start_time, ROUND_TIME * 2 / 3) < time_now:
                if len(points) < 3 and spawning:
                    print("changing stage", stage, "to", 4)
                    stage = 4
                    process_stage(stage)
            elif addSecs(start_time, ROUND_TIME / 3) < time_now:
                print("changing stage", stage, "to", 3)
                stage = 3
                if spawning and len(points) < 2:
                    process_stage(stage)
            elif start_time < time_now:
                print("changing stage", stage, "to", 2)
                stage = 2
                if len(points) < 1:
                    process_stage(stage)
                    spawning = True

            if addSecs(start_time, TOTAL_TIME) < time_now:
                print("changing stage", stage, "to", 5)
                points = []
                game_finished = True
                stage = 5

        try:
            # Recieve data from client
            data = conn.recv(48)

            if not data:
                break

            data = data.decode("utf-8")
            # print("[DATA] Recieved", data, "from client id:", current_id)

            # look for specific commands from recieved data
            if data.split(" ")[0] == "move":
                splited_data = data.split(" ")
                x = int(splited_data[1])
                y = int(splited_data[2])
                players[current_id]["x"] = x
                players[current_id]["y"] = y
                # ..
                check_point_collision(players, points)
                send_data = pickle.dumps((players, points, level, stage))

            elif data.split(" ")[0] == "id":
                print("[LOG] SERVER DATASPLIT ID")
                send_data = str.encode(str(current_id))  # if user requests id then send it

            # elif data.split(" ")[0] == "jump":
            #    send_data = pickle.dumps((balls, players, game_time))
            else:
                # any other command just send back list of players
                print("[LOG] SERVER DATASPLIT ELSE")
                send_data = pickle.dumps(players)  # (walls, players, game_time)

            # send data back to clients
            conn.send(send_data)

        except Exception as e:
            print(e)
            break  # if an exception has been reached disconnect client

        time.sleep(0.001)

    # When user disconnects
    print("[DISCONNECT] Name:", name, ", Client Id:", current_id, "disconnected")

    connections -= 1
    del players[current_id]  # remove client information from players list
    conn.close()  # close connection


print("[GAME] Setting up level")
print("[SERVER] Waiting for connections")

# Keep looping to accept new connections
while True:

    host, addr = Socket.accept()
    print("[CONNECTION] Connected to:", addr)

    # start game when a client on the server computer connects
    if addr[0] == SERVER_IP and not start and connections == 1:  # TODO at least two players
        start = True
        start_time = addSecs(datetime.datetime.now().time(), BREAK_TIME)
        print(datetime.datetime.now().time(), "[STARTING] Game Starting in 10 seconds")
        stage = 1

    # increment connections start new thread then increment ids
    connections += 1
    start_new_thread(threaded_client, (host, _id))
    _id += 1
