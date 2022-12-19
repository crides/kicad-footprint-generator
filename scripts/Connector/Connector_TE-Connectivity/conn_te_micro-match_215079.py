#!/usr/bin/env python3

"""

Drawing:
https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Customer+Drawing%7F215079%7FY1%7Fpdf%7FEnglish%7FENG_CD_215079_Y1.pdf%7F215079-4

"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join('.','..','..','..')))
sys.path.append(os.path.abspath(os.path.join('.','..','..','tools')))

import argparse
import math
import yaml
from KicadModTree import *
from footprint_text_fields import addTextFields


man_lib = 'TE-Connectivity'
man_short = 'TE'
series = 'Micro-MaTch'
series_no = '215079'
orientation = 'V'
pitch = 1.27
pitch_x = 2.54
pad_drill = 0.8
pad_size = 0.8 + 2*0.25
indexing_hole_x = 1.8
indexing_hole_y = -1.4
indexing_hole_drill = 1.5
body_width = 5.2
body_lengths = {
    4: 7.1,
    6: 9.7,
    8: 12.2,
    10: 14.7,
    12: 17.3,
    14: 19.8,
    16: 22.4,
    18: 24.9,
    20: 27.4
}
body_cutout_depth = 0.9
pins_per_row_range = (4, 6, 8, 10, 12, 14, 16, 18, 20)
drawing_url = 'https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Customer+Drawing%7F215079%7FY1%7Fpdf%7FEnglish%7FENG_CD_215079_Y1.pdf%7F215079-4'

def make_part_number(pincount):
    if pincount < 4 or pincount > 20:
        raise ValueError('Requested pin count out of series range')
    if pincount % 2 != 0:
        raise ValueError('Series supports only even numbers of pins')
    if pincount < 10:
        return f'{series_no}-{pincount}', f'7-{series_no}-{pincount}'
    if pincount < 20:
        return f'1-{series_no}-{pincount-10}', f'8-{series_no}-{pincount}'
    return f'2-{series_no}-0', f'9-{series_no}-{pincount}'


def generate_one_footprint(pincount, configuration):
    partno, alt_partno = make_part_number(pincount)
    body_length = body_lengths[pincount]

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(
        man=man_short,
        series=series,
        mpn=partno,
        num_rows=2,
        pins_per_row=pincount//2,
        mounting_pad='',
        pitch=pitch,
        orientation=orientation_str
    )
    print(footprint_name)

    # Initialize footprint
    kicad_mod = Footprint(footprint_name)
    descr_str = f'{man_lib} {series} female-on-board top-entry thru-hole {pincount} pin connector, {drawing_url}'
    keywords = []
    keywords.append(configuration['keyword_fp_string'].format(
        man=man_lib,
        series=series,
        entry=orientation_str
    ))
    keywords.append(partno)
    keywords.append(alt_partno)
    kicad_mod.setDescription(descr_str)
    kicad_mod.setTags(' '.join(keywords))

    # Create pads
    for idx in range(pincount):
        kicad_mod.append(Pad(
            number=idx+1,
            type=Pad.TYPE_THT,
            shape=Pad.SHAPE_RECT if idx == 0 else Pad.SHAPE_CIRCLE,
            layers=Pad.LAYERS_THT,
            at=((idx % 2)*pitch_x, idx*pitch),
            size=pad_size,
            drill=pad_drill))
    # Add indexing hole
    kicad_mod.append(Pad(
        type=Pad.TYPE_NPTH,
        shape=Pad.SHAPE_CIRCLE,
        layers=Pad.LAYERS_NPTH,
        size=indexing_hole_drill,
        drill=indexing_hole_drill,
        at=(indexing_hole_x, indexing_hole_y)
    ))

    # Calculate body edge
    body_edge = {
        'left': pitch_x/2 - body_width/2,
        'right': pitch_x/2 + body_width/2,
        'top': (pincount-1)*pitch/2 - body_length/2,
        'bottom': (pincount-1)*pitch/2 + body_length/2
    }

    # Add fabrication outline
    fab_polygone_points = [
        (pitch_x/2, body_edge['top'] + body_cutout_depth),
        (0, body_edge['top'] + body_cutout_depth),
        (0, body_edge['top']),
        (body_edge['left'], body_edge['top']),
        (body_edge['left'], (body_edge['top'] + body_edge['bottom'])/2)
    ]
    kicad_mod.append(PolygoneLine(
        polygone = fab_polygone_points,
        layer='F.Fab',
        width=configuration['fab_line_width']
    ))
    kicad_mod.append(PolygoneLine(
        polygone = fab_polygone_points,
        x_mirror = pitch_x/2,
        layer='F.Fab',
        width=configuration['fab_line_width']
    ))
    kicad_mod.append(PolygoneLine(
        polygone = fab_polygone_points,
        y_mirror = (pincount-1)*pitch/2,
        layer='F.Fab',
        width=configuration['fab_line_width']
    ))
    kicad_mod.append(PolygoneLine(
        polygone = fab_polygone_points,
        x_mirror = pitch_x/2,
        y_mirror = (pincount-1)*pitch/2,
        layer='F.Fab',
        width=configuration['fab_line_width']
    ))

    # Add silkscreen outline
    offs = configuration['silk_fab_offset']
    silk_polygone_points = [
        (pitch_x/2 - body_width/2 - offs, (pincount-1)*pitch/2 - body_length/2 - offs),
        (pitch_x/2 - body_width/2 - offs, (pincount-1)*pitch/2 + body_length/2 + offs),
        (pitch_x/2 + body_width/2 + offs, (pincount-1)*pitch/2 + body_length/2 + offs),
        (pitch_x/2 + body_width/2 + offs, (pincount-1)*pitch/2 - body_length/2 - offs),
    ]
    kicad_mod.append(PolygoneLine(
        polygone = silk_polygone_points,
        layer='F.SilkS',
        width=configuration['silk_line_width']
    ))

    # Pin 1 mark
    pin_mark_width = 1
    pin_mark_height = 1
    pin_mask_offset = 0.5
    pin_mark_polygone = [
        (pitch_x/2 - body_width/2 - pin_mask_offset, 0),
        (pitch_x/2 - body_width/2 - pin_mask_offset - pin_mark_width, pin_mark_height/2),
        (pitch_x/2 - body_width/2 - pin_mask_offset - pin_mark_width, -pin_mark_height/2),
        (pitch_x/2 - body_width/2 - pin_mask_offset, 0),
    ]
    kicad_mod.append(PolygoneLine(
        polygone = pin_mark_polygone,
        layer='F.SilkS',
        width=configuration['silk_line_width']
    ))
    kicad_mod.append(PolygoneLine(
        polygone = pin_mark_polygone,
        layer='F.Fab',
        width=configuration['fab_line_width']
    ))

    # Courtyard
    court_offs = configuration['courtyard_offset']['connector']
    court_grid = configuration['courtyard_grid']
    cx1 = math.floor((body_edge['left']-court_offs)/court_grid)*court_grid
    cx2 = math.ceil((body_edge['right']+court_offs)/court_grid)*court_grid
    cy1 = math.floor((body_edge['top']-court_offs)/court_grid)*court_grid
    cy2 = math.ceil((body_edge['bottom']+court_offs)/court_grid)*court_grid
    assert(abs(cx1 - body_edge['left']) >= court_offs)
    assert(abs(cx2 - body_edge['right']) >= court_offs)
    assert(abs(cy1 - body_edge['top']) >= court_offs)
    assert(abs(cy2 - body_edge['bottom']) >= court_offs)
    kicad_mod.append(RectLine(
        start=(cx1, cy1), end=(cx2, cy2),
        layer='F.CrtYd', width=configuration['courtyard_line_width']
    ))

    # Text fields
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top': cy1, 'bottom': cy2}, fp_name=footprint_name)

    # Output
    model3d_path_prefix = configuration.get('3d_model_prefix','${KICAD6_3DMODEL_DIR}/')
    lib_name = configuration['lib_name_format_string'].format(man=man_lib)
    model_name = f'{model3d_path_prefix}{lib_name}.3dshapes/{footprint_name}.wrl'
    kicad_mod.append(Model(filename=model_name))

    output_dir = f'{lib_name}.pretty/'
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    filename = f'{output_dir}{footprint_name}.kicad_mod'

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../conn_config_KLCv3.yaml')
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.series_config, 'r') as config_stream:
        try:
            configuration.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    for pins_per_row in pins_per_row_range:
        generate_one_footprint(pins_per_row, configuration)
