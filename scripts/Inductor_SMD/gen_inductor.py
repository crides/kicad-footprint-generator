#####
# Usage : python gen_inductor.py <inputfile.yaml> <outputPath>

#!/usr/bin/env python3

import sys
import os
import yaml
from pathlib import Path
import csv

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", ".."))
sys.path.append(os.path.join(sys.path[0], ".."))
from KicadModTree import *


if len(sys.argv) != 3:
    print(f'Usage : python gen_inductor.py <inputfile.yaml> <outputPath>')
    exit(0)
else:
    outputPath = Path(sys.argv[2])
    print(f'output folder is {outputPath}')
    batchInputFile = Path(sys.argv[1])

silkscreenOffset = 0.2
fabOffset = 0.0
courtyardOffset = 0.25      # 0.25 per KLC

with open(batchInputFile, 'r') as stream:
    data_loaded = yaml.safe_load(stream)

    for yamlBlocks in range(0, len(data_loaded)): # For each series block in the yaml file, we process the CSV
        seriesName = data_loaded[yamlBlocks]['series']
        seriesManufacturer = data_loaded[yamlBlocks]['manufacturer']
        seriesDatasheet = data_loaded[yamlBlocks]['datasheet']
        seriesCsv = data_loaded[yamlBlocks]['csv']
        seriesTags = data_loaded[yamlBlocks]['tags']      # space delimited list of the tags
        seriesTagsString = ' '.join(seriesTags)

        with open(seriesCsv) as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                widthX = float(row['widthX'])
                lengthY = float(row['lengthY'])
                padX = float(row['padX'])
                padY = float(row['padY'])
                padGap = float(row['padGap'])
                partName = row['PartNumber']
                
                footprint_name = f'L_{seriesManufacturer}_{partName}'
                print(f'Processing {footprint_name}')

                # Silkscreen corners
                vertLen = (lengthY/2 - padY/2) + silkscreenOffset - 0.2
                horzLen = (widthX/2 - padX/2) + silkscreenOffset - 0.2

                leftX = 0-widthX/2-silkscreenOffset
                rightX = widthX/2+silkscreenOffset
                upperY = 0-lengthY/2-silkscreenOffset
                lowerY = lengthY/2+silkscreenOffset
                

                # init kicad footprint
                kicad_mod = Footprint(footprint_name)
                kicad_mod.setDescription(f"Inductor, {seriesManufacturer}, {partName}, {widthX}mmx{lengthY}mm, {seriesDatasheet}")
                kicad_mod.setTags(f"Inductor {seriesTagsString}")
                kicad_mod.setAttribute("smd")
                # set general values
                kicad_mod.append(Text(type='reference', text='REF**', at=[0, 0-lengthY/2-1], layer='F.SilkS'))
                
                kicad_mod.append(Text(type='value', text=footprint_name, at=[0, lengthY/2+1], layer='F.Fab'))
                scaling = padX/3
                clampscale = clamp(scaling, 0.5, 1)
                
                # Check if our part is so small that REF will overlap the pads. Rotate it to fit.
                if padX + padGap < 2:
                    y=lengthY/2+2
                    rot = 90
                else:
                    y=0
                    rot = 0
                kicad_mod.append(Text(type='user', text='${REFERENCE}', at=[0, 0], layer='F.Fab', rotation=rot, size=[clampscale, clampscale], thickness=clampscale*0.15))


                # create silkscreen
                #kicad_mod.append(RectLine(start=[0-width/2-silkscreenOffset, 0-height/2-silkscreenOffset], end=[width/2+silkscreenOffset, height/2+silkscreenOffset], layer='F.SilkS'))

                #kicad_mod.append(Line(start=[leftX, upperY], end=[leftX+horzLen, upperY], layer='F.SilkS'))
                kicad_mod.append(Line(start=[leftX, upperY], end=[rightX, upperY], layer='F.SilkS'))     # Full upper line
                kicad_mod.append(Line(start=[leftX, upperY], end=[leftX, upperY + vertLen], layer='F.SilkS')) # Tick down left

                #kicad_mod.append(Line(start=[rightX, upperY], end=[rightX-horzLen, upperY], layer='F.SilkS'))
                kicad_mod.append(Line(start=[rightX, upperY], end=[rightX, upperY + vertLen], layer='F.SilkS')) # Tick down right

                #kicad_mod.append(Line(start=[leftX, lowerY], end=[leftX+horzLen, lowerY], layer='F.SilkS'))
                kicad_mod.append(Line(start=[leftX, lowerY], end=[leftX, lowerY - vertLen], layer='F.SilkS')) # Tick up left
                kicad_mod.append(Line(start=[leftX, lowerY], end=[rightX, lowerY], layer='F.SilkS')) # Full line
                #kicad_mod.append(Line(start=[rightX, lowerY], end=[rightX-horzLen, lowerY], layer='F.SilkS'))
                kicad_mod.append(Line(start=[rightX, lowerY], end=[rightX, lowerY - vertLen], layer='F.SilkS')) # Tick up right




                # fab layer
                kicad_mod.append(RectLine(start=[0-widthX/2-fabOffset, 0-lengthY/2-fabOffset], end=[widthX/2+fabOffset, lengthY/2+fabOffset], layer='F.Fab'))

                # create COURTYARD
                # Base it off the copper or physical, whichever is biggest. Need to check both X and Y.
                
                # Extreme right edge
                rightCopperMax= padGap/2 + padX
                rightPhysicalMax = widthX / 2
                if rightCopperMax > rightPhysicalMax:    # Copper is bigger
                    widest = padGap + (padX * 2)
                else:
                    widest = widthX

                # Extreme top edge
                bottomCopperMax= padY / 2
                bottomPhysicalMax = lengthY / 2
                if bottomCopperMax > bottomPhysicalMax:    # Copper is bigger
                    tallest = padY
                else:
                    tallest = lengthY

                # Need to round so we stick to 0.01mm precision
                kicad_mod.append(RectLine(start=[round(0-widest/2-courtyardOffset, 2), round(0-tallest/2-courtyardOffset, 2)], end=[round(widest/2+courtyardOffset, 2), round(tallest/2+courtyardOffset, 2)], layer='F.CrtYd'))

                # create pads
                kicad_mod.append(Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                                    at=[0-padGap/2-padX/2, 0], size=[padX, padY], layers=Pad.LAYERS_SMT))
                kicad_mod.append(Pad(number=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                                    at=[padGap/2+padX/2, 0], size=[padX, padY], layers=Pad.LAYERS_SMT))

                # add model
                kicad_mod.append(Model(filename="${KICAD6_3DMODEL_DIR}/" + f"Inductor_SMD.3dshapes/{footprint_name}.wrl",
                                    at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

                # output kicad model
                file_handler = KicadFileHandler(kicad_mod)
                file_handler.writeFile(f'{outputPath}/{footprint_name}.kicad_mod')

