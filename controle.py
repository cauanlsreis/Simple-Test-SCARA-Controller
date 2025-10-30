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
print("INDICADOR + MEDIO = Gira Direita/Esquerda")
print("GARRA (Polegar + Indicador): PROXIMOS = Fecha | DISTANTES = Abre | 'q' = Sair")

ultimo_tempo = 0

# Estado da garra (para evitar comandos repetidos)
estado_garra_atual = "ABERTA"  # "ABERTA" ou "FECHADA"
ultimo_comando_garra = ""
tempo_ultimo_comando_garra = 0


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

    # RIGOROSO: Mão fechada apenas se TODOS os 5 dedos estão fechados
    # E não é um gesto de pinça (que tem polegar + indicador levantados)
    polegar_levantado = landmarks[4].x > landmarks[3].x
    indicador_levantado = landmarks[8].y < landmarks[6].y

    # Se polegar e indicador estão levantados, não é mão fechada (pode ser pinça)
    if polegar_levantado and indicador_levantado:
        return False

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


def distancia_euclidiana(ponto1, ponto2):
    """Calcula a distância euclidiana entre dois pontos"""
    return ((ponto1.x - ponto2.x) ** 2 + (ponto1.y - ponto2.y) ** 2) ** 0.5


def detectar_gesto_rotacao(landmarks):
    """
    Detecta gesto de rotação: indicador e médio levantados, outros fechados
    Retorna True se o gesto for detectado
    """
    # Verifica se indicador (8) e médio (12) estão levantados
    indicador_levantado = landmarks[8].y < landmarks[6].y
    medio_levantado = landmarks[12].y < landmarks[10].y

    # Verifica se polegar, anelar e mindinho estão fechados
    polegar_fechado = landmarks[4].x < landmarks[3].x
    anelar_fechado = landmarks[16].y > landmarks[14].y
    mindinho_fechado = landmarks[20].y > landmarks[18].y

    # Gesto de rotação: indicador + médio levantados, outros fechados
    return (indicador_levantado and medio_levantado and
            polegar_fechado and anelar_fechado and mindinho_fechado)


def detectar_gesto_pinca(landmarks):
    """
    Detecta gesto de pinça: polegar e indicador próximos, outros dedos fechados
    Retorna: 'FECHA', 'ABRE' ou None
    """
    # Distância entre polegar (4) e indicador (8)
    dist_pinca = distancia_euclidiana(landmarks[4], landmarks[8])

    # Verifica se polegar e indicador estão levantados
    polegar_levantado = landmarks[4].x > landmarks[3].x
    indicador_levantado = landmarks[8].y < landmarks[6].y

    # Verifica se os outros dedos (médio, anelar, mindinho) estão fechados
    medio_fechado = landmarks[12].y > landmarks[10].y
    anelar_fechado = landmarks[16].y > landmarks[14].y
    mindinho_fechado = landmarks[20].y > landmarks[18].y

    # CONDIÇÕES para gesto de pinça:
    # 1. Polegar E indicador levantados
    # 2. Outros 3 dedos fechados
    if (polegar_levantado and indicador_levantado and
            medio_fechado and anelar_fechado and mindinho_fechado):
        if dist_pinca < 0.04:  # Dedos bem próximos = comando para fechar
            return 'FECHA'
        elif dist_pinca > 0.12:  # Dedos bem distantes = comando para abrir
            return 'ABRE'

    return None  # Sem comando (zona neutra ou não é pinça)


while True:
    ret, frame = camera.read()
    frame = cv2.flip(frame, 1)
    largura = frame.shape[1]
    centro = largura // 2    # Detecta mão
    resultado = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if resultado.multi_hand_landmarks and resultado.multi_handedness:
        mao = resultado.multi_hand_landmarks[0]
        info_mao = resultado.multi_handedness[0]

        # Identifica qual mão (Right/Left do ponto de vista da câmera)
        label_mao = info_mao.classification[0].label

        # Verifica gestos específicos
        mao_esta_fechada = mao_fechada(mao.landmark)
        dedos_levantados = contar_dedos_levantados(mao.landmark)
        gesto_pinca = detectar_gesto_pinca(mao.landmark)
        gesto_rotacao = detectar_gesto_rotacao(mao.landmark)

        # Debug temporário
        print(
            f"Debug: {label_mao} - Dedos: {dedos_levantados}, Fechada: {mao_esta_fechada}, Garra: {gesto_pinca}, Rotacao: {gesto_rotacao}")

        comando = ""

        # Comando baseado na mão identificada e estado - PRIORIDADES CORRIGIDAS
        # PRIORIDADE 1: Gesto de pinça (mais específico) com controle de estado
        if gesto_pinca:
            # Só envia comando se for diferente do estado atual e com intervalo mínimo
            if (gesto_pinca == 'FECHA' and estado_garra_atual == "ABERTA" and
                    time.time() - tempo_ultimo_comando_garra > 2):
                comando = "GARRA_FECHA"
                estado_garra_atual = "FECHADA"
                ultimo_comando_garra = comando
                tempo_ultimo_comando_garra = time.time()

            elif (gesto_pinca == 'ABRE' and estado_garra_atual == "FECHADA" and
                  time.time() - tempo_ultimo_comando_garra > 2):
                comando = "GARRA_ABRE"
                estado_garra_atual = "ABERTA"
                ultimo_comando_garra = comando
                tempo_ultimo_comando_garra = time.time()

        # PRIORIDADE 2: Gesto de rotação (indicador + médio)
        elif gesto_rotacao:
            if label_mao == "Right":
                comando = "GIRA_DIREITA"
            elif label_mao == "Left":
                comando = "GIRA_ESQUERDA"

        # PRIORIDADE 3: Mão aberta (3+ dedos) = braço principal
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
        if gesto_pinca:
            cor = (0, 255, 255)  # Ciano para gesto de pinça
            estado = f"Garra ({gesto_pinca}) - Estado: {estado_garra_atual}"
        elif gesto_rotacao:
            cor = (255, 0, 255)  # Magenta para rotação
            estado = f"Rotacao ({comando})"
        elif dedos_levantados >= 3:
            cor = (0, 255, 0) if label_mao == "Right" else (0, 0, 255)
            estado = f"Open ({dedos_levantados} fingers)"
        elif mao_esta_fechada:
            cor = (255, 0, 255) if label_mao == "Right" else (255, 255, 0)
            estado = "Closed"
        else:
            cor = (128, 128, 128)  # Cinza para neutro
            estado = f"Neutro ({dedos_levantados} fingers)"

        texto_mao = f"{label_mao} Hand ({estado})"
        cv2.putText(frame, texto_mao, (int(x_mao), int(y_mao)-30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)

        # Mostra distancia da garra e estado da garra para debug
        dist_pinca = distancia_euclidiana(mao.landmark[4], mao.landmark[8])
        cv2.putText(frame, f"Dist Garra: {dist_pinca:.3f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Garra: {estado_garra_atual}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if estado_garra_atual == "ABERTA" else (0, 0, 255), 2)

    cv2.imshow('SCARA', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
arduino.close()
