import sys
import requests
import json
from PyQt5 import QtWidgets, QtCore, QtGui

class RoundImageLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setPixmap(self, pixmap):
        size = min(pixmap.width(), pixmap.height())  # Imposta la dimensione minore come lato del cerchio
        mask = QtGui.QBitmap(pixmap.size())
        mask.fill(QtCore.Qt.white)
        painter = QtGui.QPainter(mask)
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.black)
        painter.drawEllipse(0, 0, size, size)
        painter.end()

        pixmap.setMask(mask)
        super().setPixmap(pixmap)

class ChatApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Imposta la finestra principale
        self.setWindowTitle("Skai_main")
        self.setGeometry(100, 100, 300, 675)
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        window_width = self.width()
        window_height = self.height()
        self.move(screen.width() - window_width, (screen.height() - window_height) // 2)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        # Layout principale
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Layout per la barra superiore
        self.top_bar = QtWidgets.QHBoxLayout()
        self.top_bar.setContentsMargins(10, 10, 10, 10)
        self.layout.addLayout(self.top_bar)

        # Spacer per spostare il pulsante menu nell'angolo in alto a destra
        self.top_bar.addStretch()

        # Pulsante per il menu
        self.menu_button = QtWidgets.QPushButton("☰", self)
        self.menu_button.setStyleSheet("background-color: transparent; color: white; font-size: 20px; border: none;")
        self.menu_button.clicked.connect(self.toggle_chat)
        self.top_bar.addWidget(self.menu_button)

        # Pannello di chat
        self.chat_frame = QtWidgets.QFrame(self)
        self.chat_frame.setStyleSheet("background: rgba(169, 169, 169, 0.8); border-radius: 10px;")
        self.layout.addWidget(self.chat_frame)

        # Layout della chat
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_frame)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)

        # Layout per l'immagine e il titolo
        image_and_title_layout = QtWidgets.QHBoxLayout()
        image_and_title_layout.setContentsMargins(0, 0, 0, 0)
        image_and_title_layout.setSpacing(10)

        # Immagine rotonda
        self.image_label = RoundImageLabel(self)
        self.image_pixmap = QtGui.QPixmap("/home/kuser/skai/app/skai.png").scaled(56, 56, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.image_label.setPixmap(self.image_pixmap)
        self.image_label.setFixedSize(56, 56)
        self.image_label.setStyleSheet("background: transparent;")
        image_and_title_layout.addWidget(self.image_label)

        # Etichetta del titolo
        self.title_label = QtWidgets.QLabel("Skai", self.chat_frame)
        self.title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: transparent;")
        image_and_title_layout.addWidget(self.title_label, alignment=QtCore.Qt.AlignVCenter)

        # Aggiungi al layout
        self.chat_layout.addLayout(image_and_title_layout)

        # Area per i messaggi
        self.messages_area = QtWidgets.QScrollArea(self.chat_frame)
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setStyleSheet("background: transparent;")

        # Contenitore per i messaggi
        self.messages_area_widget = QtWidgets.QWidget()
        self.messages_area_content = QtWidgets.QVBoxLayout(self.messages_area_widget)
        self.messages_area_content.setContentsMargins(0, 0, 0, 0)
        self.messages_area_content.setSpacing(5)
        self.messages_area_content.setAlignment(QtCore.Qt.AlignTop)  # Allinea in alto

        # Spacer per mantenere i messaggi in alto
        self.spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.messages_area_content.addSpacerItem(self.spacer)

        self.messages_area.setWidget(self.messages_area_widget)
        self.chat_layout.addWidget(self.messages_area)

        # Layout per input e pulsante invio
        self.input_layout = QtWidgets.QHBoxLayout()
        self.chat_layout.addLayout(self.input_layout)

        # Campo di input per il messaggio
        self.message_entry = QtWidgets.QTextEdit(self.chat_frame)
        self.message_entry.setStyleSheet("background: rgba(200, 200, 200, 0.8); border-radius: 10px;")
        self.message_entry.setPlaceholderText("Scrivi a Skorpion AI...")
        self.message_entry.setFixedHeight(50)
        self.input_layout.addWidget(self.message_entry)

        # Pulsante di invio
        self.send_button = QtWidgets.QPushButton(self.chat_frame)
        self.send_button.setStyleSheet("background: transparent; border: none;")
        self.send_button.setIcon(QtGui.QIcon("/home/kuser/skai/app/send.png"))
        self.send_button.setIconSize(QtCore.QSize(30, 30))
        self.send_button.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_button)

        # Tasto Enter per inviare
        self.message_entry.installEventFilter(self)

        self.is_chat_visible = True

    def toggle_chat(self):
        self.chat_frame.setVisible(not self.is_chat_visible)
        self.is_chat_visible = not self.is_chat_visible

    def send_message(self):
        message = self.message_entry.toPlainText().strip()
        if message:
            self.add_message("Tu: " + message, "#FFC38D")
            self.message_entry.clear()
            self.get_response(message)

    def add_message(self, text, color):
        message_widget = QtWidgets.QLabel(text)
        message_widget.setStyleSheet(f"background: {color}; border-radius: 10px; padding: 5px; margin: 5px;")
        message_widget.setWordWrap(True)
        message_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        message_widget.setMinimumWidth(10)

        # Inserisci il messaggio prima dello spacer
        self.messages_area_content.insertWidget(self.messages_area_content.count() - 1, message_widget)

        # Scorri in fondo per mostrare il nuovo messaggio
        self.messages_area.verticalScrollBar().setValue(self.messages_area.verticalScrollBar().maximum())

    def eventFilter(self, obj, event):
        if obj is self.message_entry and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return and not event.modifiers() & QtCore.Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def get_response(self, message):
        payload = {
            'input': message,  # The input message
            'context': ""      # Optional, depending on Ollama's API requirement
        }

        headers = {
            'Content-Type': 'application/json'
        }

        try:
            # Send POST request to Ollama's local API
            response = requests.post("http://localhost:5000/chat", data=json.dumps(payload), headers=headers)
            
            # If the response is successful, parse the response
            if response.status_code == 200:
                response_data = response.json()  # Assuming response is in JSON
                ollama_reply = response_data.get('reply', 'Sorry, I couldn\'t get a response.')

                # Add the response to the chat
                self.add_message("Skai: " + ollama_reply, "#B0EFFF")
            else:
                self.add_message("Skai: Error communicating with Ollama API.", "#FF0000")
        except Exception as e:
            self.add_message("Skai: Failed to connect to Ollama API.", "#FF0000")
            print(f"Error: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())
