/*
 * Teste Simples do Servo da Garra (Gripper)
 * Baseado nas conexões do projeto SCARA de HowToMechatronics
 */

#include <Servo.h>

// Definição do pino de controle do servo da garra
// Conforme o código original do SCARA, o servo é anexado ao pino A0.
#define PINO_SERVO_GARRA A0

// Cria o objeto Servo
Servo gripperServo;

// Variáveis para as posições de abertura e fechamento
const int POSICAO_ABERTA = 180; // Posição para garra aberta (ajuste se necessário)
const int POSICAO_FECHADA = 0;   // Posição para garra fechada (ajuste se necessário)
const int TEMPO_ESPERA = 1500;   // Tempo de espera entre os movimentos (em milissegundos)

void setup() {
  // Inicializa a comunicação serial para debug (opcional)
  Serial.begin(9600);
  Serial.println("Teste da Garra Servo Iniciado");

  // Anexa o objeto servo ao pino de controle
  // Os valores 600 e 2500 são os pulsos min/max do código original, garantindo a calibração correta.
  gripperServo.attach(PINO_SERVO_GARRA, 600, 2500);

  // Posição inicial: Garra aberta
  gripperServo.write(POSICAO_ABERTA);
  Serial.print("Garra em ");
  Serial.print(POSICAO_ABERTA);
  Serial.println(" graus (Aberta)");
  delay(TEMPO_ESPERA);
}

void loop() {
  // 1. Fecha a garra
  gripperServo.write(POSICAO_FECHADA);
  Serial.print("Garra em ");
  Serial.print(POSICAO_FECHADA);
  Serial.println(" graus (Fechada)");
  delay(TEMPO_ESPERA); // Espera 1.5 segundos

  // 2. Abre a garra
  gripperServo.write(POSICAO_ABERTA);
  Serial.print("Garra em ");
  Serial.print(POSICAO_ABERTA);
  Serial.println(" graus (Aberta)");
  delay(TEMPO_ESPERA); // Espera 1.5 segundos
}