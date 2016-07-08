#include "ButtonBox.h"
#include <TimerOne.h>
#include <ClickEncoder.h>
#include <TimeLib.h>

#include <Wire.h>
#include <I2C_LCD.h>
I2C_LCD LCD;
uint8_t I2C_LCD_ADDRESS = 0x51; //Device address configuration, the default value is 0x51.

#define ABS_LED 15
#define TRACTION_LED 14
#define REFUEL_LED 18
#define REPAIR_LED 17
#define TYRES_LED 16

#define PRESSED LOW
#define NOTPRESSED HIGH

struct iRacingConstants
{
    const int lf_tire_change     = 0x01;
    const int rf_tire_change     = 0x02;
    const int lr_tire_change     = 0x04;
    const int rr_tire_change     = 0x08;
    const int fuel_fill          = 0x10;
    const int windshield_tearoff = 0x20;
    const int fast_repair        = 0x40;
};

#define ENCODERS 3
int16_t lastEncoderValues[ENCODERS];

int firstPinToJoystick = 32;

ClickEncoder* encoders[ENCODERS];

void timerIsr() {
  for(int f = 0; f < ENCODERS; ++ f)
  {
    encoders[f] -> service();
  }

}


void FlashLED(int pinNumber, int flashCount = 3)
{
  for(int count = 0; count < flashCount; ++count)
  {
    digitalWrite(pinNumber, HIGH);
    delay(200);
    digitalWrite(pinNumber, LOW);
    delay(200);
  }
}
void setup() {
  
  Serial.begin(9600);
  for(int ledPin=14; ledPin < 19; ++ledPin)
  {
    pinMode(ledPin, OUTPUT);
  }
  encoders[2] = new ClickEncoder(A1, A0, -1, 2);
  encoders[1] = new ClickEncoder(A3, A2, -1, 2);
  encoders[0] = new ClickEncoder(A7, A6, -1, 2);
  for(int f = 0; f < ENCODERS; ++f)
  {
    pinMode(firstPinToJoystick+(f*2), OUTPUT);
    pinMode(firstPinToJoystick+(f*2)+1, OUTPUT);
    digitalWrite(firstPinToJoystick+(f*2), LOW);
    digitalWrite(firstPinToJoystick+(f*2)+1, LOW);
    lastEncoderValues[f] = 0;
    
    encoders[f] -> setAccelerationEnabled(true);
  }
  for(int x = 0; x< 3; ++x)
  {
    for(int c = 14; c < 19; ++c)
    {
      digitalWrite(c, HIGH);
    }
    delay(200);
    for(int c1 = 14; c1 < 19; ++c1)
    {
      digitalWrite(c1, LOW);
    }
    delay(200);
  }

  Wire.begin();         //I2C controller initialization.
  LCD.CleanAll(WHITE);    //Clean the screen with black or white.
  LCD.FontModeConf(Font_6x12, FM_ANL_AAA, BLACK_BAC); 

  Timer1.initialize(1000);
  Timer1.attachInterrupt(timerIsr); 
 
}


void loop() 
{
  if (timeStatus() == timeSet)
  {
    String s(hour());
    s = s + ":";
    int mins = minute();
    int secs = second();
    if (mins < 10)
    {
      s = s + "0";
    }
    s = s + String(mins);
    s = s + ":";
    if (secs < 10)
    {
      s = s + "0";
    }
    s = s + String(secs);
    s = s + "       ";
    
    LCD.CharGotoXY(3, 0);    
    LCD.print(s);
  }
  else
  {
    LCD.CharGotoXY(3, 0);
    LCD.print("Time not set");
  
  }

  for (int f= 0; f< ENCODERS; ++f)    
  {
    int value = encoders[f] -> getValue();
    if (value > 0)
    {
       digitalWrite(firstPinToJoystick + f*2, HIGH);
       delay(30);
       digitalWrite(firstPinToJoystick + f*2, LOW);
    }
    else if (value < 0)
    {
       digitalWrite(firstPinToJoystick + f*2+1, HIGH);
       delay(30);
       digitalWrite(firstPinToJoystick + f*2+1, LOW);
    }
  }
  
  
    while (Serial.available())
    {
        String content = "";         // INBOUND SERIAL STRING
        String str = Serial.readStringUntil('!');
        content.concat(str);

        switch(str.charAt(0))
        {
          case '#':
          {
            // text
            str.remove(0, 1);
            LCD.CharGotoXY(3, 12);
            LCD.print(str);
            break;
            }
          case 'P':
          {
            // Pit info
            str.remove(0, 1);
            int pitFlags = str.toInt();
            bool tyresLight = pitFlags & (15) == 15;
            if (tyresLight)
            {
                digitalWrite(TYRES_LED, HIGH);
            }
            else
            {
                digitalWrite(TYRES_LED, LOW);
            }
            if (pitFlags & 0x10)
            {
                digitalWrite(REFUEL_LED, HIGH);
            }
            else
            {
                digitalWrite(REFUEL_LED, LOW);
            }
            if (pitFlags & 0x40)
            {
                digitalWrite(REPAIR_LED, HIGH);
            }
            else
            {
               digitalWrite(REPAIR_LED, LOW);
            }
            
            break;
            }
         
          case 'X':
          {
            // Timestamp
            const unsigned long DEFAULT_TIME = 1357041600;
            str.remove(0,1);
            unsigned long pctime = str.toInt();
            if (pctime > DEFAULT_TIME)
            {
              setTime(pctime);
            }
            else
            {
              LCD.CharGotoXY(3, 0);
              LCD.print(str);
            }
            break;
          }
            
          default:
            break;
        }
    }
}



