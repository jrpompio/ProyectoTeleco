import sys
import serial
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QHBoxLayout, QFrame)
from PyQt5.QtCore import QTimer, Qt

# Divididos en 2 filas
ESTADOS_FILA_1 = [
    "INICIO", "INICIAR_WIFI_BLE", "ESCANEAR_BLE",
    "ESPERAR_CONEXION_BLE", "AUTENTICAR"
]

ESTADOS_FILA_2 = [
    "LEER_CREDENCIALES", "DESCONECTAR_BLE",
    "CONECTAR_WIFI", "CAPTURAR_IP", "FIN"
]

class BLEMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor BLE-WiFi")
        self.setGeometry(100, 100, 1000, 400)

        self.layout = QVBoxLayout()
        self.flow_layout_1 = QHBoxLayout()
        self.flow_layout_2 = QHBoxLayout()
        self.blocks = {}

        # Crear primera fila
        for estado in ESTADOS_FILA_1:
            frame = QFrame()
            frame.setStyleSheet("background-color: lightgray; "
                                "border: 1px solid black;")
            label = QLabel(estado)
            label.setAlignment(Qt.AlignCenter)
            inner_layout = QVBoxLayout()
            inner_layout.addWidget(label)
            frame.setLayout(inner_layout)
            self.blocks[estado] = frame
            self.flow_layout_1.addWidget(frame)

        # Crear segunda fila
        for estado in ESTADOS_FILA_2:
            frame = QFrame()
            frame.setStyleSheet("background-color: lightgray; "
                                "border: 1px solid black;")
            label = QLabel(estado)
            label.setAlignment(Qt.AlignCenter)
            inner_layout = QVBoxLayout()
            inner_layout.addWidget(label)
            frame.setLayout(inner_layout)
            self.blocks[estado] = frame
            self.flow_layout_2.addWidget(frame)

        self.result_label = QLabel("Resultado: ...")
        self.ip_label = QLabel("IP: ...")

        self.layout.addLayout(self.flow_layout_1)
        self.layout.addLayout(self.flow_layout_2)
        self.layout.addWidget(self.result_label)
        self.layout.addWidget(self.ip_label)
        self.setLayout(self.layout)

        # Puerto serial
        self.serial = serial.Serial('/dev/ttyUSB0', 115200)

        # Timer para leer sin bloquear GUI
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial)
        self.timer.start(100)

    def reset_blocks(self):
        for frame in self.blocks.values():
            frame.setStyleSheet("background-color: lightgray; "
                                "border: 1px solid black;")

    def highlight_block(self, estado):
        self.reset_blocks()
        if estado in self.blocks:
            self.blocks[estado].setStyleSheet(
                "background-color: lightgreen; border: 2px solid green;")

    def read_serial(self):
        while self.serial.in_waiting:
            line = self.serial.readline().decode(errors='ignore').strip()
            if line.startswith("ESTADO:"):
                estado = line.split(":")[1].strip()
                self.highlight_block(estado)
            elif line.startswith("RESULTADO:"):
                result = line.split(":")[1].strip()
                self.result_label.setText(f"Resultado: {result}")
            elif line.startswith("IP:"):
                ip = line.split(":")[1].strip()
                self.ip_label.setText(f"IP: {ip}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BLEMonitor()
    window.show()
    sys.exit(app.exec_())

