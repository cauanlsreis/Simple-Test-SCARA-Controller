# 🤖 Controle SCARA por Gesto

Este repositório contém um sistema de controle de um robô SCARA usando gestos da mão detectados pela webcam. O projeto integra um cliente Python (detecção de mãos e lógica de gestos) com um firmware Arduino que comanda motores de passo e uma garra.

Conteúdo principal
- `controle.py` — Cliente Python que usa OpenCV + MediaPipe para detectar gestos na webcam, classificar gestos e enviar comandos via serial para o Arduino.
- `scara/scara.ino` — Firmware Arduino (versão simplificada) que recebe comandos via serial e move os motores de passo (AccelStepper) e o servo da garra.
- `SCARA_Robot.ino` — Implementação referência (mais completa) com homing, armazenamento de trajetórias e controle de garra.

Resumo do funcionamento
- A câmera captura frames; MediaPipe Hands extrai landmarks da mão.
- O Python classifica gestos (mão aberta, punho fechado, gesto de pinça, gesto de rotação) e controla prioridades:
   1. Gesto de garra (pinça: polegar + indicador) — fecha/abre garra com base na distância entre pontas.
   2. Gesto de rotação (indicador + médio) — gira a ferramenta (phi).
   3. Mão aberta (3+ dedos) — move o braço principal (θ1).
   4. Mão fechada (punho) — move o antebraço (θ2).

Bibliotecas e dependências

Python (cliente):
- OpenCV (cv2) — captura de vídeo e desenho na imagem.
- MediaPipe — detecção de landmarks da mão.
- pyserial — comunicação serial com o Arduino.

Arduino (firmware):
- AccelStepper — controle de motores de passo.
- Servo (builtin) — controle do servo da garra.

Instalação e execução (passos locais)

1) Criar um venv com Python 3.10 (exemplo no Windows PowerShell):

```powershell
# Cria venv com a instalação 3.10 (supondo python 3.10 no PATH)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

2) Ajustes na porta serial
- Por padrão o `controle.py` abre `COM13`. Edite `controle.py` se a sua placa estiver em outra porta.

3) Carregar firmware no Arduino
- Abra `scara/scara.ino` no Arduino IDE e instale a biblioteca `AccelStepper` (Library Manager). Selecionar a placa (Arduino Due, etc.) e a porta COM correta. Carregue o sketch.

4) Rodar o cliente Python

```powershell
# Ative o venv e execute
.\.venv\Scripts\Activate.ps1
python controle.py
```

Design e lógica técnica

1) Cinemática inversa (visão geral)

O robô SCARA tem dois elos (L1, L2). Dado um ponto alvo (x,y) no plano da base, as articulações θ1 e θ2 são calculadas pela cinemática inversa padrão:

\[ r = \sqrt{x^2 + y^2} \]
\[ \cos(\theta_2) = \frac{r^2 - L1^2 - L2^2}{2 L1 L2} \]
\[ \theta_2 = \operatorname{atan2}(\pm\sqrt{1 - \cos^2(\theta_2)}, \cos(\theta_2)) \]
\[ \theta_1 = \operatorname{atan2}(y, x) - \operatorname{atan2}(L2 \sin(\theta_2), L1 + L2 \cos(\theta_2)) \]

Essas equações retornam possíveis soluções (configurações "cotovelo para cima/baixo"). No firmware simplificado usamos valores angulares já calculados pelo cliente ou acumulados por incrementos; na versão referência (`SCARA_Robot.ino`) há rotinas mais completas que fazem parsing de trajetórias.

2) Controle da garra por distância euclidiana

- Para detectar o gesto de pinça, o cliente mede a distância normalizada entre a ponta do polegar (landmark 4) e a ponta do indicador (landmark 8) usando a fórmula da distância euclidiana 2D em coordenadas normalizadas (x,y) retornadas pelo MediaPipe:

\[ d = \sqrt{(x_4 - x_8)^2 + (y_4 - y_8)^2} \]

- Thresholds usados (são empíricos e podem ser ajustados):
   - `d < 0.04` → comando de fechamento (FECHA)
   - `d > 0.12` → comando de abertura (ABRE)
   - `0.04 <= d <= 0.12` → zona neutra (nenhuma ação)

- O cliente mantém um estado da garra (ABERTA / FECHADA) e só envia o comando de mudança de estado se:
   - o gesto de pinça apropriado for detectado (polegar+indicador levantados e outros dedos fechados), e
   - o novo estado for diferente do estado atual, e
   - passou um pequeno intervalo (ex.: 2 s) desde o último comando — isso evita alternância por ruído.

Mapeamento de gestos (padrão atual)

- Pinça (polegar + indicador): abre/fecha garra (manter estado até gesto oposto)
- Rotação (indicador + médio): gira a ferramenta (phi)
- Mão aberta (3+ dedos): move braço principal (θ1)
- Mão fechada (punho): move antebraço (θ2)
