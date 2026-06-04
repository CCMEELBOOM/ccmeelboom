#!/usr/bin/env python3
import rclpy
import socket # For network communication
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray # Array of decimal numbers for servo angles

class MultiServoAngleNodeNew(Node): 
    def __init__(self):
        super().__init__("multi_servo_angle_node_new") # initializes the node with the name "multi_servo_angle_node_new"
        
        self.publisher_ = self.create_publisher(Float64MultiArray, "/servo_angles", 10) #creates a publisher to /servo_angles topic

        HOST = "0.0.0.0"
        PORT = 5000

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #creates IPv4 TCP socket
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT)) #Tells the computer to listen on Port 5000
        self.server.listen(1) #Only allow 1 connection at a time
        self.server.setblocking(False) # Keep the node from freezing while waiting for a connection

        self.get_logger().info(f"Listening for Pi on port {PORT}...")
        
        self.conn = None
        self.data_buffer = ""

        self.create_timer(0.02, self.network_loop)

    def network_loop(self):
        # Handle new connections
        if self.conn is None: #If no Pi is connected, it tries self.server.accept()
            try:
                self.conn, addr = self.server.accept() #halts execution on the server until a client attempts to connect
                self.conn.setblocking(False)
                self.get_logger().info(f"Pi connected from {addr}")
            except (BlockingIOError, socket.error):
                return

        # Receive data
        try:
            raw_data = self.conn.recv(1024) # Grabs up to 1024 bytes of text.
            if not raw_data: # If the Pi closes the script, this detects the "silence" and resets the connection.
                self.get_logger().warn("Pi disconnected.")
                self.conn = None
                return

            self.data_buffer += raw_data.decode("utf-8") #Since TCP is a "stream," messages can be cut in half pieces saved in data_buffer

            while "\n" in self.data_buffer: #only process data when there is a new line value.
                line, self.data_buffer = self.data_buffer.split("\n", 1)
                self.process_and_publish(line) #passes to next function

        except BlockingIOError:
            pass
        except Exception as e:
            self.get_logger().error(f"Socket error: {e}")
            self.conn = None

    def process_and_publish(self, line): #takes string of comma-serparated vals and converts it to array
        try:

            angle_list = [float(x.strip()) for x in line.split(",")]
            
            msg = Float64MultiArray()
            msg.data = angle_list
            self.publisher_.publish(msg) #publishes the array of servo angles to the /servo_angles topic
            # self.get_logger().info(f"Relayed: {msg.data}")
        except ValueError:
            self.get_logger().error(f"Received bad data format: {line}") #logs an error if the data is not in the expected format (e.g., non-numeric values or incorrect delimiters)

def main(args=None):
    rclpy.init(args=args)
    node = MultiServoAngleNodeNew()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()