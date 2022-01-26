// DRA818V_3

// set parameters for DRA818V
#define PD    4


int bw = 1; // bandwidth in KHz ( 0= 12.5KHz or 1= 25KHz )
float ftx = 144.8000; // tx frequency in MHz (134.0000 - 174.0000)
float frx = 144.8000; // rx frequency in MHz (134.0000 - 174.0000)
String tx_ctcss = "0000"; // ctcss frequency ( 0000 - 0038 ); 0000 = "no CTCSS" 
String rx_ctcss = "0000"; // ctcss frequency ( 0000 - 0038 ); 0000 = "no CTCSS" 
int squ = 0; // squelch level ( 0 - 8 ); 0 = "open" 

void setup()
{
  Serial.begin(9600);

  Serial.print("AT+DMOSETGROUP="); // begin message
  Serial.print(bw,1);
  Serial.print(",");
  Serial.print(ftx,4);
  Serial.print(",");
  Serial.print(frx,4);
  Serial.print(",");
  Serial.print(tx_ctcss);
  Serial.print(",");
  Serial.print(squ);
  Serial.print(",");
  Serial.println(rx_ctcss);
  pinMode(PD, OUTPUT);
  digitalWrite(PD,HIGH);
}

void loop()
{
}
