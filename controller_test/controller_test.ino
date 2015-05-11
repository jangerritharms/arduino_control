// This sketch uses the servo library to arm the Hacker X-5 Pro ESC.
#include <Servo.h>
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#include "Wire.h"

int joyPinx = 0;
int joyPiny = 1;
int motorPin = 9;
int arm = 1000;
unsigned long counter=0;
int sample_rate = 50;
enum status {HANDSHAKE_SEND=1, HANDSHAKE_RECEIVE, RUNNING};
Servo esc;

// MPU variables
MPU6050 mpu;
bool dmpReady = false;
uint8_t devStatus;
uint8_t mpuIntStatus;
uint16_t packetSize;
uint16_t fifoCount;
uint8_t fifoBuffer[64];
Quaternion q;
VectorFloat gravity;
float ypr[3];


int speedvalue = 1000;
status s;
String buffer;

volatile bool mpuInterrupt = false;
void dmpDataReady() {
  mpuInterrupt = true;
}

void activate_motor(){
  esc.attach(motorPin);
  esc.writeMicroseconds(arm);
}

void get_data(){
  int buf = buffer.substring(4).toInt();
  if (buf >= 1000 && buf <= 2000){
    speedvalue = buf;
    esc.writeMicroseconds(speedvalue);
  }
}

void receive(const char* message, int new_state, void (*func)()){
  if (buffer.startsWith(message)){
    if (new_state){
      Serial.println(message);
      s = (status)new_state;
    }
    if (func)
      (*func)();
  }
}

void setup() 
{
    Wire.begin();
    TWBR = 24;
    Serial.begin(115200);
    s = HANDSHAKE_SEND;
    
    mpu.initialize();
    mpu.testConnection();
    devStatus = mpu.dmpInitialize();
    
    if (devStatus == 0){
      mpu.setDMPEnabled(true);
      attachInterrupt(0, dmpDataReady, RISING);
      mpuIntStatus = mpu.getIntStatus();
      dmpReady = true;
      packetSize = mpu.dmpGetFIFOPacketSize();
    } else {
      Serial.println("DMP Initialization failed");
    }
}

void loop() 
{
    unsigned long time = millis();
    unsigned long start_time, end_time;
    char data_buf[10] = "";
    if(Serial.available() > 0)
      buffer = Serial.readStringUntil('\n');
    switch(s){
      case HANDSHAKE_SEND:
        esc.detach();
        counter=0;
        delay(100);
        Serial.println("series counter yaw pitch roll fcnt timer");
        s = HANDSHAKE_RECEIVE;
        break;
      case HANDSHAKE_RECEIVE:
        receive("go", RUNNING, &activate_motor);
        mpu.resetFIFO();
        break;
      case RUNNING:
        bool received = false;
        while (!received){
          
          // Wait for mpu
          if (!dmpReady) return;
          
          while (!mpuInterrupt);
          
          mpuInterrupt = false;
          mpuIntStatus = mpu.getIntStatus();
          
          fifoCount = mpu.getFIFOCount();
          
          // check for overflow (this should never happen unless our code is too inefficient)
          if ((mpuIntStatus & 0x10) || fifoCount > 100) {
            // reset so we can continue cleanly
            mpu.resetFIFO();
            Serial.println("FIFO overflow!");
        
            // otherwise, check for DMP data ready interrupt (this should happen frequently)
          } else if (mpuIntStatus & 0x02) {
            // wait for correct available data length, should be a VERY short wait
            while (fifoCount < packetSize) fifoCount = mpu.getFIFOCount();
        
            // read a packet from FIFO
            mpu.getFIFOBytes(fifoBuffer, packetSize);
        
            // track FIFO count here in case there is > 1 packet available
            // (this lets us immediately read more without waiting for an interrupt)
            fifoCount -= packetSize;
            // display Euler angles in degrees
            mpu.dmpGetQuaternion(&q, fifoBuffer);
            mpu.dmpGetGravity(&gravity, &q);
            mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
            start_time = micros();
            end_time = micros();
            received = true;
          }
        }
        Serial.print(counter);
        Serial.print('\t');
        Serial.print(ypr[0] * 180/M_PI);
        Serial.print('\t');
        Serial.print(ypr[2] * 180/M_PI);        
        Serial.print('\t');
        Serial.print(ypr[1] * 180/M_PI);
        Serial.print('\t');
        Serial.print(fifoCount);        
        Serial.print('\t');
        Serial.println(end_time-start_time);     
        receive("done", HANDSHAKE_SEND, NULL);
        receive("set", NULL, &get_data);
        counter++;
        break;
    }
    
    while ( millis()-time < 1000/sample_rate)
      delay(1);
}

