

"""This script connects to two MCC 172 boards on a DAC hat and sends data to a PC socket.

We receive voltage data from three TC4013 hydrophones (one on the first board, two on 
the second board). Everey sample is first converted from voltage to pressure using the 
hydrophone sensitivity of 0.56234 mV/Pa. Next, the RMS value of every 50 samples is taken 
to reduce noise. When concerting to dB, the data is nondimensionalized with the reference 
pressure of 1 uPa for underwater acoustics, then converted to dB re 1 uPa.
"""
#Hyrdopphone TC4013
# Conversion for hydropphone sensitivity : -211 dB re 1V/µPa  
# Calculator: 
# https://www.translatorscafe.com/unit-converter/en-US/microphone-sensitivity/5-1/volt%20per%20pascal-decibel%20relative%20to%201%20volt%20per%201%20pascal/ 
# Pre amp IEPE1, with decibel gain of 26 dB 
# -185 dB re 1V/µPa = 0.564 mV/Pa

import socket
import time
import signal
import numpy as np

from matplotlib.pyplot import specgram
from daqhats import hat_list, HatIDs, OptionFlags, HatError
from daqhats.mcc172 import mcc172

#Configuration constants

PC_IP = "192.168.2.157"
PC_PORT = 5001
# The dac hat node has a sample rate of 950 Hz
SAMPLE_RATE = 25000.0
# Because the data is noisy the RMS value will be taken of these 50 samples before sending data to PC 
SAMPLES_PER_READ = 50
SOCKET_RETRY_DELAY = 2
SCAN_READ_TIMEOUT = 1.0

# Runs loop until there is an interuption 
running = True


def signal_handler(sig, frame):
    global running
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# This function connects to socket while running=true and will 
# retry every SOCKET_RETRY_DELAY seconds if connection fails.

def connect_socket():
    while running:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((PC_IP, PC_PORT))
            print(f"Connected to PC socket at {PC_IP}:{PC_PORT}")
            return sock
        except Exception as e:
            print(f"Socket connection failed: {e}")
            time.sleep(SOCKET_RETRY_DELAY)
    return None

# This function creates a bitmask for the specified channels, 
# which is used to configure the MCC 172 for scanning.

def create_channel_mask(channels):
    mask = 0
    for ch in channels:
        mask |= (1 << ch)
    return mask

# This function connects to the MCC 172 board at the specified address,

def connect_mcc172_by_address(address):
    boards = hat_list(HatIDs.MCC_172)
    for board in boards:
        if board.address == address:
            hat = mcc172(board.address)
            print(f"Connected to MCC 172 at address {board.address}")
            return hat
    raise RuntimeError(f"No MCC 172 found at address {address}")

#This function configures the MCC 172 for scanning on the specified channels with IEPE enabled.
def configure_hat(hat, channels, iepe_enabled=True):
    hat.a_in_clock_config_write(0, SAMPLE_RATE)

    for ch in channels:
        hat.iepe_config_write(ch, 1 if iepe_enabled else 0)

    time.sleep(0.5)

    channel_mask = create_channel_mask(channels)
    hat.a_in_scan_start(channel_mask, 0, OptionFlags.CONTINUOUS)

    print(f"Started scan on channels {channels} at {SAMPLE_RATE} S/s")

#This function stops the scan and cleans up the MCC 172, 
# and also turns off IEPE on the specified channels.
def stop_hat(hat, channels):
    try:
        hat.a_in_scan_stop()
    except Exception:
        pass

    try:
        hat.a_in_scan_cleanup()
    except Exception:
        pass

    for ch in channels:
        try:
            hat.iepe_config_write(ch, 0)
        except Exception:
            pass

def read_samples(hat, samples_per_read):
    result = hat.a_in_scan_read(samples_per_read, SCAN_READ_TIMEOUT)
    return result.data

sensitivity_mV_per_Pa = 0.56234  # TC4013 sensitivity with IEPE preamp gain


def main():
    sock = None
    hat0 = None
    hat1 = None

    board0_channels = [0]      # one hydrophone
    board1_channels = [0, 1]   # two hydrophones

    try:
        hat0 = connect_mcc172_by_address(0)
        hat1 = connect_mcc172_by_address(1)

        configure_hat(hat0, board0_channels, iepe_enabled=True)
        configure_hat(hat1, board1_channels, iepe_enabled=True)

        sock = connect_socket()
        if sock is None:
            return
# Data processing loop: read samples, convert to dB, and send to PC socket
        while running:
            try:
                data0 = read_samples(hat0, SAMPLES_PER_READ)
                data1 = read_samples(hat1, SAMPLES_PER_READ)

                if len(data0) == 0 or len(data1) == 0:
                    continue
                
                # Determines the length of data array.
                # Data from hat0 is single channel, data from hat1 is interleaved for two channels.
                n0 = len(data0)
                n1 = len(data1) // 2
                # Length of data arrays must be the same for processing, so take the minimum
                n = min(n0, n1)

                M = sensitivity_mV_per_Pa * 1e-3   # V/Pa
                p_ref = 1e-6   # 1 uPa reference for underwater acoustics

                #creates empty array to store pressure vals
                p0_vals = []
                p1_vals = []
                p2_vals = []    

                for i in range(n):

                    #hat0 has one hydrophone
                    h0 = data0[i]
                    #hat1 has two hydrophones interleaved, this reads the two channels separately
                    h1 = data1[2 * i]
                    h2 = data1[2 * i + 1]

                    # volts to pressure (Pa)
                    p0_vals.append(h0 / M)
                    p1_vals.append(h1 / M)
                    p2_vals.append(h2 / M)

                # --> numpy array 
                p0_vals = np.array(p0_vals)
                p1_vals = np.array(p1_vals)     
                p2_vals = np.array(p2_vals) 

                # RMS value of the 50 samples is taken to reduce noise before sending data to PC

                p0_rms = np.sqrt(np.mean(p0_vals**2))
                p1_rms = np.sqrt(np.mean(p1_vals**2))
                p2_rms = np.sqrt(np.mean(p2_vals**2))

                # pressure to dB re 1 uPa
                db0 = 20 * np.log10(max(p0_rms / p_ref, 1e-12))  # add small value to avoid log of zero
                db1 = 20 * np.log10(max(p1_rms / p_ref, 1e-12))
                db2 = 20 * np.log10(max(p2_rms / p_ref, 1e-12))

                # output format: "db0,db1,db2"
                line = f"{db0},{db1},{db2}\n"
                sock.sendall(line.encode("utf-8"))

            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                print(f"Socket error: {e}")
                try:
                    sock.close()
                except Exception:
                    pass
                sock = connect_socket()
                if sock is None:
                    break

            except HatError as e:
                print(f"MCC 172 error: {e}")
                break

            except Exception as e:
                print(f"Unexpected error: {e}")
                break

    finally:
        print("Shutting down...")
        if hat0 is not None:
            stop_hat(hat0, board0_channels)
        if hat1 is not None:
            stop_hat(hat1, board1_channels)
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
