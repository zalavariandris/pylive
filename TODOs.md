# TODO

- JediCompleter: FIX not compatible with QLineEdit
- ScriptEdit: Move Script Edito behaviour to its own class

## livescript

- [x] add restart button
- Show errors inline in the script editor.
- refactor QCompleters, to use eventFilter. So they can be used with
  any QTextEdit like MyCompleter(textedit)
- handle inconsisten spacing
- show tabs spaces, and convert between indentation style.

- cleanup dangling object when executed.
  on error, object will stuck in memory easaly using exec with python,
  since we are not restarting the interpeter
  (Especially cleanup dangling QObjects.)
- find bugs before executing, with tools like pyrope,
  pythons Abstract Syntax Trees, etc.
- Add GarbageCollector widget

- TEST, TEST...


## Known hickups
- [] multiline string does not highlight properly
  - fix: https://forum.qt.io/topic/146348/how-to-highlight-multiline-text-on-a-qtextedit/5
- [] RopeCompleter, will replace the "WordUnderCursor", instead of using the
  startingoffset, and offset positions...
  - Fix: We need to update the QCompleter's model from a simple StringListModel
  to something that is able to hold these offsets, and call `insertCompletion`
  with these values as well.

- [x] livescript silently reloads a file from disc if it was changed externally.
  This behaviour is intended, but the cursor will jump to the begining of
  the file. Try to keep the cursor in place!
