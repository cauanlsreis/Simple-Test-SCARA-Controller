// Controle SCARA por gesto - Versão com Cinemática Simplificada
#include <AccelStepper.h>
#include <Servo.h>
#include <math.h>

// Define the stepper motors and the pins they will use
AccelStepper stepper1(1, 2, 5); // (Type:driver, STEP, DIR) - Braço principal
AccelStepper stepper2(1, 3, 6); // Antebraço
AccelStepper stepper3(1, 4, 7); // Rotação (phi)
// AccelStepper stepper4(1, 12, 13); // Eixo Z - REMOVIDO

Servo gripperServo; // Servo da garra

// Parâmetros do SCARA (dimensões em mm)
const double L1 = 228.0;    // Comprimento do braço principal
const double L2 = 136.5;    // Comprimento do antebraço

// Fatores de conversão (steps por unidade)
const float theta1AngleToSteps = 44.444444;  // steps por grau
const float theta2AngleToSteps = 35.555555;  // steps por grau
const float phiAngleToSteps = 10.0;          // steps por grau
// const float zDistanceToSteps = 100.0;        // steps por mm - REMOVIDO

// Variáveis de posição
double currentTheta1 = 0, currentTheta2 = 0, currentPhi = 0;

// Incrementos para movimentos por gestos
const double ANGLE_INCREMENT = 5.0;  // graus
// const double Z_INCREMENT = 5.0;      // mm - REMOVIDO

// Posições da garra (baseado no SCARA_Robot.ino)
const int GARRA_ABERTA = 180;   // Garra aberta
const int GARRA_FECHADA = 0;    // Garra fechada

void setup() {
  Serial.begin(115200);
  
  // Configuração dos motores
  stepper1.setMaxSpeed(2000);
  stepper1.setAcceleration(500);
  stepper2.setMaxSpeed(2000);
  stepper2.setAcceleration(500);
  stepper3.setMaxSpeed(2000);
  stepper3.setAcceleration(500);
  // stepper4 configuração removida
  
  // Configuração da garra (baseado no SCARA_Robot.ino)
  gripperServo.attach(A0, 600, 2500);
  gripperServo.write(GARRA_ABERTA); // Inicia com garra aberta
  delay(1000);
  
  Serial.println("SCARA com cinemática simplificada pronto!");
}

// Função simplificada para mover para ângulos específicos
void moveToAngles(double theta1, double theta2, double phi) {
  int steps1 = theta1 * theta1AngleToSteps;
  int steps2 = theta2 * theta2AngleToSteps;
  int steps3 = phi * phiAngleToSteps;
  
  stepper1.moveTo(steps1);
  stepper2.moveTo(steps2);
  stepper3.moveTo(steps3);
  
  // Atualiza posições atuais
  currentTheta1 = theta1;
  currentTheta2 = theta2;
  currentPhi = phi;
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    // Movimentos do braço principal (theta1)
    if (cmd == "BRACO_DIREITA") {
      moveToAngles(currentTheta1 + ANGLE_INCREMENT, currentTheta2, currentPhi);
    } else if (cmd == "BRACO_ESQUERDA") {
      moveToAngles(currentTheta1 - ANGLE_INCREMENT, currentTheta2, currentPhi);
    } 
    // Movimentos do antebraço (theta2)
    else if (cmd == "ANTEBRACO_ESQUERDA") {
      moveToAngles(currentTheta1, currentTheta2 + ANGLE_INCREMENT, currentPhi);
    } else if (cmd == "ANTEBRACO_DIREITA") {
      moveToAngles(currentTheta1, currentTheta2 - ANGLE_INCREMENT, currentPhi);
    }
    // Rotação da ferramenta (phi)
    else if (cmd == "GIRA_DIREITA") {
      moveToAngles(currentTheta1, currentTheta2, currentPhi + ANGLE_INCREMENT);
    } else if (cmd == "GIRA_ESQUERDA") {
      moveToAngles(currentTheta1, currentTheta2, currentPhi - ANGLE_INCREMENT);
    }
    // Controle da garra
    else if (cmd == "GARRA_FECHA") {
      gripperServo.write(GARRA_FECHADA);
      Serial.println("Garra: FECHADA");
    } else if (cmd == "GARRA_ABRE") {
      gripperServo.write(GARRA_ABERTA);
      Serial.println("Garra: ABERTA");
    }
    
    // Debug: mostra posição atual
    Serial.print("Pos: θ1="); Serial.print(currentTheta1);
    Serial.print("° θ2="); Serial.print(currentTheta2);
    Serial.print("° φ="); Serial.print(currentPhi);
    Serial.println("°");
  }
  
  // Executa todos os motores
  stepper1.run();
  stepper2.run();
  stepper3.run();
  // stepper4.run(); // Removido
}