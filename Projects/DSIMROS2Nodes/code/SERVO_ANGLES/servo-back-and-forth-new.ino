#include <Servo.h>
#include <math.h>

/* 
This script allows the sensors to move back and forth within an accepted range, preferable 180,
which prevents bending damage to the cables (see homing and oscillation functions).
This movement is also paired with a data collection function that collects angle 
position data (see angle output function) and can be employed by R0S2.
*/ 
// Documentation of the Parallax Feedback 360° High-Speed Servo:
//https://www.pololu.com/file/0J1395/900-00360-Feedback-360-HS-Servo-v1.2.pdf





// ----------------------------------------------------
//-----------------------------------------------------
//-----------------------------------------------------
//       VARIABLES USED IN FUNCITONS START HERE 
// ----------------------------------------------------
// ----------------------------------------------------
// -------------------- Pins --------------------------
// Top servo
const int TOP_SERVO_PIN = 5;
const int TOP_FEEDBACK_PIN = 3;

// Starboard servo
const int STARBOARD_SERVO_PIN = 9;
const int STARBOARD_FEEDBACK_PIN = 6;

// Port servo
const int PORT_SERVO_PIN = 11;
const int PORT_FEEDBACK_PIN = 10;

// -------------------Zero Points-----------------
float ZERO_POINT_TOP       = 125.0f;
float ZERO_POINT_STARBOARD = 90.0f;
float ZERO_POINT_PORT      = 145.0f;

//-------------------Stop PWM---------------------
const int STOP_PWM = 1500; 

//------------------CW & CCW Nudges --------------
const int HOME_CW_PWM  = 1550;
const int HOME_CCW_PWM = 1450; 
// The PWM value should be greater than 1520 and lower than 1470 to be able to rotate. 
// However, the servo has to overcome static friction to be able to rotate, thus the push
// initiated by writeMicroseconds() should be greater than 1520 and lower than 1470.
// As tested, 1530 and 1470 were not enought to overcome the static friction. 
// Increase the value of CW_PWM ever so slightly and decrease CCW_PWM if the sensors don't move.
// 
//CW movement is positive and occurs at PWM> 1500 
//This is based on Parallax docs

// pulseIn timeout in microseconds (prevents hanging if feedback wire is bad)
const unsigned long PULSE_TIMEOUT_US = 30000; // 30ms
const unsigned long HOMING_TIMEOUT  = 80000;

// Print period
const unsigned long PRINT_PERIOD_MS = 20;
unsigned long lastPrintTime = 0; 

// ---------------- Servo objects ----------------
Servo TOP_SERVO;
Servo STARBOARD_SERVO;
Servo PORT_SERVO;

// ---------------- Servo Arrays-------------------
float ZERO_POINTS[] = {ZERO_POINT_TOP,ZERO_POINT_STARBOARD, ZERO_POINT_PORT};
Servo* SERVO_ARRAY[] = {&TOP_SERVO, &STARBOARD_SERVO,&PORT_SERVO};
int SERVO_PIN_ARRAY[] = {TOP_SERVO_PIN,STARBOARD_SERVO_PIN, PORT_SERVO_PIN};
int SERVO_FEEDBACK_PIN_ARRAY[] = {TOP_FEEDBACK_PIN, STARBOARD_FEEDBACK_PIN, PORT_FEEDBACK_PIN};
// ---------------- Tolerance Deg-------------------
const float TOLERANCE_DEG = 3.0f;
// ----------------NUM_SERVOS--------------------------
//for indexing
const int NUM_SERVOS=3;
// ---------------DIRECTION ARRAY ---------------------
//~ CW =+1, CCW = -1
int directions[NUM_SERVOS] = {-1, -1, -1};
// ---------------TIME INTERVAL INITIALIZATION --------
unsigned long last_ros_time = 0;
// ----------------------------------------------------
//-----------------------------------------------------
//-----------------------------------------------------
//      FUNCTIONS USED IN THIS CODE START HERE 
// ----------------------------------------------------
//-----------------------------------------------------
//-----------------------------------------------------


/*
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@ RPM to PWM Conversion Function @@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

The goal of this function is to facilitate the speed parametric input
of the servo.
*/

