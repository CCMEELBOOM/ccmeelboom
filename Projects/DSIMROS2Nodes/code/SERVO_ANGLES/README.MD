# Servo Angle ROS 2 README

This document explains the theory and scripts used to collect servo angle data from the BlueROV2 sensor servos. The Arduino sketch reads servo feedback angles, the socket bridge sends the angle data to the PC, and the ROS 2 node publishes the values to a ROS topic.

---

## Angle Feedback Theory

The Parallax Feedback 360° servos provide a feedback PWM signal. The Arduino measures the high-time of the feedback pulse and converts the duty cycle into a raw angular position.

$$
\text{Duty Cycle} = \frac{t_{high}}{T} \times 100
$$

where $t_{high}$ is the measured HIGH pulse time and $T$ is the feedback signal period.

The raw angle is then calculated from the feedback duty cycle using the servo feedback range:

$$
\theta_{raw} = \frac{(D - 2.9) \times 360}{97.1 - 2.9 + 1.0}
$$

where $D$ is the duty cycle percentage. The script then shifts the raw angle relative to each servo zero point:

$$
\theta_{shifted} = \theta_{raw} - \theta_{zero}
$$

This makes each output angle relative to the sensor's forward-facing reference direction.

---


## Servo Angle Zeroing

The servos are mounted at non-zero directions, where zero degrees is defined as the front of the BlueROV2. The corresponding angle adjustments are:

$$
\theta_{top} = 125^\circ
$$

$$
\theta_{portside} = 90^\circ
$$

$$
\theta_{starboard} = 145^\circ
$$

These offsets align the measured servo angles with the BlueROV2 reference frame.

---

## Servo Homing and Oscillation

At startup, each servo moves to its assigned zero point. The Arduino compares the current raw angle to the zero point and nudges the servo clockwise or counterclockwise until it is within the allowed tolerance.

After homing, the servos oscillate back and forth around the zero point. This keeps the sensor motion within a safe range and helps avoid cable bending or twisting.

Example of bending cable:
![image of bending cable](/Image_Gallery/PXL_20260519_230122678.jpg)

Example of proper position:
![image of bending cable](/Image_Gallery/PXL_20260519_230056400.jpg)

The sketch uses three servo channels:

| Servo | Servo Pin | Feedback Pin | Zero Point |
|---|---:|---:|---:|
| Top | `5` | `3` | `125°` |
| Portside | `9` | `6` | `90°` |
| Starboard | `11` | `10` | `145°` |

---

## Serial and Socket Data Flow

The Arduino prints the three shifted servo angles as one comma-separated line:

```text
angle_top,angle_starboard,angle_port
```

Example:

```text
12.5,-34.2,45.8
```

The `talk-to-pc.py` script reads this serial data from the Arduino at `115200` baud and forwards each line to the PC over a TCP socket.

---

## How the ROS 2 Node Works

The `multi_servo_angle_node_new.py` node opens a TCP server on port `5000` and waits for the Raspberry Pi socket bridge to connect. Once connected, it receives newline-separated angle data, converts the comma-separated values into floats, and publishes them as a `Float64MultiArray`.

The main configuration values are:

| Item | Value |
|---|---|
| Node name | `multi_servo_angle_node_new` |
| Socket host | `0.0.0.0` |
| Socket port | `5000` |
| Published topic | `/servo_angles` |
| Message type | `std_msgs/Float64MultiArray` |
| Timer period | `0.02 s` |

The node follows this process:

1. Start a TCP socket server on the PC.
2. Wait for the Raspberry Pi to connect.
3. Receive angle lines from the socket bridge.
4. Split each line by commas.
5. Convert the values to floating-point angles.
6. Publish the angle array to `/servo_angles`.

---

## Full Data Pipeline

The full servo angle data pipeline is:

```text
Servo feedback signal → Arduino sketch → Serial output → talk-to-pc.py → TCP socket → ROS 2 node → /servo_angles
```

This allows the servo angle measurements to be used by other ROS 2 nodes during BlueROV2 operation.

---

## Appendix

[Parallax Feedback 360° High-Speed Servo Documentation](https://www.pololu.com/file/0J1395/900-00360-Feedback-360-HS-Servo-v1.2.pdf)

[ROS2 Tutorial](https://www.youtube.com/watch?v=0aPbWsyENA8&list=PLLSegLrePWgJudpPUof4-nVFHGkB62Izy)

[Graph Digitizer](https://huangziyuan10-a11y.github.io/graph-digitizer-web/)