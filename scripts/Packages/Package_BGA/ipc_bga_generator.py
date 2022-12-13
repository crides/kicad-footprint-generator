#!/usr/bin/env python3

import math
import os
import sys
import argparse
import yaml
from pathlib import Path
import itertools

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))

from KicadModTree import *  # NOQA
from KicadModTree.nodes.base.Pad import Pad  # NOQA
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools

from KicadModTree import *
from string import ascii_uppercase

def generateFootprint(config, fpParams, fpId):
    createFp = False
    
    # use IPC-derived pad size if possible, then fall back to user-defined pads
    if "ball_type" in fpParams and "ball_diameter" in fpParams:
        try:
            padSize = configuration[fpParams["ball_type"]]
            try:
                padSize = configuration[fpParams["ball_type"]][fpParams["ball_diameter"]]["max"]
                fpParams["pad_size"] = [padSize, padSize]
                createFp = True
            except KeyError as e:
                print("{}mm is an invalid ball diameter. See ipc_7351b_bga_land_patterns.yaml for valid values. No footprint generated.".format(e))
        except KeyError:
            print("{} is an invalid ball type. See ipc_7351b_bga_land_patterns.yaml for valid values. No footprint generated.".format(e))
        
        if "pad_diameter" in fpParams:
            print("Pad size is being derived using IPC rules even though pad diameter is defined.")
    elif "ball_type" in fpParams and not "ball_diameter" in fpParams:
        raise KeyError("Ball diameter is missing. No footprint generated.")
    elif "ball_diameter" in fpParams and not "ball_type" in fpParams:
        raise KeyError("Ball type is missing. No footprint generated.")
    elif "pad_diameter" in fpParams:
        fpParams["pad_size"] = [fpParams["pad_diameter"], fpParams["pad_diameter"]]
        print("Pads size is set by the footprint definition. This should only be done for manufacturer-specific footprints.")
        createFp = True
    else:
        print("The config file must include 'ball_type' and 'ball_diameter' or 'pad_diameter'. No footprint generated.")

    if createFp:
        __createFootprintVariant(config, fpParams, fpId)


def compute_stagger(lParams):
    staggered = lParams.get('staggered')
    pitch = lParams.get('pitch')

    if staggered and pitch is not None:
        height = pitch * math.sin(math.radians(60))
        if staggered.lower() == 'x':
            return pitch/2, height, 'x'
        elif staggered.lower() == 'y':
            return height, pitch/2, 'y'
        else:
            raise ValueError('staggered must be either "x" or "y"')

    pitchX = lParams.get('pitch_x', pitch)
    pitchY = lParams.get('pitch_y', pitch)

    if not (pitchX and pitchY):
        raise KeyError('{}: Either pitch or both pitch_x and pitch_y must be given.'.format(fpId))

    return pitchX, pitchY, None


