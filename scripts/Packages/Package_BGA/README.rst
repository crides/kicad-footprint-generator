BGA / CSP Footprint Generator Usage
===================================

This footprint generator can be used to generate footprints with rectangular pin grids for BGAs, CSPs and similar
packages.


Running the script
------------------

The generator script is invoked with a yaml file with package definitions as a command line argument, and produces a
Kicad footprint library with the corresponding footprints. It requires at least python 3.8 to run. Invoke it like so:

.. code-block:: shell

    $ python ipc_bga_generator.py bga.yml

This will write the generated footprint library to a folder named ``Package_BGA.pretty``.

Package definition
------------------

The YAML file contains a list of packages definitions to export. For example, the following definition describes a
625-pin BGA, with outside dimensions 21mm x 21mm, and ball pitch 0.8mm. The Kicad footprint identifier of the generated
footprint will be ``BGA-625_21.0x21.0mm_Layout25x25_P0.8mm``.

.. code-block:: yaml

    BGA-625_21.0x21.0mm_Layout25x25_P0.8mm:
      description: "BGA-624"
      size_source: "https://www.nxp.com/docs/en/package-information/SOT1529-1.pdf"
      body_size_x: 21.0
      body_size_y: 21.0
      pitch: 0.8
      pad_diameter: 0.4
      mask_margin: 0.0625
      layout_x: 25
      layout_y: 25

Mandatory parameters
~~~~~~~~~~~~~~~~~~~~

The following parameters are mandatory, and must be in every package definition:

``description``
    Contains a brief, human-readable description of the package.

``size_source``
    Contains a link to a datasheet or mechanical drawing that defines the package's dimensions. 

``body_size_{x,y}``
    Defines the outside dimensions of the package. This is the dimensions of the actual package. Silkscreen and other
    graphical features are automatically generated from this using configurable offsets.

``pitch|pitch_{x,y}``
    Defines the pin pitch in mm. Either one ``pitch`` must be given, which is then used for both X and Y pitch, or
    separate ``pitch_{x,y}`` can be given.

``pad_diameter|ball_{type,diameter}``
    Either ``pad_diameter`` must be given, or ``ball_type`` and ``ball_diameter`` must be given.

    ``pad_diameter`` defines the diameter of the pad in mm. The actual sizes of the pad and soldermask opening are
    generated from this. This should be used for manufacturer-specific footprints that have their pad sizes hardcoded
    into their drawings.

    ``ball_{type,diameter}`` define ball type and diameter according to IPC-7351B. The values given here will be looked
    up in the land definition config and used for the pad dimensions. The default land definition config can be found in
    ``ipc_7351b_bga_land_patterns.yaml``.

``layout_{x,y}``
    Defines the number of pins in X and Y direction.

Optional parameters
~~~~~~~~~~~~~~~~~~~

In addition to the above, package definitions can use the following, optional parameters.

``additional_tags``
    Contains a string with a list of Kicad footprint tags that are added to the generated footprint.

``mask_margin``
    Solder mask margin to be stored in the footprint. Defaults to whatever the user sets in the board options.

``paste_margin``
    Paste margin to be stored in the footprint. Defaults to whatever the user sets in the board options.

``paste_ratio``
    Paste ratio to be stored in the footprint. Defaults to whatever the user sets in the board options.

``row_names``
    Contains a list with names to be used instead of the default IPC row names ('A', 'B', 'C', ..., 'AA', 'AB', ...)

``row_skips``
    Defines pads to omit from the generated footprint. The value of this is a list with one element per row. Each
    element is itself another list. Inside this nested list can be either integers defining pad numbers (according to
    the footprint, so starting at 1), or two-tuples of ``[start, end]`` format that describe ranges. For instance, to
    omit pins B3, B5, B6 and B7, the following could be used: ``row_skips: [[], [3,[5,7]]]``

``area_skips``
    Contains a list of four-tuples, each defining a rectangular area of pins to omit from  the generated footprint. Each
    area is given as ``[top_left_row, top_left_column, bottom_right_row, bottom_right_column]``. For example, to omit
    all pins in the rectangular area between pins B2 and J9, use: ``area_skips: [[B, 2, J, 9]]``. Note that multiple
    area skips can be defined.

