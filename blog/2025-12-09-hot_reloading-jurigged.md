*Jurigged* is a hot reloader library, that is able to reload python odules, while running.
https://github.com/breuleux/jurigged

note: the github page also mention *reloading* library. we will take a closer look at that as well later. https://github.com/julvo/reloading

## Emojis, accented letters. How to enable UTF-8 encoding
by default jurigged reloading does not support uft-8
to enable, set the environment variable right before starting jurigged.
```$env:PYTHONUTF8 = "1"; python -m jurigged main.py```