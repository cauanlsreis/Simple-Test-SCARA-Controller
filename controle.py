# Controle SCARA por gesto
import cv2
import mediapipe as mp
import serial
import time

# Configuração
arduino = serial.Serial("COM13", 115200, timeout=1)
camera = cv2.VideoCapture(0)
hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
time.sleep(2)

print("MAO DIREITA ABERTA = Braco Principal Direita | MAO ESQUERDA ABERTA = Braco Principal Esquerda")
print("MAO DIREITA FECHADA = Antebraco Direita | MAO ESQUERDA FECHADA = Antebraco Esquerda")
print("1 DEDO DIREITA = Sobe Z | 1 DEDO ESQUERDA = Desce Z")
print("2 DEDOS DIREITA = Gira Direita | 2 DEDOS ESQUERDA = Gira Esquerda | 'q' = Sair")

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

    # CORREÇÃO: Mão fechada apenas se TODOS os 5 dedos estão fechados
    # Isso evita conflito com 1 ou 2 dedos levantados
    return dedos_fechados == 5


def contar_dedos_levantados(landmarks):
    """Conta quantos dedos estão levantados"""
    dedos_tips = [4, 8, 12, 16,
                  20]  # Polegar, indicador, médio, anelar, mindinho
    dedos_pips = [3, 6, 10, 14, 18]

    dedos_levantados = 0

    # Verifica polegar (diferente dos outros dedos)
    if landmarks[4].x > landmarks[3].x:  # Polegar levantado
        dedos_levantados += 1

    # Verifica outros dedos
    for i in range(1, 5):
        if landmarks[dedos_tips[i]].y < landmarks[dedos_pips[i]].y:  # Dedo levantado
            dedos_levantados += 1

    return dedos_levantados


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
        dedos_levantados = contar_dedos_levantados(mao.landmark)

        # Debug temporário
        print(
            f"Debug: {label_mao} - Dedos: {dedos_levantados}, Fechada: {mao_esta_fechada}")

        # Comando baseado na mão identificada e estado - PRIORIDADES CORRIGIDAS
        # PRIORIDADE 1: Comandos específicos de dedos (evita conflito com mão fechada)
        if dedos_levantados == 1:  # 1 dedo = controle Z
            if label_mao == "Right":  # Mão direita com 1 dedo
                comando = "SOBE_Z"
            elif label_mao == "Left":  # Mão esquerda com 1 dedo
                comando = "DESCE_Z"
            else:
                comando = ""
        elif dedos_levantados == 2:  # 2 dedos = rotação garra
            if label_mao == "Right":  # Mão direita com 2 dedos
                comando = "GIRA_DIREITA"
            elif label_mao == "Left":  # Mão esquerda com 2 dedos
                comando = "GIRA_ESQUERDA"
            else:
                comando = ""
        # PRIORIDADE 2: Mão aberta (3+ dedos) = braço principal
        elif dedos_levantados >= 3:
            if label_mao == "Right":  # Mão direita aberta
                comando = "BRACO_DIREITA"
            elif label_mao == "Left":  # Mão esquerda aberta
                comando = "BRACO_ESQUERDA"
            else:
                comando = ""
        # PRIORIDADE 3: Mão fechada (todos os dedos) = antebraço
        elif mao_esta_fechada:  # Punho fechado = antebraço
            if label_mao == "Right":  # Mão direita fechada
                comando = "ANTEBRACO_DIREITA"
            elif label_mao == "Left":  # Mão esquerda fechada
                comando = "ANTEBRACO_ESQUERDA"
            else:
                comando = ""
        else:
            comando = ""

        # Envia comando (1 por segundo)
        if comando and time.time() - ultimo_tempo > 1:
            arduino.write(f"{comando}\n".encode())
            ultimo_tempo = time.time()
            print(comando)

        # Desenha landmarks e conexões da mão
        mp_drawing.draw_landmarks(frame, mao, mp_hands.HAND_CONNECTIONS,
                                  mp_drawing.DrawingSpec(
                                      color=(64, 64, 64), thickness=2, circle_radius=4),
                                  mp_drawing.DrawingSpec(color=(0, 0, 0), thickness=3))

        # Indica posição central do polegar (usado antes para texto)
        x_mao = mao.landmark[0].x * largura
        y_mao = mao.landmark[0].y * frame.shape[0]
        # Cor baseada na mão e estado (apenas para o texto)
        if dedos_levantados == 1:
            cor = (0, 255, 255)  # Ciano para 1 dedo (Z)
            estado = f"1 Finger ({comando})"
        elif dedos_levantados == 2:
            cor = (255, 0, 255)  # Magenta para 2 dedos (Rotação)
            estado = f"2 Fingers ({comando})"
        elif mao_esta_fechada:
            cor = (255, 0, 255) if label_mao == "Right" else (255, 255, 0)
            estado = "Closed"
        else:
            cor = (0, 255, 0) if label_mao == "Right" else (0, 0, 255)
            estado = f"Open ({dedos_levantados} fingers)"

        texto_mao = f"{label_mao} Hand ({estado})"
        cv2.putText(frame, texto_mao, (int(x_mao), int(y_mao)-30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)

    cv2.imshow('SCARA', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
arduino.close()