``pad_skips``
    Contains a list of pad names of pads that are omitted in the generated footprint. For instance, to omit pads A1, B17
    and J3, use: ``pad_skips: [A1, B17, J3]``.

``staggered``
    This option enables the generation of a staggered ball layout, where every second row or column is shifted by
    one-half pitch. Valid values are ``x`` and ``y``, where ``x`` produces a layout with staggered rows and ``y``
    produces one with staggered columns. Staggered ball layouts usually space rows (or columns) so that every three
    adjacent balls form an equilateral triangle. When ``staggered`` and ``pitch`` are given, the pitch gives the side
    length of that triangle, and its height that is used for row (or column) spacing is calculated automatically. You
    can override this by manually giving both ``pitch_x`` and ``pitch_y``.

``first_ball``
    This option is used together with ``staggered`` to define staggered layouts. It expresses that every second pad
    should be omitted in a checkerboard pattern. The value of this parameter is the first (top left) pin to be generated
    and can be one of A1, B1, or A2. B1 and A2 produce the same result.

``offset_{x,y}``
    These values define an offset (in mm) that shifts the generated pad grid relative to the chip's package. Negative
    values shift the pad positions top and left.

``pad_shape``
    This value sets the pad shape and can be one of ``circle``, ``rect`` or ``roundrect``. Defaults to ``circle``.

Staggered pad layouts
~~~~~~~~~~~~~~~~~~~~~

Some CSPs use staggered layouts, where every second row is offset horizontally by one half of the pin pitch. Usually,
the pins are arranged in a triangular grid, with any three adjacent pins forming an equilateral triangle. Layouts like
these can be expressed in footprint definitions using the ``staggered`` and ``first_ball`` parameters.

Here is an example of a footprint definition using staggered pins:

.. code-block:: yaml

    ST_WLCSP-115_4.63x4.15mm_P0.4mm_Stagger:
      description: "ST WLCSP-115, ST die ID 461"
      size_source: "https://www.st.com/resource/en/datasheet/stm32l496wg.pdf"
      body_size_x: 4.63
      body_size_y: 4.15
      pitch: 0.4
      staggered: x
      first_ball: A2
      pad_diameter: 0.225
      mask_margin: 0.0325
      paste_margin: 0.0125
      layout_x: 21
      layout_y: 11

Nested or multi-pitch pad layouts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some chips have pad patterns that consist of multiple areas that may have different pin pitch and offsets. One example
for this are BGAs that have a low-density array with a large pitch in the middle surrounded by a higher-density ring of
pads using a finer pitch on the outside.

The generator supports these cases through the ``secondary_layouts`` parameter. The value of this parameter is a list of
layout definitions, each of which will be added to the footprint in addition to the layout defined on the part itself as
usual. For instance, the following definition describes a BGA that has an area with pitch 0.65mm in the middle
surrounded by three rows of pads at pitch 0.5mm on the outside. To make space for the inner coarse grid, ``area_skips``
is used.

.. code-block:: yaml

    TFBGA-257_10x10mm_Layout19x19_P0.5mmP0.65mm:
      description: "TFBGA-257"
      size_source: "https://www.st.com/resource/en/datasheet/stm32mp151a.pdf"
      body_size_x: 10.0
      body_size_y: 10.0
      pitch: 0.5
      pad_diameter: 0.230
      mask_margin: 0.050
      layout_x: 19
      layout_y: 19
      pad_skips: [
        a5,a8,a11,a14,
        f1,j1,m1,r1,
        e19,h19,l19,p19,
        w6,w9,w12,w15
      ]
      area_skips:
        - [d,4,t,16] # Remove middle of outer 0.5mm grid to make room for inner 0.65mm grid
      secondary_layouts:
        - pitch: 0.65
          layout_x: 9
          layout_y: 9
          row_names: [1A, 1B, 1C, 1D, 1E, 1F, 1G, 1H, 1J]

Note that multiple nested grids can be defined. ``secondary_layouts`` takes a YAML list, each item of which defines one
additional grid. In the above example, the dash ``-`` on the first line under ``secondary_layouts`` starts a new item in
that list.

Each layout definition in ``secondary_layouts`` must define at least ``pitch|pitch_{x,y}``, ``layout_{x,y}`` and
``row_names``. Skips are supported like in top-level layouts, and ``pad_shape`` and ``pad_size`` can be given to
override values from the top-level footprint definition.

