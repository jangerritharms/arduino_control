// This sketch uses the servo library to arm the Hacker X-5 Pro ESC.
// #include <Servo.h>


int joyPinx = 0;
int joyPiny = 1;
int value=0;
int counter=0;
enum status {HANDSHAKE_SEND, HANDSHAKE_RECEIVE, RUNNING};
status s;
#define BUFFER_SIZE 10
char in[BUFFER_SIZE];

void setup() 
{
    Serial.begin(9600);
    s = HANDSHAKE_SEND;
    for (int i=0;i<BUFFER_SIZE; i++)
      in[i] = 0;
} 

void loop() 
{
    
    switch(s){
      case HANDSHAKE_SEND:
        counter=0;
        delay(100);
        Serial.println("series counter yaxis");
        s = HANDSHAKE_RECEIVE;
        break;
      case HANDSHAKE_RECEIVE:
        receive("go", RUNNING);
        delay(10);
        break;
      case RUNNING:
        value = analogRead(joyPiny);
        Serial.println(counter);
        Serial.println(value);
        Serial.println("");
        receive("done", HANDSHAKE_SEND);
        delay(100);
        counter++;
        break;
    }
}

void receive(const char* message, int new_state){
  char c;
  int index = 0;
  
  while(Serial.available() > 0){
    if (index < BUFFER_SIZE-1 && (c=Serial.read())!='\n') {
      in[index] = c;
      index++;
      in[index] = '\0';
    }
  }
  if (strcmp(in, message)==0){
    Serial.println(message);
    s = (status)new_state;
  }
  index = 0;
  for(int i=0;i<BUFFER_SIZE;++i)
    in[i] = 0;
}
