import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
from smbus2 import SMBus
import VL53L0X

# Адрес мультиплексора TCA9548A
TCA9548A_ADDRESS = 0x70

# Функция для выбора порта на мультиплексоре
def select_port(bus, port):
    if 0 <= port <= 7:
        bus.write_byte(TCA9548A_ADDRESS, 1 << port)
    else:
        raise ValueError("Порт должен быть от 0 до 7")

# Класс для работы с датчиками в отдельном потоке
class SensorThread(QThread):
    update_signal = pyqtSignal(str)  # Сигнал для обновления текста в интерфейсе

    def __init__(self):
        super().__init__()
        self.running = False

    def run(self):
        self.running = True
        bus = SMBus(1)  # Используем I2C шину 1
        tof0 = VL53L0X.VL53L0X(i2c_bus=bus, i2c_address=0x29)
        tof2 = VL53L0X.VL53L0X(i2c_bus=bus, i2c_address=0x29)

        try:
            while self.running:
                # Чтение данных с порта 0
                select_port(bus, 0)
                tof0.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
                distance0 = tof0.get_distance()
                tof0.stop_ranging()

                # Чтение данных с порта 2
                select_port(bus, 2)
                tof2.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
                distance2 = tof2.get_distance()
                tof2.stop_ranging()

                # Вывод данных в консоль и отправка сигнала в интерфейс
                result = f"Порт 0: {distance0} мм, Порт 2: {distance2} мм"
                print(result)
                self.update_signal.emit(result)

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