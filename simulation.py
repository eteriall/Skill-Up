import heapq
import itertools
import json
import random

import sys

from xml.dom import minidom

import pygame.gfxdraw

import numpy as np
import pygame

from os_activities import save_points, create_new_project
from utilities import cv_col, get_rects, rect_collision, generate_tile_map


def intersects(point, colliders, collider_size=10):
    x, y = point
    x, y = x - collider_size // 2, y - collider_size // 2
    w, h = collider_size, collider_size
    s = any(map(lambda c:
                rect_collision(((x, y), (w, h)), c), colliders
                ))
    return s


def heuristic(a, b):
    return np.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)


def astar(array, start, goal):
    if tuple(start) == tuple(goal):
        return [start]
    neighbors = np.array(((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)))
    close_set = set()

    start = tuple(start)
    goal = tuple(goal)

    came_from = {}
    gscore = {start: 0}

    fscore = {start: heuristic(start, goal)}

    oheap = []
    heapq.heappush(oheap, (fscore[start], start))

    while oheap:
        current = heapq.heappop(oheap)[1]
        if current == goal:
            data = []
            while current in came_from:
                data.append(current)

                current = came_from[current]
            return data
        close_set.add(current)

        for i, j in neighbors:

            neighbor = current[0] + i, current[1] + j

            tentative_g_score = gscore[current] + heuristic(current, neighbor)

            if 0 <= neighbor[0] < array.shape[0]:

                if 0 <= neighbor[1] < array.shape[1]:

                    if array[neighbor[0]][neighbor[1]] == 1:
                        continue

                else:

                    # array bound y walls

                    continue

            else:

                # array bound x walls

                continue

            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue

            if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap]:
                came_from[neighbor] = current

                gscore[neighbor] = tentative_g_score

                fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)

                heapq.heappush(oheap, (fscore[neighbor], neighbor))

    return [start]


def trajectory(tile_map: np.ndarray, start: tuple, goal: tuple) -> list:
    return [list(start)] + list(map(list, astar(tile_map, start, goal)[::-1]))


def get_next_positions(tile_map=None, agents=None, goal=None) -> list:
    tiles = tile_map.copy()
    s = []
    for passenger in agents:
        next_point = trajectory(tiles, passenger, goal)[1]
        s += [next_point]
        tiles[next_point[0]][next_point[1]] = 1
    return s


def tile_map_with_passengers(tile_map: np.ndarray, passengers: np.ndarray) -> np.ndarray:
    tiles = tile_map.copy()
    for (i, j) in passengers:
        tiles[i][j] = 1
    return tiles


def run_simulation(project_name,
                   sim_name,
                   SCREEN_SIZE=(500, 500),
                   GRID_SIZE=(50, 50),
                   GRID_CELL_SIZE=10,
                   SVG_SCALE=1,
                   SVG_DELTA=(0, 0),
                   MODEL_FILENAME=None,
                   FONT_NAME='Arial',
                   AGENTS_AMOUNT=30,
                   PASSENGERS_SPAWN_RECTS=((25, 45, 12, 2),),
                   goal=(1, 1)):
    PASSENGERS = np.array(tuple(set(tuple(tuple(((random.randint(rect[0], rect[0] + rect[2]),
                                                  random.randint(rect[1], rect[1] + rect[3])) for _ in
                                                 range(AGENTS_AMOUNT))) for rect
                                          in PASSENGERS_SPAWN_RECTS)[0])))

    rects = get_rects(
        f"Projects/{project_name}/Models/{MODEL_FILENAME}",
        svg_delta=SVG_DELTA,
        svg_scale=SVG_SCALE
    )
    TILE_MAP = generate_tile_map(rects, GRID_SIZE, GRID_CELL_SIZE)

    obstacles = tuple(
        tuple((x, y) if intersects(
            (x * GRID_CELL_SIZE, y * GRID_CELL_SIZE), rects) else None for y in range(len(TILE_MAP[0]))) for x in
        range(len(TILE_MAP)))

    obstacles = list(filter(lambda x: x is not None, itertools.chain(*obstacles)))
    pygame.init()
    font = pygame.font.SysFont(FONT_NAME, 20)
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()
    running = True

    settings = {'show_colliders': True,
                'show_map': True,
                'show_tile_map': False,
                'show_passengers': True}

    simulation_filename = f"Projects/{project_name}/Simulations/{sim_name}.json"
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
                if event.key == pygame.K_w:
                    settings['show_colliders'] = not settings['show_colliders']
                if event.key == pygame.K_e:
                    settings['show_map'] = not settings['show_map']
                if event.key == pygame.K_r:
                    settings['show_tile_map'] = not settings['show_tile_map']

        # Make white screen background
        screen.fill((255, 255, 255))

        # Draw map
        if settings['show_map']:
            for rect in rects:
                pygame.draw.rect(screen, rect[-1], (rect[0], rect[1]))

        # Draw colliders
        if settings['show_colliders']:
            for c in obstacles:
                x, y = c
                rect = ((x * GRID_CELL_SIZE, y * GRID_CELL_SIZE),
                        (GRID_CELL_SIZE, GRID_CELL_SIZE))
                pygame.draw.rect(screen, (0, 255, 0), rect, 1)

        pos = pygame.mouse.get_pos()
        pos = tuple(x // GRID_CELL_SIZE for x in pos)

        if settings['show_tile_map']:
            for x in range(GRID_SIZE[0]):
                for y in range(GRID_SIZE[1]):
                    if TILE_MAP[x][y] == 0:
                        rect = ((x * GRID_CELL_SIZE, y * GRID_CELL_SIZE),
                                (GRID_CELL_SIZE, GRID_CELL_SIZE))
                        pygame.draw.rect(screen, (0, 0, 255), rect, 1)

        if settings['show_passengers']:
            for x, y in PASSENGERS:
                rect = ((x * GRID_CELL_SIZE, y * GRID_CELL_SIZE),
                        (GRID_CELL_SIZE, GRID_CELL_SIZE))

                pygame.draw.rect(screen,
                                 (0, 0, 255),
                                 rect
                                 )

        PASSENGERS = get_next_positions(
            tile_map=tile_map_with_passengers(TILE_MAP, PASSENGERS),
            agents=PASSENGERS,
            goal=goal
        )

        meta = {
            "SCREEN_SIZE": SCREEN_SIZE,
            "GRID_SIZE": GRID_SIZE,
            "GRID_CELL_SIZE": GRID_CELL_SIZE,
            "SVG_SCALE": SVG_SCALE,
            "SVG_DELTA": SVG_DELTA,
            "MODEL_FILENAME": MODEL_FILENAME,
            "FONT_NAME": FONT_NAME
        }
        save_points(list(map(lambda x: (x[0].item(), x[1].item()), PASSENGERS)), meta, simulation_filename)

        for passenger in PASSENGERS:
            if heuristic(passenger, goal) < 3:
                PASSENGERS.remove(passenger)

        if len(PASSENGERS) == 0:
            sys.exit()

        text_to_show = font.render(f"{int(clock.get_fps())} {pos} | Agents-amount: {len(PASSENGERS)}", 0, (0, 0, 0))
        screen.blit(text_to_show, (10, 10))

        pygame.gfxdraw.rectangle(screen,
                                 ((0, 0), (GRID_SIZE[0] * GRID_CELL_SIZE, GRID_SIZE[1] * GRID_CELL_SIZE)),
                                 (0, 255, 255))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    # create_new_project('TestProject')
    run_simulation('TestProject', 'TestSimulation',
                   MODEL_FILENAME='Box2.svg',
                   SVG_DELTA=(0, 100))
