/*

 */
#include "ButtonBox.h"
#include <TimerOne.h>
#include <ClickEncoder.h>

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

//#define ENCODERS 3
//int firstPinToJoystick = 32;

String str = ""; 
//ClickEncoder* encoders[ENCODERS];
//
//void timerIsr() {
//  for(int f = 0; f < ENCODERS; ++ f)
//  {
//    encoders[f] -> service();
//  }
//}

//// variables will change:
//int16_t lastValues[ENCODERS];
//int16_t currentValues[ENCODERS];


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

void TestLED(int pinNumber,  String text)
{
  LCD.CharGotoXY(3, 12);
  LCD.print(text);
  FlashLED(pinNumber, 3);
}

void setup() {
  
  Serial.begin(9600);
  for(int ledPin=14; ledPin < 19; ++ledPin)
  {
    pinMode(ledPin, OUTPUT);
  }
  //encoders[2] = new ClickEncoder(A1, A0, -1, 2);
  //encoders[1] = new ClickEncoder(A3, A2, -1, 2);
  //encoders[0] = new ClickEncoder(A7, A6, -1, 2);
  //for(int f = 0; f < ENCODERS; ++f)
  //{
  //  pinMode(firstPinToJoystick+(f*2), OUTPUT);
  //  pinMode(firstPinToJoystick+(f*2)+1, OUTPUT);
  //  digitalWrite(firstPinToJoystick+(f*2), LOW);
  //  digitalWrite(firstPinToJoystick+(f*2)+1, LOW);
  //  
  //  encoders[f] -> setAccelerationEnabled(true);
  //  lastValues[f] = 0;
  //  currentValues[f] = 0;
  //}
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
  

  //Timer1.initialize(1000);
  //Timer1.attachInterrupt(timerIsr); 
  Wire.begin();         //I2C controller initialization.
  LCD.CleanAll(WHITE);    //Clean the screen with black or white.
  LCD.FontModeConf(Font_6x8, FM_ANL_AAA, BLACK_BAC); 
//
//  TestLED(ABS_LED, "ABS");
//  TestLED(TRACTION_LED, "Traction Control");
//  TestLED(REFUEL_LED, "Refuel");
//  TestLED(REPAIR_LED, "Fast Repair");
//  TestLED(TYRES_LED, "Change Tyres");
//        
}


void loop() 
{

    while (Serial.available())
    {
        String content = "";         // INBOUND SERIAL STRING
        String str = Serial.readStringUntil('!');
        content.concat(str);

        //switch(str.charAt(0))
        //{
        //  case 'P':
        //    str.remove(0, 1);
            LCD.CharGotoXY(3, 12);
            LCD.print(str);
            LCD.CharGotoXY(3, 20);
            LCD.print(content);
        //}
    }
}
    
//for (int f= 0; f< ENCODERS; ++f)    
//  {
//    currentValues[f] += encoders[f]->getValue();
//    //Serial.println(lastValues[f]);
//     
//    if (currentValues[f] != lastValues[f])
//    {
//      LCD.CharGotoXY(0,16*f);
//      LCD.print("From ");
//      LCD.print(lastValues[f]);
//      LCD.print(" to ");
//      LCD.print(currentValues[f]);
//      LCD.print("   ");
//      if (currentValues[f] > lastValues[f])
//      {
//        digitalWrite(firstPinToJoystick + f*2, HIGH);
//        delay(30);
//        digitalWrite(firstPinToJoystick + f*2, LOW);
//        
//      }
//      else
//      {
//        digitalWrite(firstPinToJoystick+f*2+1, HIGH);
//        delay(30);
//        digitalWrite(firstPinToJoystick+f*2+1, LOW);
//        
//      }
//      lastValues[f] = currentValues[f];
//      
//    }
//    
//  


