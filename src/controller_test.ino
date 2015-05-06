// This sketch uses the servo library to arm the Hacker X-5 Pro ESC.
// #include <Servo.h>


int joyPinx = 0;
int joyPiny = 1;
int value=0;
int counter=0;
enum status {HANDSHAKE_SEND=1, HANDSHAKE_RECEIVE, RUNNING};

int speedvalue = 1100;
status s;
String buffer;

void get_data(){
  int buf = buffer.substring(4).toInt();
  if (buf >= 1000 && buf <= 2000){
    speedvalue = buf;
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
    Serial.begin(9600);
    s = HANDSHAKE_SEND;
} 

void loop() 
{
    char data_buf[10] = "";
    if(Serial.available() > 0)
      buffer = Serial.readStringUntil('\n');
    switch(s){
      case HANDSHAKE_SEND:
        counter=0;
        delay(100);
        Serial.println("series counter yaxis");
        s = HANDSHAKE_RECEIVE;
        break;
      case HANDSHAKE_RECEIVE:
        receive("go", RUNNING, NULL);
        delay(10);
        break;
      case RUNNING:
        value = analogRead(joyPiny);
        Serial.println(counter);
        Serial.println(value);
        Serial.println("");
        receive("done", HANDSHAKE_SEND, NULL);
        receive("set", NULL, &get_data);
        delay(100);
        counter++;
        break;
    }
}