int pwm_conv( int RPM_SPEED ){
  int pwm_speed;
  if (RPM_SPEED > 147){
    pwm_speed = STOP_PWM;
  }
// Don't want to have a value larger than the maximum rpm the servo can handle.
  
  else if (RPM_SPEED > 0){
    pwm_speed = 1/0.735 * (RPM_SPEED)+1520; // 1/0.735 is the ratio between PWM and RPM
    // 1520 is the lowerbound PWM of the servo for CW rotation 
  }
  else{
    pwm_speed = STOP_PWM;
  }
return (pwm_speed);
}

// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// @@@@@@@@@@@@@@@ Get Raw Angle Function @@@@@@@@@@@@@
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// ~ Raw angle is based off duty cycle of the servo.

float get_raw_angle(int feedbackPin, unsigned long pulseTimeout){
      
    int current_feedback_pin = feedbackPin;
    float time_high = pulseIn(current_feedback_pin, HIGH, pulseTimeout); 
    /*
    built-in function that allows the arduino to track how long the PWM signal
    remains in high, in microseconds.
    */
    //float time_low = pulseIn(current_feedback_pin, LOW, pulseTimeout);

    if (time_high == 0){ //|| time_low == 0) {
      return NAN;
      }
    // this signifies the system is not active and the servo is not receiving any PWM signal.
    //float cycle_time = (float)(time_low + time_high);
    float cycle_time = 1100.0f; // given by parallax 360 Doc.
    float duty_cycle = (100.0f * time_high) / cycle_time; // multiply by 100 to get proper unit for ratio 
    float raw_angle = ((duty_cycle - 2.9f) * 360.0f) / (97.1f - 2.9f + 1.0f);
    /* 2.9 is the Duty Cycle min (%) the servo can sustain.
    97.1 is the Duty Cycle max (%) the servo can sustain.
    */
    // 
    
    return raw_angle;
}
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// @@@@@@@@@@@@@@@  Homing Function @@@@@@@@@@@@@@@@@@@
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// ~ Needs to get raw angle and zero angle, find the difference, and determine if CW or CCW based on smallest travel distance.
// ~ Goes in void setup()
// ~ Each of the feedback_pins must be run through this function in void setup.

bool move_to_start_one(Servo *s, int feedback_pin, float zero_point, float tolerance_deg, unsigned long pulse_timeout) {
  unsigned long start_ms = millis(); // beginning of time stamp

  while (true) {
    float raw_angle = get_raw_angle(feedback_pin, pulse_timeout);

    // If feedback missing, stop to be safe
    if (isnan(raw_angle)) {
      s->writeMicroseconds(STOP_PWM);
            // keep trying until timeout; this also helps catch intermittent feedback wiring
    } else {
      // Are we at home?
      if (fabs(raw_angle - zero_point) <= tolerance_deg) {
        s->writeMicroseconds(STOP_PWM);
        return true;
      }

      // Same "closest direction" logic you used
      if ((raw_angle > zero_point) && (raw_angle <= zero_point + 180.0f)) {
        s->writeMicroseconds(HOME_CW_PWM); 
        // nudges the sensor slightly toward the zeropoint CW
      } else {
        s->writeMicroseconds(HOME_CCW_PWM);  
        // nudges the sensor slightly toward the zeropoint CCW
      }
    }

    if (millis() - start_ms > HOMING_TIMEOUT) {
      s->writeMicroseconds(STOP_PWM);
      /* Stops the the homing function if too much time has elapsed.
      */
      return false;
    }

    delay(15);
  }
}

// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// @@@@@@@@@@@  Angle Oscillation Function @@@@@@@@@@@@
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// ~ change RPM_SPEED as you wish...
/* function that generates the oscillation of the sensors. The range of the sensors should be 180, with limits 
-90 and 90 degree from the zero point(original direction).
The zero point is the horizontal direction facing the front of the sub. 
This ensures cable maintenance. 
*/ 

int RPM_SPEED = 50; // For servo to rotate, RPM_SPEED > 0, Max RPM_SPEED = ~147 rpm
int PWM_SPEED = pwm_conv(RPM_SPEED);
// ~ PWM Speed is x where PWM is 1500 +- x. Just the difference between the STOP_PWM and any increment.

