import serial
import socket
import time

PC_IP = "192.168.2.157"   # <-- CHANGE to your PC's IP
PC_PORT = 5000


def connect_arduino():
    for port in ('/dev/ttyACM0','/dev/ttyACM1'):
        try:
            return serial.Serial(port=port, baudrate=115200, timeout=1)
        except Exception:
            continue
    raise RuntimeError("Arduino not able to connect.")


def connect_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((PC_IP, PC_PORT))
    return sock


if __name__ == "__main__":
    arduino = connect_arduino()
    time.sleep(2)
    print(f"Connected to Arduino on {arduino.port}")

    sock = connect_socket()
    print("Connected to PC socket")

    while True:
        line = arduino.readline().decode('utf-8', errors='ignore')
        if line:
            sock.sendall(line.encode('utf-8'))

## Need to add socket for hydrophone stuff 
