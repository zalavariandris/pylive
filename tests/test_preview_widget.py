from pylive.preview_widget import PreviewWidget, SingletonException

import unittest

class TestPreviewWidget(unittest.TestCase):
	def test_create_with_instance(self):
		widget = PreviewWidget.instance()
		
	def test_throw_using_init(self):
		self.assertRaises(SingletonException, PreviewWidget)

if __name__ == "__main__":
	unittest.main()