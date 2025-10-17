from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 

class PrimitiveElementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Primitive Elements")
        self.setMinimumSize(600, 400)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Define primitive elements to draw
        primitive_elements = {
            "PanelButtonCommand": QStyle.PrimitiveElement.PE_PanelButtonCommand,
            "PanelButtonBevel": QStyle.PrimitiveElement.PE_PanelButtonBevel,
            "PanelButtonTool": QStyle.PrimitiveElement.PE_PanelButtonTool,
            "PanelLineEdit": QStyle.PrimitiveElement.PE_PanelLineEdit,
            "PanelToolBar": QStyle.PrimitiveElement.PE_PanelToolBar,
            "PanelTipLabel": QStyle.PrimitiveElement.PE_PanelTipLabel,
            "PanelItemViewItem": QStyle.PrimitiveElement.PE_PanelItemViewItem,
            "PanelItemViewRow": QStyle.PrimitiveElement.PE_PanelItemViewRow,
            "PanelStatusBar": QStyle.PrimitiveElement.PE_PanelStatusBar,
            "PanelMenu": QStyle.PrimitiveElement.PE_PanelMenu,
            "PanelMenuBar": QStyle.PrimitiveElement.PE_PanelMenuBar,
            "PanelScrollAreaCorner": QStyle.PrimitiveElement.PE_PanelScrollAreaCorner,
            "FrameDefaultButton": QStyle.PrimitiveElement.PE_FrameDefaultButton,
            "FrameFocusRect": QStyle.PrimitiveElement.PE_FrameFocusRect,
            "Frame": QStyle.PrimitiveElement.PE_Frame,
            "FrameMenu": QStyle.PrimitiveElement.PE_FrameMenu,
            "FrameDockWidget": QStyle.PrimitiveElement.PE_FrameDockWidget,
            "FrameTabWidget": QStyle.PrimitiveElement.PE_FrameTabWidget,
            "FrameLineEdit": QStyle.PrimitiveElement.PE_FrameLineEdit,
            "FrameGroupBox": QStyle.PrimitiveElement.PE_FrameGroupBox,
            "FrameButtonBevel": QStyle.PrimitiveElement.PE_FrameButtonBevel,
            "FrameButtonTool": QStyle.PrimitiveElement.PE_FrameButtonTool,
            "FrameStatusBarItem": QStyle.PrimitiveElement.PE_FrameStatusBarItem,
            "FrameWindow": QStyle.PrimitiveElement.PE_FrameWindow,
            "FrameTabBarBase": QStyle.PrimitiveElement.PE_FrameTabBarBase,
            "Widget": QStyle.PrimitiveElement.PE_Widget,
            "CustomBase": QStyle.PrimitiveElement.PE_CustomBase,
            "IndicatorArrowUp": QStyle.PrimitiveElement.PE_IndicatorArrowUp,
            "IndicatorArrowDown": QStyle.PrimitiveElement.PE_IndicatorArrowDown,
            "IndicatorArrowRight": QStyle.PrimitiveElement.PE_IndicatorArrowRight,
            "IndicatorArrowLeft": QStyle.PrimitiveElement.PE_IndicatorArrowLeft,
            "IndicatorButtonDropDown": QStyle.PrimitiveElement.PE_IndicatorButtonDropDown,
            "IndicatorBranch": QStyle.PrimitiveElement.PE_IndicatorBranch,
            "IndicatorColumnViewArrow": QStyle.PrimitiveElement.PE_IndicatorColumnViewArrow,
            "IndicatorCheckBox": QStyle.PrimitiveElement.PE_IndicatorCheckBox,
            "IndicatorDockWidgetResizeHandle": QStyle.PrimitiveElement.PE_IndicatorDockWidgetResizeHandle,
            "IndicatorSpinUp": QStyle.PrimitiveElement.PE_IndicatorSpinUp,
            "IndicatorSpinDown": QStyle.PrimitiveElement.PE_IndicatorSpinDown,
            "IndicatorSpinPlus": QStyle.PrimitiveElement.PE_IndicatorSpinPlus,
            "IndicatorSpinMinus": QStyle.PrimitiveElement.PE_IndicatorSpinMinus,
            "IndicatorItemViewItemCheck": QStyle.PrimitiveElement.PE_IndicatorItemViewItemCheck,
            "IndicatorItemViewItemDrop": QStyle.PrimitiveElement.PE_IndicatorItemViewItemDrop,
            "IndicatorHeaderArrow": QStyle.PrimitiveElement.PE_IndicatorHeaderArrow,
            "IndicatorMenuCheckMark": QStyle.PrimitiveElement.PE_IndicatorMenuCheckMark,
            "IndicatorProgressChunk": QStyle.PrimitiveElement.PE_IndicatorProgressChunk,
            "IndicatorToolBarHandle": QStyle.PrimitiveElement.PE_IndicatorToolBarHandle,
            "IndicatorToolBarSeparator": QStyle.PrimitiveElement.PE_IndicatorToolBarSeparator,
            "IndicatorTabTear": QStyle.PrimitiveElement.PE_IndicatorTabTear,
            "IndicatorTabTearLeft": QStyle.PrimitiveElement.PE_IndicatorTabTearLeft,
            "IndicatorTabTearRight": QStyle.PrimitiveElement.PE_IndicatorTabTearRight,
            "IndicatorTabClose": QStyle.PrimitiveElement.PE_IndicatorTabClose,
            # QStyle.PrimitiveElement.PE_IndicatorRadioButton, THIS HAS BUGS
        }

        style = self.style()
        x, y = 10, 10
        width, height = 150, 50
        margin = 10

        # Iterate through the primitive elements and draw each one
        for name, pe in primitive_elements.items():
            ...
            rect = QRect(x, y, width, height)
            option = QStyleOption()  # Generic style option
            option.initFrom(self)
            option.rect = rect
            
            style.drawPrimitive(pe, option, painter, self)
            painter.drawText(rect.x(), rect.bottom(), f"{pe}. {name}")

            # Update positions for next element
            x += width + margin
            if x + width > self.width():
                x = 10
                y += height + margin

        painter.end()

class ControlElementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Elements")
        self.setMinimumSize(600, 400)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Define primitive elements to draw
        control_elements = {
            "PushButton": QStyle.ControlElement.CE_PushButton,
            "PushButtonBevel": QStyle.ControlElement.CE_PushButtonBevel,
            "PushButtonLabel": QStyle.ControlElement.CE_PushButtonLabel,
            "DockWidgetTitle": QStyle.ControlElement.CE_DockWidgetTitle,
            "Splitter": QStyle.ControlElement.CE_Splitter,
            "CheckBox": QStyle.ControlElement.CE_CheckBox,
            "CheckBoxLabel": QStyle.ControlElement.CE_CheckBoxLabel,
            "RadioButton": QStyle.ControlElement.CE_RadioButton,
            "RadioButtonLabel": QStyle.ControlElement.CE_RadioButtonLabel,
            "TabBarTab": QStyle.ControlElement.CE_TabBarTab,
            "TabBarTabShape": QStyle.ControlElement.CE_TabBarTabShape,
            "TabBarTabLabel": QStyle.ControlElement.CE_TabBarTabLabel,
            "ProgressBar": QStyle.ControlElement.CE_ProgressBar,
            "ProgressBarGroove": QStyle.ControlElement.CE_ProgressBarGroove,
            "ProgressBarContents": QStyle.ControlElement.CE_ProgressBarContents,
            "ProgressBarLabel": QStyle.ControlElement.CE_ProgressBarLabel,
            "ToolButtonLabel": QStyle.ControlElement.CE_ToolButtonLabel,
            "MenuBarItem": QStyle.ControlElement.CE_MenuBarItem,
            "MenuBarEmptyArea": QStyle.ControlElement.CE_MenuBarEmptyArea,
            "MenuItem": QStyle.ControlElement.CE_MenuItem,
            "MenuScroller": QStyle.ControlElement.CE_MenuScroller,
            "MenuTearoff": QStyle.ControlElement.CE_MenuTearoff,
            "MenuEmptyArea": QStyle.ControlElement.CE_MenuEmptyArea,
            "MenuHMargin": QStyle.ControlElement.CE_MenuHMargin,
            "MenuVMargin": QStyle.ControlElement.CE_MenuVMargin,
            "ToolBoxTab": QStyle.ControlElement.CE_ToolBoxTab,
            "SizeGrip": QStyle.ControlElement.CE_SizeGrip,
            "Header": QStyle.ControlElement.CE_Header,
            "HeaderSection": QStyle.ControlElement.CE_HeaderSection,
            "HeaderLabel": QStyle.ControlElement.CE_HeaderLabel,
            "ScrollBarAddLine": QStyle.ControlElement.CE_ScrollBarAddLine,
            "ScrollBarSubLine": QStyle.ControlElement.CE_ScrollBarSubLine,
            "ScrollBarAddPage": QStyle.ControlElement.CE_ScrollBarAddPage,
            "ScrollBarSubPage": QStyle.ControlElement.CE_ScrollBarSubPage,
            "ScrollBarSlider": QStyle.ControlElement.CE_ScrollBarSlider,
            "ScrollBarFirst": QStyle.ControlElement.CE_ScrollBarFirst,
            "ScrollBarLast": QStyle.ControlElement.CE_ScrollBarLast,
            "RubberBand": QStyle.ControlElement.CE_RubberBand,
            "FocusFrame": QStyle.ControlElement.CE_FocusFrame,
            "ItemViewItem": QStyle.ControlElement.CE_ItemViewItem,
            "CustomBase": QStyle.ControlElement.CE_CustomBase,
            "ComboBoxLabel": QStyle.ControlElement.CE_ComboBoxLabel,
            "ToolBar": QStyle.ControlElement.CE_ToolBar,
            "ToolBoxTabShape": QStyle.ControlElement.CE_ToolBoxTabShape,
            "ToolBoxTabLabel": QStyle.ControlElement.CE_ToolBoxTabLabel,
            "HeaderEmptyArea": QStyle.ControlElement.CE_HeaderEmptyArea,
            "ShapedFrame": QStyle.ControlElement.CE_ShapedFrame
        }

        style = self.style()
        x, y = 10, 10
        width, height = 150, 50
        margin = 10

        # Iterate through the primitive elements and draw each one
        for name, ce in control_elements.items():
            ...
            rect = QRect(x, y, width, height)
            option = QStyleOption()  # Generic style option
            option.initFrom(self)
            option.rect = rect
            
            style.drawControl(ce, option, painter, self)
            painter.drawText(rect.x(), rect.bottom(), f"{ce}. {name}")

            # Update positions for next element
            x += width + margin
            if x + width > self.width():
                x = 10
                y += height + margin

        painter.end()

class ComplexControlWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Complex Controls")
        self.setMinimumSize(600, 400)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Define primitive elements to draw
        complex_controls = {
            "SpinBox": QStyle.ComplexControl.CC_SpinBox,
            "ComboBox": QStyle.ComplexControl.CC_ComboBox,
            "ScrollBar": QStyle.ComplexControl.CC_ScrollBar,
            "Slider": QStyle.ComplexControl.CC_Slider,
            "ToolButton": QStyle.ComplexControl.CC_ToolButton,
            "TitleBar": QStyle.ComplexControl.CC_TitleBar,
            "GroupBox": QStyle.ComplexControl.CC_GroupBox,
            "Dial": QStyle.ComplexControl.CC_Dial,
            "MdiControls": QStyle.ComplexControl.CC_MdiControls,
            "CustomBase": QStyle.ComplexControl.CC_CustomBase,
        }

        style = self.style()
        x, y = 10, 10
        width, height = 150, 50
        margin = 10

        # Iterate through the primitive elements and draw each one
        for name, cc in complex_controls.items():
            ...
            rect = QRect(x, y, width, height)
            option = QStyleOptionComplex()  # Generic style option
            option.initFrom(self)
            option.rect = rect
            
            style.drawComplexControl(cc, option, painter, self)
            painter.drawText(rect.x(), rect.bottom(), f"{cc}. {name}")

            # Update positions for next element
            x += width + margin
            if x + width > self.width():
                x = 10
                y += height + margin

        painter.end()


if __name__ == "__main__":
    app = QApplication([])

    # pe_widget = PrimitiveElementWidget()
    # pe_widget.show()
    ce_widget = ControlElementWidget()
    ce_widget.show()
    # cc_widget = ComplexControlWidget()
    # cc_widget.show()

    app.exec()
