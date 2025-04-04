import sys
from PyQt5 import QtWidgets, QtCore, QtGui

class RoundImageLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setPixmap(self, pixmap):
        # Crea una maschera circolare
        size = min(pixmap.width(), pixmap.height())  # Imposta la dimensione minore come lato del cerchio
        mask = QtGui.QBitmap(pixmap.size())
        mask.fill(QtCore.Qt.white)

        # Disegna un cerchio sulla maschera
        painter = QtGui.QPainter(mask)
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.black)
        painter.drawEllipse(0, 0, size, size)  # Assicuriamo che la maschera sia un cerchio
        painter.end()

        # Applica la maschera all'immagine
        pixmap.setMask(mask)

        # Imposta la pixmap
        super().setPixmap(pixmap)

class ChatApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Imposta la finestra principale
        self.setWindowTitle("Skai_main")
        self.setGeometry(100, 100, 400, 600)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        # Layout principale
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Layout per la barra superiore (per menu e titolo)
        self.top_bar = QtWidgets.QHBoxLayout()
        self.top_bar.setContentsMargins(10, 10, 10, 10)
        self.layout.addLayout(self.top_bar)

        # Spacer per spostare il pulsante menu nell'angolo in alto a destra
        self.top_bar.addStretch()

        # Pulsante per il menu (fissato nell'angolo in alto a destra)
        self.menu_button = QtWidgets.QPushButton("☰", self)
        self.menu_button.setStyleSheet("background-color: transparent; color: white; font-size: 20px; border: none;")
        self.menu_button.clicked.connect(self.toggle_chat)
        self.top_bar.addWidget(self.menu_button)

        # Pannello di chat (sfondo trasparente, elementi visibili)
        self.chat_frame = QtWidgets.QFrame(self)
        self.chat_frame.setStyleSheet("background: rgba(169, 169, 169, 0.8); border-radius: 10px;")
        self.layout.addWidget(self.chat_frame)

        # Layout per la chat
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_frame)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)

        # Crea un layout orizzontale per l'immagine e il titolo
        image_and_title_layout = QtWidgets.QHBoxLayout()
        image_and_title_layout.setContentsMargins(0, 0, 0, 0)  # Rimuove i margini esterni
        image_and_title_layout.setSpacing(80)  # Distanza di 30px tra immagine e titolo

        # Immagine rotonda
        self.image_label = RoundImageLabel(self)
        self.image_pixmap = QtGui.QPixmap("/home/endrx/Scrivania/codes/skorpion/ai/skai.png").scaled(56, 56, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.image_label.setPixmap(self.image_pixmap)
        self.image_label.setFixedSize(56, 56)
        self.image_label.setStyleSheet("background: transparent;")  # Rimuove lo sfondo dietro l'immagine
        image_and_title_layout.addWidget(self.image_label)

        # Etichetta del titolo
        self.title_label = QtWidgets.QLabel("Skai", self.chat_frame)
        self.title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: transparent;")

        # Allinea verticalmente il testo al centro rispetto all'immagine
        image_and_title_layout.addWidget(self.title_label, alignment=QtCore.Qt.AlignVCenter)

        # Aggiungi il layout orizzontale (contenente l'immagine e il titolo) al layout della chat
        self.chat_layout.addLayout(image_and_title_layout)

        # Area per i messaggi
        self.messages_area = QtWidgets.QScrollArea(self.chat_frame)
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setStyleSheet("background: transparent;")

        # Contenitore per i messaggi
        self.messages_area_widget = QtWidgets.QWidget()
        self.messages_area_content = QtWidgets.QVBoxLayout(self.messages_area_widget)
        self.messages_area_content.setContentsMargins(0, 0, 0, 0)  # Rimuove margini extra
        self.messages_area_content.setSpacing(5)  # Spazio tra i messaggi

        self.messages_area.setWidget(self.messages_area_widget)
        self.chat_layout.addWidget(self.messages_area)

        # Layout per l'inserimento del messaggio e il pulsante di invio
        self.input_layout = QtWidgets.QHBoxLayout()
        self.chat_layout.addLayout(self.input_layout)

        # Campo di input per il messaggio
        self.message_entry = QtWidgets.QTextEdit(self.chat_frame)
        self.message_entry.setStyleSheet("background: rgba(200, 200, 200, 0.8); border-radius: 10px;")
        self.message_entry.setPlaceholderText("Scrivi a Skorpion ai...")
        self.message_entry.setFixedHeight(50)
        self.message_entry.setWordWrapMode(QtGui.QTextOption.WordWrap)  # Abilita il ritorno a capo automatico
        self.input_layout.addWidget(self.message_entry)

        # Pulsante di invio con immagine
        self.send_button = QtWidgets.QPushButton(self.chat_frame)
        self.send_button.setStyleSheet("background: transparent; border: none;")
        self.send_button.setIcon(QtGui.QIcon("/home/endrx/Scrivania/codes/skorpion/ai/send.png"))  # Aggiungi l'immagine al pulsante
        self.send_button.setIconSize(QtCore.QSize(30, 30))  # Imposta la dimensione dell'icona
        self.send_button.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_button)

        # Gestione della pressione del tasto Enter per inviare il messaggio
        self.message_entry.installEventFilter(self)

        self.is_chat_visible = True
        self.chat_frame.setVisible(True)

    def toggle_chat(self):
        if self.is_chat_visible:
            self.chat_frame.hide()
        else:
            self.chat_frame.show()
        self.is_chat_visible = not self.is_chat_visible

    def send_message(self):
        message = self.message_entry.toPlainText().strip()
        if message:
            self.add_message("Tu: " + message, "#FFC38D")
            self.message_entry.clear()
            self.get_response(message)

    def get_response(self, message):
        self.add_message("Skai: " + message, "#B0EFFF")

    def add_message(self, text, color):
        message_widget = QtWidgets.QLabel(text)
        message_widget.setStyleSheet(f"background: {color}; border-radius: 10px; padding: 5px; margin: 5px;")
        message_widget.setWordWrap(True)
        message_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        message_widget.setMinimumWidth(100)
        self.messages_area_content.addWidget(message_widget)

        # Scorri fino in fondo all'area dei messaggi
        self.messages_area.verticalScrollBar().setValue(self.messages_area.verticalScrollBar().maximum())

    def eventFilter(self, obj, event):
        if obj is self.message_entry and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())
