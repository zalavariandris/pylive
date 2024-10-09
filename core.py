from PySide6.QtWidgets import QLabel

import weakref
class TriggerInPort:
	def __init__(self, name):
		self.callbacks = set()
		self.name = name

	def destroy(self):
		self.callbacks = []

	def on_trigger(self, callback):
		self.callbacks.add(callback)

	def run_callbacks(self, props=None):
		for callback in self.callbacks:
			callback(props)


class TriggerOutPort:
    def __init__(self, name):
        self.targets = set()
        self.name = name
        self.listeners = []  # List of subscribed callback functions

    def trigger(self, value=None):
        # Iterate over the listeners and invoke each callback
        for listener in self.listeners:
            listener(value)

    def subscribe(self, callback):
        # Add a callback to the list of listeners
        self.listeners.append(callback)

    def destroy(self):
        # Clear the listeners list when destroying
        self.listeners = []

    def __del__(self):
    	self.destroy()


class Node:
	def __init__(self):
		self.in_ports = dict()
		self.out_ports = dict()
		self.events = dict({
			"on_destroy": []
		})

	def event(self, fn):
		self.events[fn.__name__].append(fn)

	def destroy(self):
		for callback in self.events["on_destroy"]:
			callback()

		for name, in_port in self.in_ports.items():
			in_port.destroy()

		for name, out_port in self.out_ports.items():
			out_port.destroy()

	def __del__(self):
		self.destroy()

	def triggerIn(self, name):
		port = TriggerInPort(name)
		self.in_ports[name] = port
		return port

	def triggerOut(self, name):
		port = TriggerOutPort(name)
		self.out_ports[name] = port
		return port

