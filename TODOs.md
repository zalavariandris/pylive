# TODO

## livescript
- [x] add restart button
- Show errors inline in the script editor.
- refactor QCompleters, to use eventFilter. So they can be used with any QTextEdit like MyCompleter(textedit)
- handle inconsisten spacing
- show tabs spaces, and convert between indentation style.

- cleanup dangling object when executed.
  on error, object will stuck in memory easaly using exec with python, since we are not restarting the interpeter
  - specifically cleanup dangling QObjects.
- find bugs before executing, with tools like pyrope, pythons Abstract Syntax Trees, etc.
- Add GarbageCollector widget

- TEST, TEST...