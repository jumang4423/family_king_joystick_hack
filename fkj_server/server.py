import win32api, win32con
import sys
import serial
import time
import threading
from pynput.keyboard import Key, Controller

serial_port = serial.Serial("COM7", 115200)
new_data_event = threading.Event()
current_fcj_data = None
data_lock = threading.Lock()
exit_event = threading.Event()
keyboard = Controller()


def validate_fcj_data(data: str):
    if len(data) != 6:
        print("Invalid data")
        print(data)
        return False
    return True


def gen_diff(a, b):
    return 0 if a == b else 1 if a > b else 2


class FCJData:
    left: int
    right: int
    top: int
    bottom: int
    a: int
    b: int

    def __init__(self, data: str):
        assert validate_fcj_data(data)
        self.left = int(data[0])
        self.right = int(data[1])
        self.top = int(data[2])
        self.bottom = int(data[3])
        self.a = int(data[4])
        self.b = int(data[5])

    def __str__(self):
        return f"{int(self.left)}{int(self.right)}{int(self.top)}{int(self.bottom)}{int(self.a)}{int(self.b)}"

    def get_diff(self, diff):
        # no effect: 0, pressed: 1, released: 2
        return FCJData(
            f"{gen_diff(self.left, diff.left)}{gen_diff(self.right, diff.right)}{gen_diff(self.top, diff.top)}{gen_diff(self.bottom, diff.bottom)}{gen_diff(self.a, diff.a)}{gen_diff(self.b, diff.b)}"
        )


def read_serial():
    global current_fcj_data
    while not exit_event.is_set():
        if not serial_port.in_waiting > 0:
            time.sleep(0.01)
            continue
        serial_data = serial_port.readline().decode("utf-8", "ignore").strip()
        if not validate_fcj_data(serial_data):
            continue
        new_data = FCJData(serial_data)
        with data_lock:
            current_fcj_data = new_data
        new_data_event.set()


last_fcj_data = FCJData("000000")


def get_debounce(fcj_data: FCJData):
    global last_fcj_data
    debounce = fcj_data.get_diff(last_fcj_data)
    last_fcj_data = fcj_data
    return debounce


def get_mode():
    # try get arg
    if len(sys.argv) > 1:
        if sys.argv[1] in ["0", "1"]:
            return sys.argv[1]
        print("huh? (arg not 0 or 1)")
    while True:
        mode = input("mouse(0), rbo(1): ")
        if mode in ["0", "1"]:
            return mode
        print("huh?")


def mouse_m(vec: list):
    x, y = win32api.GetCursorPos()
    x += vec[0]
    y += vec[1]
    win32api.SetCursorPos((x, y))


def mouse_c(is_down: bool, is_right: bool = False):
    if is_down:
        if is_right:
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        else:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    else:
        if is_right:
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        else:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def rbo_t(key, is_down: bool):
    if is_down:
        keyboard.press(key)
    else:
        keyboard.release(key)


def mouse_mover():
    global current_fcj_data
    while not exit_event.is_set():
        new_data_event.wait()
        new_data_event.clear()
        if exit_event.is_set():
            break
        with data_lock:
            fcj_data = current_fcj_data
        # no debounce
        f = 10
        movef = [0, 0]
        if fcj_data.left == 1:
            movef[0] -= f
        if fcj_data.right == 1:
            movef[0] += f
        if fcj_data.top == 1:
            movef[1] -= f
        if fcj_data.bottom == 1:
            movef[1] += f
        mouse_m(movef)
        debounce = get_debounce(fcj_data)
        if str(debounce) == "000000":
            continue
        if debounce.a == 1:
            mouse_c(True, False)
        if debounce.a == 2:
            mouse_c(False, False)
        if debounce.b == 1:
            mouse_c(True, True)
            mouse_c(False, True)


def rbo_mover():
    global current_fcj_data
    while not exit_event.is_set():
        new_data_event.wait()
        new_data_event.clear()
        if exit_event.is_set():
            break
        with data_lock:
            fcj_data = current_fcj_data
        debounce = get_debounce(fcj_data)
        if str(debounce) == "000000":
            continue
        if debounce.left == 1:
            rbo_t("a", True)
            time.sleep(0.1)
            rbo_t("a", False)
            time.sleep(0.1)
            rbo_t("a", True)
        if debounce.left == 2:
            rbo_t("a", False)
        if debounce.right == 1:
            rbo_t("d", True)
            time.sleep(0.1)
            rbo_t("d", False)
            time.sleep(0.1)
            rbo_t("d", True)
        if debounce.right == 2:
            rbo_t("d", False)
        if debounce.top == 1:
            rbo_t("v", True)
        if debounce.top == 2:
            rbo_t("v", False)
        if debounce.bottom == 1:
            rbo_t("s", True)
        if debounce.bottom == 2:
            rbo_t("s", False)
        if debounce.a == 1:
            rbo_t("w", True)
        if debounce.a == 2:
            rbo_t("w", False)


if __name__ == "__main__":
    try:
        mode = get_mode()
        read_serial_thread = threading.Thread(target=read_serial, daemon=True)
        target = None
        if mode == "0":
            target = mouse_mover
        elif mode == "1":
            target = rbo_mover
        print("target: ", target)
        js_thread = threading.Thread(target=target, daemon=True)
        read_serial_thread.start()
        js_thread.start()

        while True:
            time.sleep(1)
            print("alive")
    except KeyboardInterrupt:
        print("bye bye")
        exit_event.set()
        new_data_event.set()  # Wake up the mouse_mover if it's waiting

        read_serial_thread.join()
        js_thread.join()
