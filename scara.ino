// Controle SCARA por gesto
#include <AccelStepper.h>

AccelStepper motor(AccelStepper::DRIVER, 2, 5);

void setup() {
  Serial.begin(115200);
  motor.setEnablePin(8);
  motor.setMaxSpeed(200);
  motor.setAcceleration(100);
  Serial.println("SCARA pronto!");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "DIREITA") {
      motor.moveTo(motor.currentPosition() + 200);
    } else if (cmd == "ESQUERDA") {
      motor.moveTo(motor.currentPosition() - 200);
    }
  }
  motor.run();
}