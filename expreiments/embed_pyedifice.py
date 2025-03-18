import asyncio

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qasync import QEventLoop

import edifice as ed


@ed.component
def CompoundComponent(self, props:dict):
    with ed.VBoxView():
        if props['error']:
            ed.Label("Error: \n" + str(props['error']))
        else:
            ed.Slider(props['x'])


@ed.component
def ExportComponent(self, component, controller):
    state, state_setter = ed.use_state( {'error': None, 'x':0} )
    def setup():
        controller['setter']  = state_setter

    ed.use_effect(setup, [])
    with ed.ExportList():
        component()


class EmbedEdifice(QWidget):
    def __init__(self, component, **props):
        super().__init__(parent=None)

        main_layout = QVBoxLayout()

        self.setLayout(main_layout)

        self.controller = {
            'setter': None,
            'props': props
        }
        self._component = component
        self._state = state

        self.ed_app = ed.App(ExportComponent(self._component, self.controller), create_application=False)

        self.edifice_widgets = self.ed_app.export_widgets()
        for w in self.edifice_widgets:
            w.setParent(self)
            main_layout.addWidget(w)

    def setState(self, new_state):
        self.controller['setter'](new_state)

        
if __name__ == "__main__":
    app = QApplication([])

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    state_edit = QTextEdit()
    ed_widget = EmbedEdifice(
        CompoundComponent,
        props={
            'x': 0,
            'error': None
        }
    )

    def compile_to_state(text):
        try:
            state = {
                'error': None,
                'x': eval(text),
            }

        except SyntaxError as err:
            state = {
                'error': str(err),
                'x': 0
            }
        except Exception as err:
            state = {
                'error': str(err),
                'x': 0
            }
        return state

       
    state_edit.textChanged.connect(
        lambda: 
        ed_widget.updateState(
            compile_to_state(state_edit.toPlainText())
        )
    )

    main_window = QWidget()
    main_layout = QVBoxLayout()
    main_layout.addWidget(state_edit)
    main_layout.addWidget(ed_widget)
    main_window.setLayout(main_layout)
    main_window.show()

    event_loop.run_until_complete(app_close_event.wait())
    event_loop.close()