from PySide6.QtWidgets import QLabel

class TriggerInPort:
	def __init__(self, name):
		self.callbacks = []
		self.name = name

	def on_trigger(self, callback):
		self.callbacks.append(callback)

	def run_callbacks(self, props=None):
		for callback in self.callbacks:
			callback(props)

class TriggerOutPort:
	def __init__(self, name):
		self.targets = []
		self.name = name

	def connect(self, target:TriggerInPort):
		self.targets.append(target)

	def trigger(self, value=None):
		for target in self.targets:
			target.run_callbacks(value)

class Node:
	def __init__(self, window):
		self.in_ports = []
		self.out_ports = []

	def on_destroy(self, callback):
		self.destroy_callbacks.append(callback)

	def destroy(self):
		pass

	def __del__(self):
		try:
			self.destroy()
		except Exception as err:
			pass


	def triggerIn(self, name):
		port = TriggerInPort(name)
		self.in_ports.append(port)
		return port

	def triggerOut(self, name):
		port = TriggerOutPort(name)
		self.out_ports.append(port)
		return port

	def add_in_port(self, name):
		self.in_ports.append(InPort(name))
