// Controle SCARA por gesto
#include <AccelStepper.h>

// Motor do braço principal SCARA
AccelStepper motorBraco(AccelStepper::DRIVER, 2, 5);

// Motor do antebraço
AccelStepper motorAntebraco(AccelStepper::DRIVER, 3, 6);

void setup() {
  Serial.begin(115200);
  
  // Configuração motor do braço principal
  motorBraco.setEnablePin(8);
  motorBraco.setMaxSpeed(2000);
  motorBraco.setAcceleration(500);
  
  // Configuração motor do antebraço
  motorAntebraco.setEnablePin(9);
  motorAntebraco.setMaxSpeed(2000);
  motorAntebraco.setAcceleration(500);
  
  Serial.println("SCARA com antebraco pronto!");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    // Movimentos do braço principal
    if (cmd == "BRACO_DIREITA") {
      motorBraco.moveTo(motorBraco.currentPosition() + 200);
    } else if (cmd == "BRACO_ESQUERDA") {
      motorBraco.moveTo(motorBraco.currentPosition() - 200);
    } 
    // Movimentos do antebraço
    else if (cmd == "ANTEBRACO_ESQUERDA") {
      motorAntebraco.moveTo(motorAntebraco.currentPosition() + 150);
    } else if (cmd == "ANTEBRACO_DIREITA") {
      motorAntebraco.moveTo(motorAntebraco.currentPosition() - 150);
    }
  }
  
  // Executa ambos os motores
  motorBraco.run();
  motorAntebraco.run();
}