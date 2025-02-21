import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
from smbus2 import SMBus
import VL53L0X

# Адреса датчиков
SENSOR_ADDRESSES = [0x30, 0x31]  # Уникальные адреса для каждого датчика

# Класс для работы с датчиками в отдельном потоке
class SensorThread(QThread):
    update_signal = pyqtSignal(str)  # Сигнал для обновления текста в интерфейсе

    def __init__(self):
        super().__init__()
        self.running = False

    def run(self):
        self.running = True
        bus = SMBus(1)  # Используем I2C шину 1

        # Инициализация датчиков с разными адресами
        tof0 = VL53L0X.VL53L0X(i2c_bus=bus, i2c_address=SENSOR_ADDRESSES[0])
        tof1 = VL53L0X.VL53L0X(i2c_bus=bus, i2c_address=SENSOR_ADDRESSES[1])

        try:
            while self.running:
                try:
                    # Чтение данных с первого датчика
                    tof0.start_ranging()
                    distance0 = tof0.get_distance()
                    tof0.stop_ranging()

                    # Чтение данных со второго датчика
                    tof1.start_ranging()
                    distance1 = tof1.get_distance()
                    tof1.stop_ranging()

                    # Вывод данных в консоль и отправка сигнала в интерфейс
                    result = f"Датчик 0: {distance0} мм, Датчик 1: {distance1} мм"
                    print(result)
                    self.update_signal.emit(result)
                except Exception as e:
                    print(f"Ошибка при чтении данных: {e}")

                time.sleep(0.1)  # Задержка между измерениями
        finally:
            bus.close()

    def stop(self):
        self.running = False
        self.wait()

# Основное окно приложения
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Управление датчиками VL53L0X")
        self.setGeometry(100, 100, 300, 150)

        # Кнопка для запуска/остановки считывания
        self.button = QPushButton("Начать считывание", self)
        self.button.clicked.connect(self.toggle_sensor_thread)

        # Метка для отображения результатов
        self.label = QLabel("Результаты будут здесь", self)
        self.label.setStyleSheet("font-size: 16px;")

        # Вертикальный layout
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Поток для работы с датчиками
        self.sensor_thread = SensorThread()
        self.sensor_thread.update_signal.connect(self.update_label)

    def toggle_sensor_thread(self):
        if self.sensor_thread.isRunning():
            self.sensor_thread.stop()
            self.button.setText("Начать считывание")
        else:
            self.sensor_thread.start()
            self.button.setText("Остановить считывание")

    def update_label(self, text):
        self.label.setText(text)

    def closeEvent(self, event):
        # Остановка потока при закрытии окна
        if self.sensor_thread.isRunning():
            self.sensor_thread.stop()
        event.accept()

# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())