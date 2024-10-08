from definitions import TickNode, PrintNode

tickNode = TickNode(window)
printNode = PrintNode(window)
tickNode.tickPort.connect(printNode.input_port)

