from typing import *
class Pipe(object):
    def __init__(self, data:Any):
        self.data:Any = data
    def __or__(self, fn:Callable):
        return Pipe( fn(self.data) )
        # self.data = 
        # return self.data
    # def __ror__(self, other):
    #     return Infix(partial(self.func, other))
    def __call__(self):
        return self.data
    
    def __str__(self):
        return f"|> {str(self.data)}"
    

def square(x):
    return x*x

result = Pipe(5) | square | square

print(result)

