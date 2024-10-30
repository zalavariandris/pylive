# Interactively Executing Scripts with Python

Now that we have the basic UI blocks for the interactive node based coding
with python, we will explore the possible implamentations to connect and
run python scripts or statements.

There are several ways to run arbitrary code within python.
we will explore each option to see how they behave and expore them.

For example we can simply run a **python script** file with a **subprocess**.
```python
subprocess.run(["python", "path/to/script.py"])
```
by using subprocesses, it would alse be possible to use any executable,
no matter what language it was written.

It is also possible to run a **python command** with **subprocess**:
```python
subprocess.run(["python", "-c", "print('hello')"])
```
we can use `eval` to **evaluate expressions**
```python
eval(expression, globals, locals)
```

and of course use `exec`
```python
exec(script, globals, locals)
```

If we are using `compile` and `exec`, then its possible to set different modes
```python
mode = "exec" # this can be 'eval', 'exec' and 'single'
compiled_code = compile(script, "<script>", 'mode')
exec(compiled_code, globals, locals)
```

this is from the python documentation:
> The mode argument specifies what kind of code must be compiled; it can be
  'exec' if source consists of a sequence of statements, 'eval' if it consists
  of a single expression, or 'single' if it consists of a single interactive
  statement (in the latter case, expression statements that evaluate
  to something other than None will be printed).
> 
  https://docs.python.org/3/library/functions.html#compile

And dont forget **IPython**: the IPython shell and the **jupyter notebook**.
Jupyter notebook is already a great interactive environment for
python (and even other languages). The notebook has a linear execution order,
from top to bottom. What if we could organize the cells into a graph,
and keep track of the cells dependancies?

## using exec
Lets start with the most obvious: `exec`.
`exec` is able to run arbitrary code from a string
But I run into a weird behaviour.
if you run the folowing code it will throw an error:
`NameError: name 'time' is not defined. Did you forget to import 'time'?`
I am not entirely sure why.

```python
script = """
import time

def get_current_time():
	return time.time()
	
get_current_time()
"""

def main():
	exec(script)

main()
```

If we simply call exec like `exec(script, globals())`, then it will behave
as expected. (at least to my expectations), and run without an error.
In case you would like to append names to the locals we can stil capture the
locals at the begining of our script. (That is probalby a default locals
dictionary, that seem to define the script behaiour), and pass that
to the exec function.

```python
local_vars = locals()

script = """
import time

def get_current_time():
	return time.time()
	
get_current_time()
"""

def main():
	exec(script, globals(), local_vars)

main()
```

let's see what inside that magical locals() at the begining of our script.

```python
for key, item in list(locals().items()):
	print(f"{key}: {item}")
```

```python
__name__: __main__
__doc__: None
__package__: None
__loader__: <_frozen_importlib_external.SourceFileLoader object at 0x00000235D5805AC0>
__spec__: None
__annotations__: {}
__builtins__: <module 'builtins' (built-in)>
__file__: C:\dev\src\pylive\expreiments\test_exec_scope.py
__cached__: None
```

For the record creating a new dictionary will throw a `NameError`.

```python
local_vars = locals()

script = """
import time

def get_current_time():
	return time.time()
	
get_current_time()
"""

def main():
	exec_locals = {key:value for key, value in list(locals().items())}
	exec(script, globals(), exec_locals)

main()
```

For now it seem like using the exec by passing `globals()` only could be
suitalbe to run blocks of code.

## locals at the first line
locals() actually returns the same stuff when called at a global scope,
that globals does()
therefore it alsa possible to call `exec(script, globals(), globals())`
and of course
```python
script = """
import time

def get_current_time():
	return time.time()
	
get_current_time()
"""

def main():
	local_vars = globals()
	exec(script, globals(), local_vars)

main()
```

### passing data
Now lets see how to pass data to the exec local scope.
Well, now its seem quite straightforward, and it works like a charm.

```python
script = """
import time

def get_current_time():
	print(my_variable)
	return time.time()
	
print( get_current_time() )
"""

def main():
	my_variable = 5
	local_vars = globals()
	local_vars["my_variable"] = my_variable
	exec(script, globals(), local_vars)

main()
```

The only issue here is that we also keep populating the globals scope.
And get_current_time is alsa available outside of the exec script.
Also locals and globals become the same dictionary, not a copy, therefore
there will be no differences between the global and the local scopes, at least inside our executed scripts. And that probably can lead to serious issues.

for the record as a wrote before copying the global and local scopes
will throw a NameError:



The thing is, that the `import time` statement happens in the local scope
of the main function.
if we define time as a global name that it works again:

```python
script = """
import time
global time

def get_current_time():
	return time.time()
	
print( get_current_time() )
"""

def main():
	exec(script)
main()
```

but that look awkward.

We could preprocess the script text and replace top-level imports to work on the
global scope. For example by using the `importlib.import_module`.
There are a few solutions to import modules globally on stackoverflow
The one with a context manager feels like a possible solution:
<https://stackoverflow.com/questions/11990556/how-to-make-global-imports-from-a-function>
