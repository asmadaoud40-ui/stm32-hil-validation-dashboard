const int GREEN_PIN = 2;   // STM32 PD12
const int RED_PIN   =4 ;   // STM32 PD14

void setup()
{
  pinMode(GREEN_PIN, INPUT);
  pinMode(RED_PIN, INPUT);

  Serial.begin(115200);
}

void loop()
{
  if (Serial.available() > 0)
  {
    String command = Serial.readStringUntil('\n');

    command.trim();

    if (command == "READ")
    {
      int green_state = digitalRead(GREEN_PIN);
      int red_state   = digitalRead(RED_PIN);

      Serial.print("GREEN=");
      Serial.print(green_state);

      Serial.print(",RED=");
      Serial.println(red_state);
    }
  }
}