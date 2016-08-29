// app_mode 0 = device is ON
// app_mode 1 = device is OFF


int app_mode = 0;
int switch_status = HIGH;
unsigned long time_pressed = 0;

// the setup function runs once when you press reset or power the board
void setup() 
  {
  pinMode(1, OUTPUT);         //PIN to notify RSPI to shut down
  pinMode(0, OUTPUT);         //PIN to control high voltage for power amplifier
  pinMode(4, OUTPUT);         //PIN to control low voltage for raspi and audio
  pinMode(3, INPUT_PULLUP);   //PIN to detect switch status
  digitalWrite(1, LOW);
  digitalWrite(0, LOW);
  digitalWrite(4, LOW);
  }

// the loop function runs over and over again forever
void loop() 
  {
  unsigned long now = millis(); 
  if (app_mode == 0)
    {
    switch_status = digitalRead(3);   // read power switch
    if (switch_status == HIGH)
      {
      delay(500);
      if (switch_status == HIGH)
        {
        app_mode = 1;
        time_pressed = now;
        digitalWrite(1, LOW);
        digitalWrite(4, LOW);
        }
      }
    }
  if (app_mode == 1)
    {
    if (now - time_pressed > 10000)
      {
      digitalWrite(0, LOW);
      }
    switch_status = digitalRead(3);   // read power switch
    if (switch_status == LOW)
      {
      delay(500);
      if (switch_status == LOW)
        {
        app_mode = 0;
        digitalWrite(1, HIGH);
        digitalWrite(0, HIGH);
        digitalWrite(4, HIGH);
        }
      }
    }
  }
