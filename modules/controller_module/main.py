from modules.controller_module.module.mod import Module
from time import sleep
from sys import platform
import signal

should_stop = False


def main():
    print("Starting application...")
    module = Module()
    print("Module created...")

    while not should_stop:
        module.process()
        sleep(0.1)

    module.stop()


def stop(signal, frame):
    global should_stop
    should_stop = True


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

if platform != "win32":
    signal.signal(signal.SIGQUIT, stop)

if __name__ == "__main__":
    main()
