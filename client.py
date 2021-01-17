import contextlib

with contextlib.redirect_stdout(None):
    import pygame
from network import Network
import os

from maps import maps

pygame.font.init()

# Constants
PLAYER_RADIUS = 10
START_VEL = 9
POINT_SIZE = 10

PANEL_WIDTH = 300
WINDOW_WIDTH, WINDOW_HEIGHT = 620 + 300, 620

WALL_SIZE = 20

NAME_FONT = pygame.font.SysFont("consolas", 12)
TIME_FONT = pygame.font.SysFont("consolas", 30)
SCORE_FONT = pygame.font.SysFont("consolas", 26)
STATUS_FONT = pygame.font.SysFont("consolas", 22)

COLORS = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (128, 255, 0), (0, 255, 0), (0, 255, 128), (0, 255, 255),
          (0, 128, 255), (255, 128, 0), (0, 0, 255), (128, 0, 255), (255, 0, 255), (255, 0, 128), (128, 128, 128)]

# Dynamic Variables
players = {}


# FUNCTIONS
def convert_time(t):
    """
    converts a time given in seconds to a time in
    minutes

    :param t: int
    :return: string
    """
    if type(t) == str:
        return t

    if int(t) < 60:
        return str(t) + "s"
    else:
        minutes = str(t // 60)
        seconds = str(t % 60)

        if int(seconds) < 10:
            seconds = "0" + seconds

        return minutes + ":" + seconds


def draw_points(points):
    for point in points:
        if point[3] == 1:
            window.blit(IMG_ORANGE, (point[0] - 10, point[1] - 10))
        elif point[3] == 2:
            window.blit(IMG_CHERRY, (point[0] - 10, point[1] - 10))
        elif point[3] == 3:
            window.blit(IMG_BANAN_YELLOW, (point[0] - 10, point[1] - 10))


def draw_walls(walls, level):
    for wall in walls:
        # pygame.draw.rect(window, COLORS[0], (wall[0] * WALL_SIZE, wall[1] * WALL_SIZE, WALL_SIZE, WALL_SIZE))
        if level == 0:
            window.blit(IMG_WALL_ZERO, (wall[0] * WALL_SIZE, wall[1] * WALL_SIZE))
        if level == 1:
            window.blit(IMG_WALL_ONE, (wall[0] * WALL_SIZE, wall[1] * WALL_SIZE))


def draw_players(players):
    for player in sorted(players, key=lambda x: players[x]["score"]):
        p = players[player]
        pygame.draw.circle(window, p["color"], (p["x"], p["y"]), PLAYER_RADIUS)
        # render and draw name for each player
        if p["name"] == name:
            text = NAME_FONT.render(p["name"], True, (0, 255, 0))
        else:
            text = NAME_FONT.render(p["name"], True, (255, 0, 0))
        window.blit(text, (p["x"] - text.get_width() / 2, p["y"] - text.get_height() / 2 + 15))


def draw_scoreboard():
    sort_players = list(reversed(sorted(players, key=lambda x: players[x]["score"])))
    title = TIME_FONT.render("Results", True, (255, 255, 255))
    start_y = 25
    x = WINDOW_WIDTH - title.get_width() - 10 - PANEL_WIDTH / 3
    window.blit(title, (x, 5))

    ran = min(len(players), 3)

    for count, i in enumerate(sort_players[:ran]):
        if players[i]["name"] == name:
            text = SCORE_FONT.render(str(players[i]["score"]) + " " + str(players[i]["name"]), 1, (0, 255, 0))
        else:
            text = SCORE_FONT.render(str(players[i]["score"]) + " " + str(players[i]["name"]), 1, (0, 0, 255))
        window.blit(text, (x - PANEL_WIDTH / 6, start_y + count * 20 + 10))


def draw_stage(stage):
    text = ""
    if stage == 0:
        text = STATUS_FONT.render(str("Waiting for players!"), 1, (255, 255, 255))
    if stage == 1:
        text = STATUS_FONT.render(str("Round starting soon!"), 1, (255, 255, 255))
    if stage in [2, 3, 4]:
        text = STATUS_FONT.render(str("stage:" + str(stage-1)), 1, (255, 255, 255))
    if stage == 5:
        text = STATUS_FONT.render(str("Game finished!"), 1, (255, 255, 255))
    if stage == 6:
        text = STATUS_FONT.render(str("Round finished"), 1, (255, 255, 255))

    window.blit(text, (WINDOW_WIDTH - PANEL_WIDTH + 20, WINDOW_HEIGHT - 200))


def redraw_window(players, points, walls, level, stage):
    window.fill((0, 0, 0))  # fill screen white, to clear old frames
    draw_points(points)
    draw_walls(walls, level)
    draw_players(players)
    draw_scoreboard()
    draw_stage(stage)


def get_walls_by_level(level):
    return maps[level]


def check_wall_collision(player_x, player_y, walls):
    for wall in walls:
        rect = pygame.Rect(wall[0] * WALL_SIZE, wall[1] * WALL_SIZE, WALL_SIZE, WALL_SIZE)
        player_rect = pygame.Rect(player_x - 10, player_y - 10, 20, 20)
        if player_rect.colliderect(rect):
            return True
    return False


def main(name):
    """
    function for running the game,
    includes the main loop of the game

    :param players: a list of dicts represting a player
    :return: None
    """
    global players

    # start by connecting to the network
    server = Network()
    current_id = server.connect(name)
    players = server.send("get")
    level = 0
    walls = get_walls_by_level(level)
    print("GET server response:", players)
    # setup the clock, limit to 30fps
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(30)  # 30 fps max
        player = players[current_id]
        velocity = START_VEL - round(player["score"] / 7)
        if velocity <= 1:
            velocity = 1

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if (player["x"] - velocity - PLAYER_RADIUS >= 0) and \
                    not check_wall_collision(player["x"] - velocity, player["y"], walls):
                player["x"] = player["x"] - velocity

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if (player["x"] + velocity + PLAYER_RADIUS <= WINDOW_WIDTH - 300) and \
                    not check_wall_collision(player["x"] + velocity, player["y"], walls):
                player["x"] = player["x"] + velocity

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if (player["y"] - velocity - PLAYER_RADIUS >= 0) and \
                    not check_wall_collision(player["x"], player["y"] - velocity, walls):
                player["y"] = player["y"] - velocity

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if (player["y"] + velocity + PLAYER_RADIUS <= WINDOW_HEIGHT) and \
                    not check_wall_collision(player["x"], player["y"] + velocity, walls):
                player["y"] = player["y"] + velocity

        data = "move " + str(player["x"]) + " " + str(player["y"])

        players, points, current_level, stage = server.send(data)
        if level != current_level:
            # reloading walls
            print("Reloading level from", level, "to", current_level)
            walls = get_walls_by_level(current_level)
            level = current_level
            for i in range(0, len(players)):
                players[i]["x"] = 40 + 20 * i
                players[i]["y"] = 40

        for event in pygame.event.get():
            # if user hits red x button close window
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                # if user hits a escape key close program
                if event.key == pygame.K_ESCAPE:
                    run = False

        # redraw window then update the frame
        redraw_window(players, points, walls, level, stage)
        pygame.display.update()

    server.disconnect()
    pygame.quit()
    quit()


# get users name
while True:
    name = input("Please enter your name: ")
    if 0 < len(name) < 20:
        break
    else:
        print("Error, this name is not allowed (must be between 1 and 19 characters [inclusive])")

# make window start in top left hand corner
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (30, 30)

# setup pygame window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("MazeBananas")

IMG_WALL_ONE = pygame.image.load("wall_one.png").convert_alpha()
IMG_WALL_ZERO = pygame.image.load("wall.png").convert_alpha()
IMG_ORANGE = pygame.image.load("orange.png").convert_alpha()
IMG_BANAN_YELLOW = pygame.image.load("banan_yellow.png").convert_alpha()
IMG_CHERRY = pygame.image.load("cherry.png").convert_alpha()
# start game
main(name)