void oscillation(int i, Servo *s, int feedback_pin, int PWM_SPEED, float zero_point, float tolerance_deg, unsigned long pulse_timeout){

  float angle = get_raw_angle(feedback_pin, pulse_timeout);
  
  //float upper_limit = zero_point + 87.0f;
  //float lower_limit = zero_point - 87.0f; 
  float diff = angle - zero_point ;

  if (isnan(angle)) return;
 
  //if ((angle-90.0f >= zero_point) && (angle > zero_point)){
  //if ((angle >= upper_limit)){

  if (diff >= 85.0) {
    directions[i] = 1; //CW
  }
  //else if ((angle + 90.0f <= zero_point) && (angle < zero_point)){
  //else if ((angle <= lower_limit)){
  if (diff <= -85.0) {
    directions[i] = -1; //CCW
  } 
  if (diff >= 93.0 || diff <= -93.0){
    direction[i]=0 ;
  }
  s->writeMicroseconds(STOP_PWM + (directions[i] * (PWM_SPEED - STOP_PWM)));


  // function that will kill oscillation of the sensors if they go over their set range. 
  // For each void loop iteration the servo should be able to move if the conditions are met.
  
}

// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// @@@@@@@@@@@@@  Angle Output Function @@@@@@@@@@@@@@@
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// ~ Change ROS_INTERVAL based on how high you want output angle 

const int ROS_INTERVAL = 20;//(20 is 50Hz collection rate)

float shifted_angle(int feedback_pin, float zero_point, unsigned long pulse_timeout){

  float raw_angle = get_raw_angle(feedback_pin, pulse_timeout); // acquiring data from the servos

  if (isnan(raw_angle)) return -999.0f; // if no data is found, displays -999.0

  float corrected_angle = raw_angle - zero_point; 
  // actual angle of the sensor, with reference
  // from sensor when facing toward the front of the sub

  while (corrected_angle > 180.0f) corrected_angle -= 360.0f;
  while (corrected_angle <= -180.0f) corrected_angle += 360.0f;
  
  return corrected_angle;
}




// ----------------------------------------------------
//-----------------------------------------------------
//-----------------------------------------------------
//              VOID SETUP STARTS HERE 
// ----------------------------------------------------
//-----------------------------------------------------
//-----------------------------------------------------

void setup() {
  Serial.begin(115200);
  // Initialize Hardware
  for (int i = 0; i < NUM_SERVOS; i++) {
    pinMode(SERVO_FEEDBACK_PIN_ARRAY[i], INPUT); 
    SERVO_ARRAY[i]->attach(SERVO_PIN_ARRAY[i]);
    SERVO_ARRAY[i]->writeMicroseconds(STOP_PWM);
  }

  // Run Homing Function
  for (int i = 0; i < NUM_SERVOS; i++) {
    bool success = move_to_start_one(
      SERVO_ARRAY[i],
      SERVO_FEEDBACK_PIN_ARRAY[i],
      ZERO_POINTS[i],
      TOLERANCE_DEG, 
      PULSE_TIMEOUT_US
    );

    if (!success) {
      // If any servo fails, lock the system forever
      while(1) {
        // Silent failure state
      }
    }  
  }
}

// ----------------------------------------------------
//-----------------------------------------------------
//-----------------------------------------------------
//              VOID LOOP STARTS HERE 
// ----------------------------------------------------
//-----------------------------------------------------
//-----------------------------------------------------
// ~ void loop will do two things:
//    1) Output shifted angle reading used in ROS2
//    2) Oscilate the servo +- 90 degrees from shifted angle

void loop() { 
  // 1. UPDATE MOVEMENTS
  for (int i = 0; i < NUM_SERVOS; i++) {
    oscillation(
      i, // Use 'i' as the index for the directions array
      SERVO_ARRAY[i],
      SERVO_FEEDBACK_PIN_ARRAY[i],
      PWM_SPEED, 
      ZERO_POINTS[i], 
      TOLERANCE_DEG,
      PULSE_TIMEOUT_US
    ); 
  }
  // 2. SEND DATA TO ROS2
  if (millis() - last_ros_time >= ROS_INTERVAL) {
    last_ros_time = millis();

    for (int i = 0; i < NUM_SERVOS; i++) {
      // Get the value from the function
      float current_ang = shifted_angle(
        SERVO_FEEDBACK_PIN_ARRAY[i],
        ZERO_POINTS[i], 
        PULSE_TIMEOUT_US
      );

      Serial.print(current_ang);

      // Only print a comma if it's NOT the last servo
      if (i < NUM_SERVOS - 1) {
        Serial.print(",");
      }
    }
    // New line at the end of the full set of angles
    Serial.println(); 
  }
}
