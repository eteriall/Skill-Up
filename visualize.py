import argparse
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
from utilities import cv_col, arrow, discrete_png


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

    simulation_data = json.load(open(f"Projects/{project_name}/Simulations/{simulation_name}", mode='r'))
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

    if MODEL_FILENAME.endswith('.svg'):
        DRAW_TYPE = 'svg'
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
    else:
        DRAW_TYPE = 'png'
        # background_img = pygame.image.load(f"Projects/{project_name}/Models/bg-{MODEL_FILENAME}").convert_alpha()

        TILE_MAP = discrete_png(
            f"Projects/{project_name}/Models/{MODEL_FILENAME}",
            GRID_SIZE,
            image_delta=SVG_DELTA,
            image_scale=SVG_SCALE
        )
        obstacles = tuple(
            tuple((i, j) if TILE_MAP[i][j] else None for j in range(len(TILE_MAP[0]))) for i in
            range(len(TILE_MAP)))
        GRID_SIZE = TILE_MAP.shape

    DENSITY_MAP = np.zeros(GRID_SIZE)
    STUCK_MAP = np.zeros(GRID_SIZE)

    colors = list(Color("yellow").range_to(Color("red"), 255))

    obstacles = list(filter(lambda x: x is not None, itertools.chain(*obstacles)))
    pygame.init()
    font = pygame.font.SysFont(FONT_NAME, 20)
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()
    running = True

    settings = {'show_colliders': True,
                'show_map': True,
                'show_tile_map': False,
                'show_passengers': True,
                'auto_animation': True,
                'density_map': False,
                'stuck_map': True,
                'reset_maps': False
                }
    KEY_BINDINGS = {
        'show_colliders': pygame.K_w,
        'show_map': pygame.K_e,
        'show_tile_map': pygame.K_r,
        'show_passengers': pygame.K_p,
        'auto_animation': pygame.K_SPACE,
        'density_map': pygame.K_a,
        'stuck_map': pygame.K_s,
        'reset_maps': pygame.K_f
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
                    pygame.display.quit()
                    pygame.quit()

                for parameter in KEY_BINDINGS:
                    if event.key == KEY_BINDINGS[parameter]:
                        settings[parameter] = not settings[parameter]

                if not settings['auto_animation']:
                    if event.key == pygame.K_RIGHT:
                        PASSENGERS = load_next_positions(1)
                    if event.key == pygame.K_LEFT:
                        PASSENGERS = load_next_positions(-1)

        if settings['reset_maps']:
            DENSITY_MAP = np.zeros(GRID_SIZE)
            STUCK_MAP = np.zeros(GRID_SIZE)
            for key in calculated:
                calculated[key] = False
            FRAME_N = 0
            settings['reset_maps'] = False

        # Make white screen background
        screen.fill((255, 255, 255))

        # Draw map
        if DRAW_TYPE == 'svg':
            if settings['show_map']:
                for rect in rects:
                    pygame.draw.rect(screen, rect[-1], (rect[0], rect[1]))

        # Draw colliders
        if settings['show_colliders']:
            for c in obstacles:
                x, y = c
                rect = ((x * GRID_CELL_SIZE, y * GRID_CELL_SIZE),
                        (GRID_CELL_SIZE, GRID_CELL_SIZE))
                pygame.draw.rect(screen, (93, 45, 92), rect, 1)

        if settings['show_tile_map']:
            for i in range(len(TILE_MAP)):
                for j in range(len(TILE_MAP[0])):
                    if TILE_MAP[i][j] == 0:
                        rect = ((i * GRID_CELL_SIZE, j * GRID_CELL_SIZE),
                                (GRID_CELL_SIZE, GRID_CELL_SIZE))
                        pygame.draw.rect(screen, (240, 240, 240), rect, 1)

        if not calculated['density_map']:
            for passenger in PASSENGERS:
                DENSITY_MAP[passenger[0]][passenger[1]] += 1
            max_destiny_value = numpy.amax(DENSITY_MAP)

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

        if settings['density_map']:
            for i in range(DENSITY_MAP.shape[0]):
                for j in range(DENSITY_MAP.shape[1]):
                    v = DENSITY_MAP[i][j] / max_destiny_value
                    rect = ((i * GRID_CELL_SIZE, j * GRID_CELL_SIZE),
                            (GRID_CELL_SIZE, GRID_CELL_SIZE))
                    if v > 0:
                        if not settings['stuck_map']:
                            pygame.draw.rect(screen, (tuple(map(lambda x: int(x * 255),
                                                                colors[int((len(colors) - 1) * v)].rgb))), rect)
                        else:
                            pygame.gfxdraw.rectangle(screen, rect, (tuple(
                                map(lambda x: int(x * 255),
                                    colors[int((len(colors) - 1) * v)].rgb))))

        if settings['stuck_map']:
            for i in range(STUCK_MAP.shape[0]):
                for j in range(STUCK_MAP.shape[1]):
                    v = STUCK_MAP[i][j] / max_stuck_value

                    rect = ((i * GRID_CELL_SIZE, j * GRID_CELL_SIZE),
                            (GRID_CELL_SIZE, GRID_CELL_SIZE))
                    if v > 0:
                        pygame.draw.rect(screen, (tuple(map(lambda x: int(x * 255),
                                                            colors[int((len(colors) - 1) * v)].rgb))), rect)

        """for vec in STUCK_VECTORS:
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
                pygame.draw.line(screen, (0, 0, 0), c2, ac2, 1)"""

        if settings['show_passengers']:
            for x, y in PASSENGERS:
                rect = ((x * GRID_CELL_SIZE, y * GRID_CELL_SIZE),
                        (GRID_CELL_SIZE, GRID_CELL_SIZE))

                pygame.draw.rect(screen, (0, 0, 255), rect)

        pos = pygame.mouse.get_pos()
        pos = tuple(x // GRID_CELL_SIZE for x in pos)
        if settings['auto_animation']:
            PASSENGERS = load_next_positions()
        s = ['|', '/', '-', '\\']
        text_to_show = font.render(
            f"{int(clock.get_fps())} {pos} | Frame-N: {FRAME_N} | {('Baking ' + s[(FRAME_N % 10) // 3]) if not calculated['density_map'] else 'Baked!'}",
            0, (0, 0, 0))

        text_width, text_height = font.size(
            f"{int(clock.get_fps())} {pos} | Frame-N: {FRAME_N} | {('Baking ' + s[(FRAME_N % 10) // 3]) if not calculated['density_map'] else 'Baked!'}")
        screen.blit(text_to_show, (SCREEN_SIZE[0] - text_width - 10, 10))

        pygame.gfxdraw.rectangle(screen,
                                 ((0, 0), (GRID_SIZE[0] * GRID_CELL_SIZE, GRID_SIZE[1] * GRID_CELL_SIZE)),
                                 (0, 255, 255))
        pygame.display.flip()
        clock.tick(60)

    pygame.display.quit()
    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SkillUp Visualizer')
    parser.add_argument('-pn', '--PROJECT_NAME', required=True)
    parser.add_argument('-sn', '--SIM_NAME', required=True)

    args = vars(parser.parse_args())
    run_visualization(args['PROJECT_NAME'], args['SIM_NAME'])
