# -*- coding: utf-8 -*-

"""
# File name:    script_find_direction.py
# Time :        2022/2/28
# Author:       xyguoo@163.com
# Description:  
"""
import sys

sys.path.append('.')

import os
import tqdm

from ui.backend import Backend
from util.canvas_grid import Canvas
import numpy as np

import pickle
from util.mask_color_util import mask_to_rgb
from common_dataset import DataFilter
from util.imutil import read_rgb, write_rgb
from shape_branch.config import cfg
from util.find_semantic_direction import get_random_direction

df = DataFilter(cfg)
be = Backend(2.5, blending=False)

exist_direction = '/workspace/CtrlHair/model_trained/shape/%s' % cfg.experiment_name
code_dim = cfg.hair_dim
att_name = 'shape'
interpolate_num = 6
max_val = 2.5
batch = 10

interpolate_values = np.linspace(-max_val, max_val, interpolate_num)

existing_dirs_dir = os.path.join(exist_direction, '%s_dir_used' % att_name)

existing_dirs_list = os.listdir(existing_dirs_dir)
existing_dirs = []
for dd in existing_dirs_list:
    with open(os.path.join(existing_dirs_dir, dd), 'rb') as f:
        existing_dirs.append(pickle.load(f))

direction_dir = '%s/direction_find/%s_dir_%d' % (exist_direction, att_name, len(existing_dirs) + 1)
img_gen_dir = '%s/direction_find/%s_%d' % (exist_direction, att_name, len(existing_dirs) + 1)
for dd in [direction_dir, img_gen_dir]:
    if not os.path.exists(dd):
        os.makedirs(dd)

img_list = df.train_list

for dir_idx in tqdm.tqdm(range(0, 300)):
    rand_dir = get_random_direction(code_dim, existing_dirs)
    with open('%s/%d.pkl' % (direction_dir, dir_idx,), 'wb') as f:
        pickle.dump(rand_dir, f)
    rand_dir = rand_dir.to(be.device)

    canvas = Canvas(batch * 2, interpolate_num + 1)
    for img_idx, img_file in tqdm.tqdm(enumerate(img_list[:batch])):
        img = read_rgb(img_file)
        _, img_parsing = be.set_input_img(img)

        canvas.process_draw_image(img, img_idx * 2, 0)
        canvas.process_draw_image(img_parsing, img_idx * 2 + 1, 0)

        for inter_idx in range(interpolate_num):
            inter_val = interpolate_values[inter_idx]
            be.continue_change_with_direction(att_name, rand_dir, inter_val)

            out_img = be.output()
            canvas.process_draw_image(out_img, img_idx * 2, inter_idx + 1)
            canvas.process_draw_image(mask_to_rgb(be.cur_mask), img_idx * 2 + 1, inter_idx + 1)
    write_rgb('%s/%d.png' % (img_gen_dir, dir_idx), canvas.canvas)
