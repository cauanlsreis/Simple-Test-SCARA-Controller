# Controle SCARA por gesto
import cv2
import mediapipe as mp
import serial
import time

# Configuração
arduino = serial.Serial("COM3", 115200, timeout=1)
camera = cv2.VideoCapture(0)
hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
time.sleep(2)

print("👈 ESQUERDA = Anti-horário | 👉 DIREITA = Horário | 'q' = Sair")

ultimo_tempo = 0

while True:
    ret, frame = camera.read()
    frame = cv2.flip(frame, 1)
    largura = frame.shape[1]
    centro = largura // 2

    # Detecta mão
    resultado = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if resultado.multi_hand_landmarks:
        mao = resultado.multi_hand_landmarks[0]
        x_mao = mao.landmark[0].x * largura

        # Comando baseado na posição
        if x_mao < centro - 100:
            comando = "ESQUERDA"
        elif x_mao > centro + 100:
            comando = "DIREITA"
        else:
            comando = ""

        # Envia comando (1 por segundo)
        if comando and time.time() - ultimo_tempo > 1:
            arduino.write(f"{comando}\n".encode())
            ultimo_tempo = time.time()
            print(f"🤖 {comando}")

        # Marca mão na tela
        y_mao = mao.landmark[0].y * frame.shape[0]
        cv2.circle(frame, (int(x_mao), int(y_mao)), 20, (0, 255, 255), -1)

    cv2.imshow('SCARA', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
arduino.close()
