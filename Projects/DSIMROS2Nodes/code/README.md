# ROV2_ESC Overview

The ROV2_ESC package consists of two unique publisher nodes, `multi_servo_angle_node_new.py` and `sound_data_node.py` that publish servo angle data and hydrophone sound data the to the topics `/bluerov2/encoder_chatter` and `/bluerov2/cost_value_chatter` used in an extremum seeking algorithm for a BlueROV2 AUV. Servo angle data is collected through and Arduino the `multi-servo-back-and-forth-new.ino` sketch and the socket-PC data bridge is made through the `talk-to-pc.py` script. Hyrdophone data is collected and directly sent to PC through the  `talk-to-pc-dac.py` script. 

![picture of BlueROV2 here](Image_Gallery/PXL_20260513_221533852~2.jpg)

---
## Servo Angle Node

This node collect servo angle data which is important when finding the sound gradient (cost function). 

The angular position is recorded and tracked using the Arduino serial monitor through the script: `multi-servo-back-and-forth-new.ino`. Serial monitor data is then transferred from the Arduino to the computer via the socket-PC data bridge (`talk-to-pc.py`). The angular position data is published through the node: `multi_servo_angle_node_new.py`, to the topic: `/bluerov2/encoder_chatter`. This topic is used in the extremum-seeking algorithm. 

[`multi-servo-back-and-forth-new.ino`]
This sketch is uploaded to the Arduino UNO R3. It generates an oscillatory motion for each of the sensors and publishes their angular positions to the serial monitor. 

[`talk-to-pc.py`]
This script sends the angular position data collected by the Arduino to the computer. 

[`multi_servo_angle_node_new.py`]
This script creates the Servo Angle Node that will publish the angular position data to the topic `/bluerov2/encoder_chatter`. The node processes the information so that the data is functional for the extremum-seeking algorithm.

Output Data Sample: 

$\theta_{top}$

$\theta_{portside}$

$\theta_{starboard}$


![terminal example when all scripts for the Servo Angle Node are properly working](Image_Gallery/Screenshot%202026-05-19%20at%201.05.01%20PM.png)

---
## Hydrophone Data Node 

The hydrophone data is recorded through and processed through the script `talk-to-pc-dac.py`, which is ran on the raspberry pie. The hydrophone data is published through the node: `sound_data_node_new.py`, to the topic: `/bluerov2/cost_value_chatter`. This topic is used in the extremum-seeking algorithm. 

[`talk-to-pc-dac.py`]
This script sends the hydrophone data collected by the raspberry pie to the computer. The node processes the information so it is lisible for a human operator.  
 

[`sound_data_node_new.py`]
This script creates the Hydrophone Data Node that will publish the hydrophone data to the topic `/bluerov2/cost_value_chatter`. The node processes the information so that the data is functional for the extremum-seeking algorithm.



Output Data Sample: 

**dB<sub>top**

**dB<sub>portside**

**dB<sub>starboard**

![terminal example when all scripts for the Hydrophone Data Node are properly working](Image_Gallery/Screenshot%202026-05-19%20at%202.18.45%20PM.png)

---
## Set-Up of the BlueROV2 to ROS2

 ### Target of the Set-Up
 [Target Set-Up Video](Image_Gallery/DSIM%20ROV2%20MOVING%20.mp4)

 ### Physical Connections
 1. Connect the battery to the BlueROV2. 

 ![battery connection](Image_Gallery/PXL_20260513_221630130.jpg)

 2. Connect the BlueROV2 blue box to the rest of the hardware.
 3. Connect the BlueROV2 blue box to the computer using the USB cable.

 ![battery connection](Image_Gallery/PXL_20260513_221603960.jpg)

 4. Ensure that the connection between the hardware of the BlueROV2 UAV and the computer is proper.

  ![battery connection](Image_Gallery/PXL_20260513_221614326.jpg)

 ### Set-Up of the Raspberry Pi Connection.
 1. Open Visual Studio Code and connect the computer to the Raspberry Pi via 'main', present at the bottom left of the interface, also represented as two arrows `><`. 

 ![connection to raspberry pi](Image_Gallery/Screenshot%202026-05-20%20at%203.20.34 PM.png)

 2. Connect to the host: `192.168.2.120`
 3. Input password: `0000`
 3. Open the appropriate directory: `home/washed/Desktop`. 
 4. Access the folder `servo-test-bench`; `multi-servo-back-and-forth-new.ino`,`talk-to-pc.py`, and `talk-to-pc-dac.py` will be in this folder.

