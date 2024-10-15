class BatchContext:
	# Tracks whether we're in a batch operation
	active = False
	queued_pushes = set()

	@classmethod
	def start(cls):
		cls.active = True
		cls.queued_pushes.clear()

	@classmethod
	def stop(cls):
		cls.active = False
		# Trigger all queued pushes at the end of the batch
		for dep in cls.queued_pushes:
			dep.push()
		cls.queued_pushes.clear()

	@classmethod
	def queue_push(cls, dep):
		# Queue the push for when the batch completes
		cls.queued_pushes.add(dep)


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
		if BatchContext.active:
			BatchContext.queue_push(self)
		else:
			print(f"Data pushed {self._data}")
			for dep in self.dependents:
				dep.push()


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
		if BatchContext.active:
			BatchContext.queue_push(self)
		else:
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
		if BatchContext.active:
			BatchContext.queue_push(self)
		else:
			print("Effect pushed")
			self.__call__()


def batch():
	"""
	Context manager to perform batched updates.
	"""
	class BatchContextManager:
		def __enter__(self):
			BatchContext.start()

		def __exit__(self, exc_type, exc_value, traceback):
			BatchContext.stop()

	return BatchContextManager()


# Test the batch functionality

name = Data("Andris")
style = Data("  Hello {}!")

@Computed
def greeting():
	return style.value.format(name.value)

@Effect
def print_result():
	print(greeting.value)


print_result()

# Perform batched updates
with batch():
	style.value = "  Hey {}!"
	name.value = "Judit"
