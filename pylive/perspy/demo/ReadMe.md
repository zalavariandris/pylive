# Camera Spy Demo Application

## TODO
- parameters:
  - [x] if no image is loaded, allow setting image size
  - [x] open image button,
  - [x] show the image size
  - [x] dim background image

- [x] show horizon line
- [ ] show real world size units
- [ ] add a tape measure on the grid floor? or on a specific axis?

- [?] landing page. when no image is loaded, show instructions to load an image.
- [x] disable docking

- [x] allow setting the image size, and let user place control points freely.
      => allow setting the image size, and play with the vanishing lines
  
- [x] quad controls for TwoVP solver

- [x] the blue controls are not saturated enough against dark background
      => added some green to the blue and a little to the red as well. these colors now a lot more pleasant on the dark background.

THEMING
- [x] adjusted style for windows dark mode.
      force window title bar to darkmmode on windows. (note: blender on windows seem to force the dark mode titlebar, that fits its own colorscheme)
- [x] adjust style for osx, potentially force dark mode for native window.
      =>set the titlebar color myself. 
      - [ ] consider setting the theme a little lighter to match the native titlebar color?
- [ ] linux?

- [x] about menu with links to github, author info

- [ ] camera sensor settings
  - presets
  - custom size
  - by default field of view is used to compute focal length.
    if sensor size is set, use that to compute focal length instead of fov.
    by default the sensor size is 36x24mm (full frame)

- results panel
  - [x] include quaternion values
  - [x] allow specifying rotation order for euler angles

- [ ] save and load project

- [-] export
  - [ ] export to json
  - [ ] copy to clipboard json
  - [ ] copy to clipboard for destination app,  (if pasting to destination is even possible, or create a script for them?)
        - AE
        - blender
        - max
        - houdini
        - nuke?
  - [ ] consider other formats: yaml, fspy.
  - [ ] consider creating destination specific applications: blender? after? Maya, Max, houdini nuke?
  - [ ] consider additional data like sensor size, vanishing points, computed vanishing points, sensor size based focal length etc.


- [ ] consider a log window to show messages
- [ ] also show error in results window if camera cant be solved...
- [x] allow emojis! :)

## Code Quality
- [ ] simplify variable names. 
      eg _pixels unit does not needed anymore.
      consider using vp1 instead of first_vanishing_point_pixel, etc.
- [ ] clenup hello_imgui mess and potentially move it into a wrapper function.
- [ ] cleanup font loading with FA and emojis. it is a mess now.
- [ ] consider writing a helper run-like function without using hello_imgui. (this coul be more problematic eg: dpi awarness, docking options, etc...)

- [ ] COLLECT TODOS from Code Comments, and consider fixing or dropping them.

## BUGS
- [ ] review axis settings (currently twoVP mode, seem to be flipped on Y)
- [ ] when opening a combo box, the selectable items are in an awkward position.
- [ ] combo popup is a little off. might be dpi scaling, or font. investigate later.

## Solver
- [ ] documentation

