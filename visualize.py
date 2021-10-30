import itertools
import json
import sys
from xml.dom import minidom

import numpy
import pygame.gfxdraw

import numpy as np
import pygame

from colour import Color

from utilities import get_rects, intersects, generate_tile_map
from utilities import cv_col, arrow


def load_next_positions(d=1):
    global FRAME_N, paths, calculated
    FRAME_N += d
    FRAME_N %= len(paths)
    if FRAME_N == 0:
        calculated['density_map'] = True
        calculated['stuck_map'] = True
    return paths[FRAME_N]


def run_visualization(project_name, simulation_name):
    global FRAME_N, paths, calculated

    simulation_data = json.load(open(f"Projects/{project_name}/Simulations/{simulation_name}.json", mode='r'))
    meta, paths = simulation_data['meta'], simulation_data['paths']
    PASSENGERS = simulation_data['paths'][0]

    SCREEN_SIZE = meta['SCREEN_SIZE']
    GRID_SIZE = meta['GRID_SIZE']
    GRID_CELL_SIZE = meta['GRID_CELL_SIZE']
    SVG_SCALE = meta['SVG_SCALE']
    SVG_DELTA = meta['SVG_DELTA']
    MODEL_FILENAME = meta['MODEL_FILENAME']
    FONT_NAME = meta['FONT_NAME']
    FRAME_N = 0

    rects = get_rects(
        f"Projects/{project_name}/Models/{MODEL_FILENAME}",
        svg_delta=SVG_DELTA,
        svg_scale=SVG_SCALE
    )

    TILE_MAP = generate_tile_map(rects, GRID_SIZE, GRID_CELL_SIZE)
    DENSITY_MAP = np.zeros(GRID_SIZE)
    STUCK_MAP = np.zeros(GRID_SIZE)

    red = Color("yellow")
    colors = list(red.range_to(Color("red"), 255))

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

    settings = {'show_colliders': False,
                'show_map': True,
                'show_tile_map': False,
                'show_passengers': True,
                'auto_animation': True,
                'density_map': False,
                'stuck_map': True
                }
    calculated = {'density_map': False,
                  'stuck_map': False}

    PREVIOUS_PASSENGERS = PASSENGERS[::-1]
    max_stuck_value = 0
    max_destiny_value = 0

    STUCK_VECTORS = set()

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

                if event.key == pygame.K_SPACE:
                    settings['auto_animation'] = not settings['auto_animation']

                if not settings['auto_animation']:
                    if event.key == pygame.K_RIGHT:
                        PASSENGERS = load_next_positions(1)
                    if event.key == pygame.K_LEFT:
                        PASSENGERS = load_next_positions(-1)

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
            for i in range(GRID_SIZE[0]):
                for j in range(GRID_SIZE[1]):
                    if TILE_MAP[i][j] == 0:
                        rect = ((i * GRID_CELL_SIZE, j * GRID_CELL_SIZE),
                                (GRID_CELL_SIZE, GRID_CELL_SIZE))
                        pygame.draw.rect(screen, (240, 240, 240), rect, 1)

        if not calculated['density_map']:
            for passenger in PASSENGERS:
                DENSITY_MAP[passenger[0]][passenger[1]] += 1
            max_destiny_value = numpy.amax(DENSITY_MAP)

        if settings['density_map']:
            for i in range(DENSITY_MAP.shape[0]):
                for j in range(DENSITY_MAP.shape[1]):
                    v = DENSITY_MAP[i][j] / max_destiny_value
                    rect = ((i * GRID_CELL_SIZE, j * GRID_CELL_SIZE),
                            (GRID_CELL_SIZE, GRID_CELL_SIZE))
                    if v > 0:
                        pygame.gfxdraw.rectangle(screen,
                                                 rect,
                                                 (tuple(
                                                     map(lambda x: int(x * 255),
                                                         colors[int((len(colors) - 1) * v)].rgb)))
                                                 )

        if not calculated['stuck_map']:
            if settings['auto_animation']:
                for i, passenger in enumerate(PASSENGERS):
                    if i < len(PREVIOUS_PASSENGERS) and passenger == PREVIOUS_PASSENGERS[i]:
                        STUCK_MAP[passenger[0]][passenger[1]] += 1
                max_stuck_value = numpy.amax(STUCK_MAP)
        else:
            if settings['auto_animation']:
                if len(PASSENGERS) == len(PREVIOUS_PASSENGERS):
                    for i, passenger in enumerate(PASSENGERS):
                        prev = PREVIOUS_PASSENGERS[i]
                        if STUCK_MAP[passenger[0]][passenger[1]] >= max_stuck_value / 2:
                            STUCK_VECTORS.add((tuple(prev), tuple(passenger)))

        PREVIOUS_PASSENGERS = PASSENGERS[:]

        if settings['stuck_map']:
            for i in range(STUCK_MAP.shape[0]):
                for j in range(STUCK_MAP.shape[1]):
                    v = STUCK_MAP[i][j] / max_stuck_value

                    rect = ((i * GRID_CELL_SIZE, j * GRID_CELL_SIZE),
                            (GRID_CELL_SIZE, GRID_CELL_SIZE))
                    if v > 0:
                        pygame.gfxdraw.rectangle(screen,
                                                 rect,
                                                 (tuple(
                                                     map(lambda x: int(x * 255),
                                                         colors[int((len(colors) - 1) * v)].rgb)))
                                                 )

            for vec in STUCK_VECTORS:
                c1, c2 = vec
                h = GRID_CELL_SIZE // 2
                k = 3

                module = (c2[0] - c1[0]) * k * GRID_CELL_SIZE, (c2[1] - c1[1]) * k * GRID_CELL_SIZE

                pygame.draw.line(screen, (0, 0, 0), (c1[0] * GRID_CELL_SIZE + h, c1[1] * GRID_CELL_SIZE + h),
                                 (c1[0] * GRID_CELL_SIZE + h + module[0], c1[1] * GRID_CELL_SIZE + h + module[1]), 1)

                if c1 != c2:
                    c2 = (c1[0] * GRID_CELL_SIZE + h + module[0], c1[1] * GRID_CELL_SIZE + h + module[1])
                    c1 = (c1[0] * GRID_CELL_SIZE + h, c1[1] * GRID_CELL_SIZE + h)
                    ac1, ac2 = arrow(c1, c2, l2=5, O=0.5)

                    pygame.draw.line(screen, (0, 0, 0), c2, ac1, 1)
                    pygame.draw.line(screen, (0, 0, 0), c2, ac2, 1)

        if settings['show_passengers']:
            for x, y in PASSENGERS:
                rect = ((x * GRID_CELL_SIZE, y * GRID_CELL_SIZE),
                        (GRID_CELL_SIZE, GRID_CELL_SIZE))

                pygame.draw.rect(screen, (0, 0, 255), rect)

        if settings['auto_animation']:
            PASSENGERS = load_next_positions()

        text_to_show = font.render(f"{int(clock.get_fps())} {pos} | Frame-N: {FRAME_N}", 0, (0, 0, 0))
        screen.blit(text_to_show, (10, 10))

        pygame.gfxdraw.rectangle(screen,
                                 ((0, 0), (GRID_SIZE[0] * GRID_CELL_SIZE, GRID_SIZE[1] * GRID_CELL_SIZE)),
                                 (0, 255, 255))
        pygame.display.flip()
        clock.tick(24)

    pygame.quit()


if __name__ == "__main__":
    run_visualization('TestProject', 'TestSimulation')
