# Camera Spy Demo Application

## Feature TODOs
- IO
  - [x] save and load project
      - [ ] consider saving additional information like results(camera, vanishing points); camera sensor size, and focal length
  - [ ] import
  - [ ] export results
    - [ ] export results to json
    - [ ] copy to clipboard json
    - [ ] consider other formats: yaml.
    - [ ] fspy import export
    - [ ] AE: export to jsx
    - [ ] blender export to script, or import plugin from .prpy 
    - [ ] max: export to .ms or .py
    - [ ] houdini?
    - [ ] nuke: copy to clipboard, export to .nk

- [ ] instead of crashing, show error messages when actions fail
- [ ] review try except, logging, printing messages, consider using errorr popups and log window

- landing page.
  - [?] when no image is loaded, show instructions to load an image.
  - [x] allow setting the image size, and let user place control points freely.
        => allow setting the image size, and play with the vanishing lines

- about menu
  - [ ] with links to github, author info

- parameters panel:
  - [x] if no image is loaded, allow setting image size
  - [x] open image button,
  - [x] show the image size
  - [x] dim background image
  - [ ] camera sensor settings
    - presets
    - custom size
    - by default field of view is used to compute focal length.
      if sensor size is set, use that to compute focal length instead of fov.
      by default the sensor size is 36x24mm (full frame)

- results panel
  - [x] include quaternion values
  - [x] allow specifying rotation order for euler angles
  - [x] also show error in results window if camera cant be solved...

- logging
  - [ ] consider a log window to show messages

- Viewer
  - guides
  - [x] show horizon line
  - [ ] show real world size units
  - [ ] add a tape measure on the grid floor? or on a specific axis?

- UI/UX
  - [x] disable docking
  - [x] show windows menu
  - [x] quad controls option for TwoVP solver
  - [x] the blue controls are not saturated enough against dark background
        => added some green to the blue and a little to the red as well. these colors now a lot more pleasant on the dark background.
  - [-] allow emojis! :)
  - [-] fontawesome icons?
  
- [ ] consider implementing document is modified query for the Document.
      since with imgui, we update the state every frame this might not be easy.

- COLOR STYLE
- [x] adjusted style for windows dark mode.
      force window title bar to darkmmode on windows. (note: blender on windows seem to force the dark mode titlebar, that fits its own colorscheme)
- [x] adjust style for osx, potentially force dark mode for native window.
      =>set the titlebar color myself. 
      - [ ] consider setting the theme a little lighter to match the native titlebar color?
- [ ] linux?


## Code Quality
- [ ] CREATE TESTS!
- [x] now viewport using its own get_viewer_style. therefore 'colors.py' could be removed.
- [ ] review module structure, eg: Solver enums or App Enums; imports and __init__ files...
- [ ] simplify variable names. 
      eg _pixels unit does not needed anymore.
      consider using vp1 instead of first_vanishing_point_pixel, etc.

- [ ] cleanup font loading with FA and emojis. it is a mess now.

- [x] clenup hello_imgui mess.
- [ ] consider a custom hello_imgui based runner function. or a class.
- [ ] consider rolling my own helper run-like function without using hello_imgui. (this couldbe more problematic eg: dpi awarness, docking options, etc...)
- [ ] COLLECT TODOS from Code Comments, and consider fixing or dropping them.
- [ ] consider subclassing ValueError to specific solver errors. SolverError->FocalLengthError, VanishingPointError, GeometryError, AxisMappingError

## BUGS
- [ ] review axis settings (currently twoVP mode, seem to be flipped on Y)
- [ ] when opening a combo box, the selectable items are in an awkward position.
- [ ] combo popup is a little off. might be dpi scaling, or font. investigate later.

## Solver
- [ ] documentation

