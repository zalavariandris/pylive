from PySide6.QtCore import QTimer

def main(node, container):
	print("main evaluate")
	from PySide6.QtCore import QTimer
	output = node.triggerOut("output")

	k = 0
	def tick():
		nonlocal k, output
		output.trigger(k)
		k+=1

	timer = QTimer(container)
	timer.timeout.connect(tick)
	timer.start(1000/60)

	@node.event
	def on_destroy():
		nonlocal timer
		timer.stop()
