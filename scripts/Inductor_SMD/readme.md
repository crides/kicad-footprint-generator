# gen_inductor.py
## Usage
`python gen_inductor.py <inputfile.yaml> <outputPath>`

## Intent
The goal was to easily copy and paste datasheet information for inductor series to generate the
appropriate footprints. In the specific case, Sunlord has a certain format (describe in CSV section below)
that did not suit the existing Inductor_SMD script format.

The workflow that has worked well for me is as follows
1. Use Foxit PDF to copy the specifications table.
1. Paste this in the spreadsheet editor of your choice
1. Delete the columns which aren't required
1. Rename the headers and perform any other editing or grouping required
1. Export to CSV format

## YAML input file
The yaml file is used to define all the generic series inputs.
It will have an entries for the CSV for that specific series which will actually hold the footprint measurements. You can see the included YAML file for the format.


## CSV input files
The CSV format requires the following 6 columns, which can be in any order in the actual CSV file.


`PartNumber` - Part number that will be generated. This could be the unique part number,
or you can perform grouping if there are multiple parts sharing the same footprint.

`lengthY` and `widthX` - physical dimensions of the inductor

`padX` and `padY` - the center of the pad

`padGap` - the gap between the copper pads (NOT center to center)

**Note** - you may need to swap the `length`/`width` values, and thus the `pad x`/`pad y` values.
The `lengthY` value should be the dimension/edge that shares the same side as the copper pads.

### Example
![Layout Example](layout1.png)

In this example from the SWPA series, the recommended land pattern is in the proper orientation (pads on the left/right) for this script.

- `b` becomes `padX`
- `c` is `padY`
- `a` is `pad gap`.

In this datasheet, care must be taken to adjust the physical dimensions. `A` becomes `widthX` and `B` becomes `lengthY`,
since the land pattern is rotated to differ from the physical drawings.

