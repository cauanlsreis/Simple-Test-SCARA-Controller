#include <AccelStepper.h>

// Definição do motor de passo para o eixo Z (altura)
// Assume-se: DRIVER (1 pin for STEP, 1 pin for DIR)
// STEP (Passo) no Pino 2
// DIR (Direção) no Pino 5
AccelStepper stepperZ(AccelStepper::DRIVER, 2, 5);

// Pino ENABLE (Habilitar) - Usado para ligar/desligar o motor
// Para a CNC Shield, o pino 8 controla o ENABLE de todos os eixos
#define ENABLE_PIN 8 

void setup() {
  // Configura o pino ENABLE e o define como LOW para habilitar o motor
  // (O pino ENABLE da CNC Shield geralmente precisa estar em LOW para LIGAR)
  stepperZ.setEnablePin(ENABLE_PIN);
  stepperZ.enableOutputs(); // Habilita as saídas (coloca o ENABLE_PIN em LOW)

  // Define as configurações de movimento
  stepperZ.setMaxSpeed(2000);   // Velocidade máxima em passos por segundo
  stepperZ.setAcceleration(500); // Aceleração em passos/segundo^2

  // Define o primeiro destino de movimento (exemplo: 2000 passos)
  stepperZ.moveTo(2000);
}

void loop() {
  // Se o motor chegou ao destino (distância restante é 0)
  if (stepperZ.distanceToGo() == 0) {
    // Define o novo destino para o lado oposto da posição atual
    // Isso cria o movimento de "vai e volta"
    stepperZ.moveTo(-stepperZ.currentPosition());
  }

  // A função run() deve ser chamada repetidamente para fazer o motor mover
  // Ele verifica se há um moveTo pendente e executa os passos necessários.
  stepperZ.run();
}