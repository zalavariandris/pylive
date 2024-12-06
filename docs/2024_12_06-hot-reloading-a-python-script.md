# hot reloading a python script

With pylive, we have a clear goal. Whenever the code changes, i want it to reflect on the currenty running python application.
The application will allways be live!

Python is super flexible. Most impreative languages are. To hotreload functions, or classes would mean to fix an airplaine in the air. Its extremely dangerous. eg updateng a class, will also means we need to swap all its instances to the new Object...

If a change one part of a codebase, we either need to swap the while airplaine. Restart the application or we need to know precisely what needs to be replaced in the currenlty running code. The first approach is trivial but slow and cannot tap into the current state of the applicatin. The second is less than trivial.

What is missing, is a clear way to define the current state of the app, and a dependency graph.
Instead of deriving that graph from the source code, for now we will define it ourselves. (later wi will experience to derive a state from the running app, and see if we can get a dependency grap of the application from the source code.) This is where the GraphEditor comes into the game.

We will define computational nodes and their dependencies.
These nodes will run python code. But that code will have restriction, therefore understanding, the flow of the app will be a lot easier.

first we will need a GUI, to describe the application flow ourselves.