## How to Run the Nodes

 ### Run the Servo Angle Node
 1. Upload the sketch `multi-servo-back-and-forth-new.ino` on the Raspberry Pi terminal by calling the appropriate path. 
```
user@machine:~$ arduino --upload path/multi-servo-back-and-forth-new.ino
```
The sensor should start moving after the script has been uploaded. If not, try to adjust the sensors so that they are horizontal and facing forward. 
If the script is still not uploading properly, check if the correct folder has been called.

 2. Open two terminals from your computer and set them up side by side. Run the following two lines on their respective terminals:
```
user@machine:~$ ros2 run rov2_esc multi_servo_angle_node_new

user@machine:~$ ros2 topic echo /bluerov2/encoder_chatter
```
The first line will run the publisher node sending information to the topic, `/bluerov2/encoder_chatter`. 

The second line will allow the user to see if the data is published to the topic `/bluerov2/encoder_chatter`.

 3. Open and run talk-to-pc.py on a dedicated Raspberry Pi terminal.
 4. The data should start flowing as presented in Example of Desired Output below.

 ### Stop the Oscillation Function
 - Stop the oscillation of the sensors by typing the following command:
```
user@machine:~$ arduino --upload folder/multi-servo-stop.ino
```
 ### Run the Hydrophone Data Node
 1. Open two terminals from your computer and set them up side by side. Run the following two lines on their own respective terminals:
```
user@machine:~$ ros2 run rov2_esc sound_data_node

user@machine:~$ ros2 topic echo /bluerov2/cost_value_chatter
```
The first line will run the publisher node sending information to the topic, `/bluerov2/cost_value_chatter`.

The second line will allow the user to see if the data is published to the topic `/bluerov2/cost_value_chatter`.

 2. Open and run talk-to-pc_dac.py on a dedicated Raspberry Pi terminal.
 3. The data should start flowing as presented in Example of Desired Output below.

 ### Example of Desired Output
[Video of Working Nodes](Image_Gallery/Screencast%20from%2005-13-2026%2001_55_45%20PM.webm)


---
## Additional Info

The servo-back-and-forth-new.ino script is home to an oscillating function that will move the sensors around while also tracking their angular positions.
Notice that the servo-back-and-forth-new.ino script is not in python but in Arduino Language as the servos are directly controlled by an Arduino Controller. Thus, when modifying servo-back-and-forth-new.ino, make sure to employ the appropriate language. 

The creation of the multi_servo_angle_node_new.py was inspired by a tutorial found on the internet. For further information, please refer to Appendix, ROS2 Tutorial.

Any other details about the code can be found in the scripts themselves. 

### Update or Install the Nodes:
Inside the ~/ros2_ws repository, in the terminal run: 
```
user@machine:~$ colcon build 

user@machine:~$ source ~/.bashrc
```
---
## Appendix

Parallax Feedback 360° High-Speed Servo Documentation: https://www.pololu.com/file/0J1395/900-00360-Feedback-360-HS-Servo-v1.2.pdf

ROS2 Tutorial: https://www.youtube.com/watch?v=0aPbWsyENA8&list=PLLSegLrePWgJudpPUof4-nVFHGkB62Izy 

Useful Tools:

Graph Digitizer: https://huangziyuan10-a11y.github.io/graph-digitizer-web/
