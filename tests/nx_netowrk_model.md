# NXNetowrkModel Tests

1. Test if network model behaves the same as a NXGraphmodel
   - except for the edge key:
   - it must throw errors, when the edge key is not a tuple specifying the
     connected inlets or edges
2. inlets outlets tests
   - either auto create outlets and inlets (like networkx autocreate nodes when
     edges are added)
   - or throw an error when the ports does not exist.
