# Controle SCARA por gesto
import cv2
import mediapipe as mp
import serial
import time

# Configuração
arduino = serial.Serial("COM13", 115200, timeout=1)
camera = cv2.VideoCapture(0)
hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
time.sleep(2)

print("MAO DIREITA ABERTA = Braco Principal Direita | MAO ESQUERDA ABERTA = Braco Principal Esquerda")
print("MAO DIREITA FECHADA = Antebraco Esquerda | MAO ESQUERDA FECHADA = Antebraco Direita | 'q' = Sair")

ultimo_tempo = 0


def mao_fechada(landmarks):
    """Detecta se a mão está fechada baseado na posição dos dedos"""
    # Pontos dos dedos (tip) e articulações (pip)
    # Polegar, indicador, médio, anelar, mindinho
    dedos_tips = [4, 8, 12, 16, 20]
    dedos_pips = [3, 6, 10, 14, 18]

    dedos_fechados = 0

    # Verifica polegar (diferente dos outros dedos)
    if landmarks[4].x < landmarks[3].x:  # Polegar fechado
        dedos_fechados += 1

    # Verifica outros dedos
    for i in range(1, 5):
        if landmarks[dedos_tips[i]].y > landmarks[dedos_pips[i]].y:  # Dedo fechado
            dedos_fechados += 1

    return dedos_fechados >= 4  # Mão fechada se 4 ou mais dedos estão fechados


while True:
    ret, frame = camera.read()
    frame = cv2.flip(frame, 1)
    largura = frame.shape[1]
    centro = largura // 2

    # Detecta mão
    resultado = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if resultado.multi_hand_landmarks and resultado.multi_handedness:
        mao = resultado.multi_hand_landmarks[0]
        info_mao = resultado.multi_handedness[0]

        # Identifica qual mão (Right/Left do ponto de vista da câmera)
        label_mao = info_mao.classification[0].label

        # Verifica se a mão está fechada
        mao_esta_fechada = mao_fechada(mao.landmark)

        # Comando baseado na mão identificada e estado (aberta/fechada)
        if mao_esta_fechada:
            if label_mao == "Right":  # Mão direita fechada
                comando = "ANTEBRACO_DIREITA"
            elif label_mao == "Left":  # Mão esquerda fechada
                comando = "ANTEBRACO_ESQUERDA"
            else:
                comando = ""
        else:
            if label_mao == "Right":  # Mão direita aberta
                comando = "BRACO_DIREITA"
            elif label_mao == "Left":  # Mão esquerda aberta
                comando = "BRACO_ESQUERDA"
            else:
                comando = ""

        # Envia comando (1 por segundo)
        if comando and time.time() - ultimo_tempo > 1:
            arduino.write(f"{comando}\n".encode())
            ultimo_tempo = time.time()
            print(comando)

        # Marca mão na tela
        x_mao = mao.landmark[0].x * largura
        y_mao = mao.landmark[0].y * frame.shape[0]

        # Cor baseada na mão e estado
        if mao_esta_fechada:
            # Magenta=Direita Fechada, Ciano=Esquerda Fechada
            cor = (255, 0, 255) if label_mao == "Right" else (255, 255, 0)
            estado = "Closed"
        else:
            # Verde=Direita Aberta, Vermelho=Esquerda Aberta
            cor = (0, 255, 0) if label_mao == "Right" else (0, 0, 255)
            estado = "Open"

        cv2.circle(frame, (int(x_mao), int(y_mao)), 20, cor, -1)
        texto_mao = f"{label_mao} Hand ({estado})"
        cv2.putText(frame, texto_mao, (int(x_mao), int(y_mao)-30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)

    cv2.imshow('SCARA', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
arduino.close()
