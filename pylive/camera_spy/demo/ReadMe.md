# Camera Spy Demo Application

## TODO
- parameters:
  - [x] if no image is loaded, allow setting image size
  - [x] open image button,
  - [x] show the image size
  - [x] dim background image

- [x] show horizon line
- [ ] show real world size units

- [?] landing page. when no image is loaded, show instructions to load an image.
- [ ] disable docking

- [x] allow setting the image size, and let user place control points freely.
      => allow setting the image size, and play with the vanishing lines
  
- [x] quad controls for TwoVP solver

- [x] the blue controls are not saturated enough against dark background
      => added some green to the blue and a little to the red as well. these colors now a lot more pleasant on the dark background.

- [ ] simplify variable names. 
      eg _pixels unit does not needed anymore.
      consider using vp1 instead of first_vanishing_point_pixel, etc.


- [ ] "help?" menu
- [ ] about menu with links to github, author info

- camera sensor size?
  - presets
  - custom size
  - by default field of view is used to compute focal length.
    if sensor size is set, use that to compute focal length instead of fov.
    by default the sensor size is 36x24mm (full frame)

- results panel
  - [x] include quaternion values
  - [ ] allow specifying rotation order for euler angles

- [ ] export
  - [ ] copy to clipboard (if pasting to destination is possible)
  - [ ] save to file (json yaml, if possible create destination specific format)
  - [ ] formats: json, yaml, fspy. Applications: blender? after? Maya, Max, houdini nuke?

- [ ] consider a log window to show messages
- [ ] also show error in results window if camera cant be solved...
- [ ] allow emojis! :)

- [ ] COLLECT TODOS from Code Comments, and consider fixing or dropping them.

## BUGS
- [ ] review axis settings (currently twoVP mode, seem to be flipped on Y)
- [ ] when opening a combo box, the selectable items are in an awkward position.

## Solver
- [ ] documentation