def __createFootprintVariant(config, fpParams, fpId):
    pkgX = fpParams["body_size_x"]
    pkgY = fpParams["body_size_y"]
    layoutX = fpParams["layout_x"]
    layoutY = fpParams["layout_y"]
    fFabRefRot = 0

    if "additional_tags" in fpParams:
        additionalTag = " " + fpParams["additional_tags"]
    else:
        additionalTag = ""
    
    f = Footprint(fpId)
    f.setAttribute("smd")
    if "mask_margin" in fpParams:
        f.setMaskMargin(fpParams["mask_margin"])
    if "paste_margin" in fpParams:
        f.setPasteMargin(fpParams["paste_margin"])
    if "paste_ratio" in fpParams:
        f.setPasteMarginRatio(fpParams["paste_ratio"])

    s1 = [1.0, 1.0]
    if pkgX < 4.3 and pkgY > pkgX:
      s2 = [min(1.0, round(pkgY / 4.3, 2))] * 2 # Y size is greater, so rotate F.Fab reference
      fFabRefRot = -90
    else:
      s2 = [min(1.0, round(pkgX / 4.3, 2))] * 2

    t1 = 0.15 * s1[0]
    t2 = 0.15 * s2[0]

    chamfer = min(config['fab_bevel_size_absolute'], min(pkgX, pkgY) * config['fab_bevel_size_relative'])
    
    silkOffset = config['silk_fab_offset']
    crtYdOffset = config['courtyard_offset']['bga']
    
    def crtYdRound(x):
        # Round away from zero for proper courtyard calculation
        neg = x < 0
        if neg:
            x = -x
        x = math.ceil(x * 100) / 100.0
        if neg:
            x = -x
        return x

    pitchX, pitchY, staggered = compute_stagger(fpParams)

    xCenter = 0.0
    xLeftFab = xCenter - pkgX / 2.0
    xRightFab = xCenter + pkgX / 2.0
    xChamferFab = xLeftFab + chamfer
    xPadLeft = xCenter - pitchX * ((layoutX - 1) / 2.0)
    xLeftCrtYd = crtYdRound(xCenter - (pkgX / 2.0 + crtYdOffset))
    xRightCrtYd = crtYdRound(xCenter + (pkgX / 2.0 + crtYdOffset))

    yCenter = 0.0
    yTopFab = yCenter - pkgY / 2.0
    yBottomFab = yCenter + pkgY / 2.0
    yChamferFab = yTopFab + chamfer
    yPadTop = yCenter - pitchY * ((layoutY - 1) / 2.0)
    yTopCrtYd = crtYdRound(yCenter - (pkgY / 2.0 + crtYdOffset))
    yBottomCrtYd = crtYdRound(yCenter + (pkgY / 2.0 + crtYdOffset))
    yRef = yTopFab - 1.0
    yValue = yBottomFab + 1.0

    wFab = configuration['fab_line_width']
    wCrtYd = configuration['courtyard_line_width']
    wSilkS = configuration['silk_line_width']

    # silkOffset should comply with pad clearance as well
    xSilkOffset = max(silkOffset,
                     xLeftFab + config['silk_pad_clearance'] + wSilkS / 2.0 -(xPadLeft - fpParams["pad_size"][0] / 2.0 ))
    ySilkOffset = max(silkOffset,
                     yTopFab + config['silk_pad_clearance'] + wSilkS / 2.0 -(yPadTop - fpParams["pad_size"][1] / 2.0 ))

    silkChamfer = min(config['fab_bevel_size_absolute'], min(pkgX+2*(xSilkOffset-silkOffset), pkgY+2*(ySilkOffset-silkOffset)) * config['fab_bevel_size_relative'])

    xLeftSilk = xLeftFab - xSilkOffset
    xRightSilk = xRightFab + xSilkOffset
    xChamferSilk = xLeftSilk + silkChamfer
    yTopSilk = yTopFab - ySilkOffset
    yBottomSilk = yBottomFab + ySilkOffset
    yChamferSilk = yTopSilk + silkChamfer

    # Text
    f.append(Text(type="reference", text="REF**", at=[xCenter, yRef],
                  layer="F.SilkS", size=s1, thickness=t1))
    f.append(Text(type="value", text=fpId, at=[xCenter, yValue],
                  layer="F.Fab", size=s1, thickness=t1))
    f.append(Text(type="user", text='${REFERENCE}', at=[xCenter, yCenter],
                  layer="F.Fab", size=s2, thickness=t2, rotation=fFabRefRot))

    # Fab
    f.append(PolygoneLine(polygone=[[xRightFab, yBottomFab],
                                    [xLeftFab, yBottomFab],
                                    [xLeftFab, yChamferFab],
                                    [xChamferFab, yTopFab],
                                    [xRightFab, yTopFab],
                                    [xRightFab, yBottomFab]],
                          layer="F.Fab", width=wFab))

    # Courtyard
    f.append(RectLine(start=[xLeftCrtYd, yTopCrtYd],
                      end=[xRightCrtYd, yBottomCrtYd],
                      layer="F.CrtYd", width=wCrtYd))

    # Silk
    f.append(PolygoneLine(polygone=[[xChamferSilk, yTopSilk],
                                    [xRightSilk, yTopSilk],
                                    [xRightSilk, yBottomSilk],
                                    [xLeftSilk, yBottomSilk],
                                    [xLeftSilk, yChamferSilk]],
                          layer="F.SilkS", width=wSilkS))

    # Pads
    balls = makePadGrid(f, fpParams, config, xCenter=xCenter, yCenter=yCenter)

    for layout in fpParams.get('secondary_layouts', []):
        balls += makePadGrid(f, layout, config, fpParams, xCenter=xCenter, yCenter=yCenter)
    
    # If this looks like a CSP footprint, use the CSP 3dshapes library
    packageType = 'CSP' if 'BGA' not in fpId and 'CSP' in fpId else 'BGA'

    f.append(Model(filename="{}Package_{}.3dshapes/{}.wrl".format(
                  config['3d_model_prefix'], packageType, fpId)))

    if staggered:
        pdesc = str(fpParams.get('pitch')) if 'pitch' in fpParams else f'{pitchX}x{pitchY}'
        sdesc = f'{staggered.upper()}-staggered '
    else:
        pdesc = str(pitchX) if pitchX == pitchY else f'{pitchX}x{pitchY}'
        sdesc = ''

    f.setDescription(f'{fpParams["description"]}, {pkgX}x{pkgY}mm, {balls} Ball, {sdesc}{layoutX}x{layoutY} Layout, {pdesc}mm Pitch, {fpParams["size_source"]}') #NOQA
    f.setTags(f'{packageType} {balls} {pdesc}{additionalTag}')

    outputDir = Path(f'Package_{packageType}.pretty')
    outputDir.mkdir(exist_ok=True)
    
    file_handler = KicadFileHandler(f)
    file_handler.writeFile(str(outputDir / f'{fpId}.kicad_mod'))

