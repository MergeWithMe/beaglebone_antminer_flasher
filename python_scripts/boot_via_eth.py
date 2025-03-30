#!/usr/bin/python3

import serial
import sys
import threading
import time
import os
import termios
import fcntl
from xmodem import XMODEM
from ymodem.Socket import ModemSocket

# Serial configuration
SERIAL_PORT = "/dev/ttyACM1"
BAUD_RATE = 115200

XMODEM_FILE = "/tftpboot/u-boot-spl.bin"
YMODEM_FILE = "/tftpboot/u-boot.img"

# Open serial port
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)

# Inbuffer
buffer = ""
signal_patterns = []

# Reset and flush buffers
ser.reset_input_buffer()
ser.reset_output_buffer()

# Set raw mode
fd = ser.fileno()
attrs = termios.tcgetattr(fd)
attrs[3] = attrs[3] & ~(termios.ICANON | termios.ECHO | termios.ECHOE | termios.ECHOK | termios.ECHONL | termios.ISIG)  # Raw mode
termios.tcsetattr(fd, termios.TCSANOW, attrs)
fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)  # Non-blocking mode

found_marker = False
signal_char = 'C'
end_read_thread = False
serial_thread = None

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def start_read_thread():
    global serial_thread
    # Start reading serial output in a separate thread
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()

def clear_buffers():
    """ Continuously read from serial unless paused. """
    global buffer
    buffer = ""

def read_serial():
    """ Continuously read from serial unless paused. """
    global found_marker
    global end_read_thread
    global buffer
    end_read_thread = False
    global signal_patterns

    while True:
        try:
            if end_read_thread:
                break
            data = ser.read(1024)
            if data:
                dec_data = data.decode(errors='ignore')
                sys.stdout.write(dec_data)
                sys.stdout.flush()
                
                buffer += dec_data  # Accumulate data in buffer
                for pattern in signal_patterns:
                    if pattern in buffer:
                        found_marker = True

        except serial.SerialException as e:
            print(f"[ERROR] Serial device disconnected: {e}")
            break
        except Exception as e:
            print(f"[ERROR] Serial read error: {e}")
            break

def wait_for_signal(arg_signal_patterns):
    """ Wait for the 'C' character in serial output. """
    global found_marker
    global signal_patterns
    global buffer
    buffer = ""
    found_marker = False
    signal_patterns = arg_signal_patterns
    print(f"[INFO] Waiting for one of {signal_patterns}...")
    
    while not found_marker:
        time.sleep(0.1)

    print(f"[INFO] Signal triggered ...")

def xmodem_send_callback(total, success, error):
    """ Progress callback for XMODEM transfer. """
    print(f"[INFO] XMODEM Progress - Sent: {sizeof_fmt(success*128)}, Errors: {error}")

def ymodem_send_callback(index, name, total, success):
    """ Progress callback for XMODEM transfer. """
    print(f"[INFO] YMODEM Progress - Sent: {sizeof_fmt(success)}")

def xmodem_send(file):
    global serial_thread
    clear_buffers()

    """ Perform XMODEM file transfer while serial reading is paused. """
    wait_for_signal(["C"])  # Wait for 'C' before proceeding

    def getc(size, timeout=1):
        return ser.read(size) or None

    def putc(data, timeout=1):
        return ser.write(data)

    global end_read_thread
    end_read_thread = True
    serial_thread.join()

    modem = XMODEM(getc, putc)
    with open(file, 'rb') as stream:
        print(f"[INFO] Sending file via XMODEM...")
        success = modem.send(stream, callback=xmodem_send_callback)
        if success:
            print("[INFO] XMODEM transfer complete!")
        else:
            print("[ERROR] XMODEM transfer failed!")

    start_read_thread()

def ymodem_send(file):
    global serial_thread
    clear_buffers()

    """ Perform XMODEM file transfer while serial reading is paused. """
    print("!!! THIS STEP MAY TAKE 1-2 MINUTES BEFORE IT STARTS ... BE PATIENT !!!")
    wait_for_signal(["C"])  # Wait for 'C' before proceeding

    def getc(size, timeout=1):
        return ser.read(size) or None

    def putc(data, timeout=1):
        return ser.write(data)

    global end_read_thread
    end_read_thread = True
    serial_thread.join()
    cli = ModemSocket(getc, putc)
    success = cli.send([file], callback=ymodem_send_callback)
    if success:
        print("[INFO] YMODEM transfer complete!")
    else:
        print("[ERROR] YMODEM transfer failed!")

    start_read_thread()


start_read_thread()

# Send file via XMODEM after detecting 'C'
xmodem_send(XMODEM_FILE)
ymodem_send(YMODEM_FILE)

wait_for_signal(["Press ESC"])
# Send the ESC key
ser.write(b"\x1b")

wait_for_signal(["U-Boot#"])

content = []
with open("netbootCommand.txt", "r") as f:
    content = ";".join(line.strip() for line in f) + "\n"
content = content.encode("ascii")
print("** About to write to SER:", content)
ser.write(content)



# Keep main thread alive
serial_thread.join()
