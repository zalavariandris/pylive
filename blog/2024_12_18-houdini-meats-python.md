# Houdini meats python adn colour-science

In the last few years (actually since my first look on 3d code and node based applications) I was looking for tools where code and node based UI are friends. The real reason i love node based workflows, is not because of the nodes themselfes but the reason they are live!

there are plenty nodebased tools out there like maxmsp, puredata, vvvv, nodes.io also came along nowdays.
But they always felt a bit like a toy.

Houdini on the other hand is a professional CGI application. That is capable of creating pretty complex CGI. But its main strength is not simply the procedural approach, but how deeply procedural it is.
The problem with Houdini, and actually all the tools mentioned is they all meant for a special pourpose.

That is where python comes in. The main strength usually python is mentioned is for its ease of the its syntax.
- by the way i really miss real anonymous functions from python, its such a powerfool tool in javascript. And naming is one of the hardest part in programming.

aside from the missing real anonymous functions
And ther is python. Usually the


# useful snippets
create numpy array from geometry attriubte
```python
attr_array = np.frombuffer(
	geo.pointFloatAttribValuesAsString(
		"attribute_name", 
		dtype=np.float32
	) #optionally reshape to the attribute dimensions.reshape(-1,3)
```

set points attribute from a numpy array
```python
setPointFloatAttribValuesFromString(
	"attribute_name", values, 
	float_type=hou.numericData.Float32
)
```

lets se an example

# surface the visible gammut
https://horizon-lab.org/colorvis/chromaticity.html
https://stackoverflow.com/questions/48390558/how-is-the-visible-gamut-bounded