def makePadGrid(f, lParams, config, fpParams={}, xCenter=0.0, yCenter=0.0):
    layoutX = lParams["layout_x"]
    layoutY = lParams["layout_y"]
    rowNames = lParams.get('row_names', fpParams.get('row_names', config['row_names']))[:layoutY]
    rowSkips = lParams.get('row_skips', [])
    areaSkips = lParams.get('area_skips', [])
    padSkips = {skip.upper() for skip in lParams.get('pad_skips', [])}
    pitchX, pitchY, staggered = compute_stagger(lParams)

    for row_start, col_start, row_end, col_end in areaSkips:
        rows = rowNames[rowNames.index(row_start.upper()):rowNames.index(row_end.upper())+1]
        cols = range(col_start, col_end+1)
        padSkips |= {f'{a}{b}' for a, b in itertools.product(rows, cols)}

    for row, skips in zip(rowNames, rowSkips):
        for skip in skips:
            if isinstance(skip, int):
                padSkips.add(f'{row}{skip}')
            else:
                padSkips |= {f'{row}{skip}' for skip in range(*skip)}

    if (first_ball := lParams.get('first_ball')):
        if not staggered:
            raise ValueError('first_ball only makes sense for staggered layouts.')

        if first_ball not in ('A1', 'B1', 'A2'):
            raise ValueError('first_ball must be "A1" or "A2".')

        skip_even = (first_ball != 'A1')

        for row_num, row in enumerate(rowNames):
            for col in range(layoutX):
                is_even = (row_num + col) % 2 == 0
                if is_even == skip_even:
                    padSkips.add(f'{row}{col+1}')

    padShape = {
            'circle': Pad.SHAPE_CIRCLE,
            'rect': Pad.SHAPE_RECT,
            'roundrect': Pad.SHAPE_ROUNDRECT,
            }[lParams.get('pad_shape', fpParams.get('pad_shape', 'circle'))]

    xOffset = lParams.get('offset_x', 0.0)
    yOffset = lParams.get('offset_y', 0.0)
    xPadLeft = xCenter - pitchX * ((layoutX - 1) / 2.0) + xOffset
    yPadTop = yCenter - pitchY * ((layoutY - 1) / 2.0) + yOffset

    for rowNum, row in enumerate(rowNames):
        rowSet = {col for col in range(1, layoutX+1) if f'{row}{col}' not in padSkips}
        for col in rowSet:
            f.append(Pad(number="{}{}".format(row, col), type=Pad.TYPE_SMT,
                         shape=padShape,
                         at=[xPadLeft + (col-1) * pitchX, yPadTop + rowNum * pitchY],
                         size=lParams.get('pad_size') or fpParams['pad_size'],
                         layers=Pad.LAYERS_SMT, 
                         radius_ratio=config['round_rect_radius_ratio']))

    return layoutX * layoutY - len(padSkips)

def rowNameGenerator(seq):
    for n in itertools.count(1):
        for s in itertools.product(seq, repeat=n):
            yield ''.join(s)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='use config .yaml files to create footprints.')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of files holding information about what devices should be created.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    # parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../package_config_KLCv3.yaml')
    parser.add_argument('--ipc_doc', type=str, nargs='?', help='IPC definition document', default='ipc_7351b_bga_land_patterns.yaml')
    parser.add_argument('-v', '--verbose', action='count', help='set debug level')
    args = parser.parse_args()
    
    if args.verbose:
        DEBUG_LEVEL = args.verbose
    
    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    # with open(args.series_config, 'r') as config_stream:
        # try:
            # configuration.update(yaml.safe_load(config_stream))
        # except yaml.YAMLError as exc:
            # print(exc)
    
    with open(args.ipc_doc, 'r') as config_stream:
        try:
            configuration.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    # generate dict of A, B .. Y, Z, AA, AB .. CY less easily-confused letters
    rowNamesList = [x for x in ascii_uppercase if x not in 'IOQSXZ']
    configuration.update({'row_names': list(itertools.islice(rowNameGenerator(rowNamesList), 80))})

    for filepath in args.files:
        with open(filepath, 'r') as command_stream:
            try:
                cmd_file = yaml.safe_load(command_stream)
            except yaml.YAMLError as exc:
                print(exc)
        for pkg in cmd_file:
            print("generating part for parameter set {}".format(pkg))
            generateFootprint(configuration, cmd_file[pkg], pkg)
