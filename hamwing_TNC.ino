#include <stdio.h>

/* Used Pins */
#define PTT      A2  // to the DRA818 PD pin
#define READ      4 //Read high or low

float freq = 144.650;                 // tx/rx frequency

int mode = 1; //mode = 0 or 1
int squelch = 5;
char ctcss[5] = "00000";
int val = 0;
//char startcommand[300];


void setup(){
  pinMode(PTT, OUTPUT); 
  pinMode(READ, INPUT); 
  Serial.begin(9600); // for tx/rx to hamwing
  //get it up and running
  Serial.write("AT+DMOCONNECT\r\n");
  //startcommand = "AT+DMOSETGROUP=%d,%f,%f,%s,%d,%s\r\n", mode, freq, freq, ctcss, squelch, ctcss
  char startcommand[] = "AT+DMOSETGROUP=1,146.500,146.500,00000,5,00000\r\n";
  Serial.write(startcommand);
}

void loop(){
  val = digitalRead(READ);   // read the input pin
  digitalWrite(PTT, val);
  delay(1000); 
}
