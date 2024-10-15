class Data:
	def __init__(self, data):
		self._data = data
		self.dependents = set()

	@property
	def value(self):
		self.dependents.add(Effect.ctx.stack[-1])
		Effect.ctx.stack.append(self)
		result = self._data
		Effect.ctx.stack.pop()
		return result

	@value.setter
	def value(self, next_data):
		self._data = next_data
		self.push()

	def push(self):
		print(f"Data pushed {self._data}")
		for dep in self.dependents:
			dep.push()

from datetime import datetime
import asyncio

class Time:
	def __init__(self):
		self.dependents = set()

	@property
	def value(self):
		self.dependents.add(Effect.ctx.stack[-1])
		Effect.ctx.stack.append(self)
		result = datetime.now()
		Effect.ctx.stack.pop()
		return result

	async def start(self):
		while True:
			self.push()
			await asyncio.sleep(0)

	def push(self):
		for dep in self.dependents:
			dep.push()

class Deferre:
	def __init__(self):
		self.dependents = set()

	async def __call__(self, value):
		self.dependents.add(Effect.ctx.stack[-1])
		Effect.ctx.stack.append(self)
		result = value
		Effect.ctx.stack.pop()
		return result

class Computed:
	def __init__(self, fn):
		self._fn = fn
		self.dependents = set()

	@property
	def value(self):
		self.dependents.add(Effect.ctx.stack[-1])
		Effect.ctx.stack.append(self)
		result = self._fn()
		Effect.ctx.stack.pop()
		return result

	def push(self):
		print("Computed pushed")
		for dep in self.dependents:
			dep.push()
	

class Effect:
	ctx = None
	def __init__(self, fn):
		self.stack = []
		self._fn = fn

	def __call__(self):
		Effect.ctx = self
		self.stack = []
		self.stack.append(self)
		self._fn()
		self.stack.pop()
		print("Effect called")

	def push(self):
		print("Effect pushed")
		self.__call__()

if __name__ == "__main__":
	name = Data("Andris")
	style = Data("  Hello {}!")

	@Computed
	def greeting():
		return style.value.format(name.value)

	@Effect
	def print_result():
		print(greeting.value)


	print_result()

	name.value = "Judit"

