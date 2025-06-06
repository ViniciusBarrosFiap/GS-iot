import cv2
import mediapipe as mp
import numpy as np
import time
import csv
import os

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

video = cv2.VideoCapture(0)

# Parâmetros de controle
LIMIAR_ESCURO = 200  # ≥ 200 é escuro
LIMIAR_CLARO = 160   # < 160 é claro
TEMPO_MIN_ESCURO = 3 # seg p/ acionar alerta de luz
TEMPO_MIN_GESTO = 10 # seg p/ acionar alerta por palma aberta

# Estados e variáveis de controle
inicio_escuro = None
inicio_luz = None
alerta_ativo = False
motivo_alerta = None
log_quedas = [] # lista de dicts para gerar CSV depois

# Controle do gesto de palma
gesto_detectado = ""
gesto_confirmado = False
inicio_gesto = None
alerta_gesto_ativo = False

# Função para detectar palma aberta
def detecta_gesto(resultado):
    global gesto_detectado, inicio_gesto, gesto_confirmado
    dedos_levantados = 0

    if resultado.multi_hand_landmarks:
        for hand in resultado.multi_hand_landmarks:
            dedos = hand.landmark
            # Indicador, médio, anelar, mínimo
            if dedos[8].y < dedos[6].y:
                dedos_levantados += 1
            if dedos[12].y < dedos[10].y:
                dedos_levantados += 1
            if dedos[16].y < dedos[14].y:
                dedos_levantados += 1
            if dedos[20].y < dedos[18].y:
                dedos_levantados += 1

            if dedos_levantados >= 4:
                if not gesto_confirmado:
                    inicio_gesto = time.time()
                    gesto_confirmado = True
                else:
                    duracao = time.time() - inicio_gesto
                    if duracao >= TEMPO_MIN_GESTO:
                        return True
            else:
                gesto_confirmado = False
                inicio_gesto = None
    else:
        gesto_confirmado = False
        inicio_gesto = None
    return False

def alerta_visual(frame):
    brilho_frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=50)
    overlay = brilho_frame.copy()
    vermelho = np.full(frame.shape, (0, 0, 150), dtype=np.uint8)
    cv2.addWeighted(vermelho, 0.3, brilho_frame, 0.7, 0, overlay)
    return overlay

def desenhar_texto_centralizado(imagem, texto, fonte=cv2.FONT_HERSHEY_SIMPLEX, escala=1.5, cor=(0, 0, 255), espessura=3):
    texto_tamanho, _ = cv2.getTextSize(texto, fonte, escala, espessura)
    largura_texto, altura_texto = texto_tamanho
    altura_img, largura_img = imagem.shape[:2]
    pos_x = (largura_img - largura_texto) // 2
    pos_y = (altura_img + altura_texto) // 2
    cv2.putText(imagem, texto, (pos_x, pos_y), fonte, escala, cor, espessura, cv2.LINE_AA)

def desenhar_cronometro(imagem, segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    seg = int(segundos % 60)
    tempo_formatado = f"Sem luz: {horas:02}:{minutos:02}:{seg:02}"
    cv2.putText(imagem, tempo_formatado, (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

def registrar_log(motivo, inicio, fim):
    duracao = fim - inicio
    log_quedas.append({
        'motivo': motivo,
        'inicio': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(inicio)),
        'fim': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fim)),
        'duracao_segundos': round(duracao, 2)
    })

def salvar_log_csv():
    if not log_quedas:
        return
    caminho = "log_quedas.csv"
    escrever_cabecalho = not os.path.exists(caminho)
    with open(caminho, 'a', newline='') as csvfile:
        fieldnames = ['motivo', 'inicio', 'fim', 'duracao_segundos']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if escrever_cabecalho:
            writer.writeheader()
        for linha in log_quedas:
            writer.writerow(linha)
    log_quedas.clear() # limpa para evitar duplicidade

while video.isOpened():
    sucesso, frame = video.read()
    if not sucesso:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    color = cv2.cvtColor(eq, cv2.COLOR_GRAY2BGR)
    media_luminosidade = np.mean(gray)
    nivel_escuro = 255 - int(media_luminosidade)

    # Detecta mãos e se o gesto está ativo
    resultado = hands.process(cv2.cvtColor(color, cv2.COLOR_BGR2RGB))
    gesto_palma_ativa = detecta_gesto(resultado)

    # --- ALERTA POR ESCURIDÃO ---
    if nivel_escuro >= LIMIAR_ESCURO:
        inicio_luz = None
        if inicio_escuro is None:
            inicio_escuro = time.time()
        elif not alerta_ativo and (time.time() - inicio_escuro >= TEMPO_MIN_ESCURO):
            alerta_ativo = True
            motivo_alerta = "Escuridão"
            tempo_inicio_alerta = inicio_escuro
            alerta_gesto_ativo = False # Prioriza motivo de escuridão
    # --- ALERTA POR GESTO (PALMA ABERTA) ---
    elif gesto_palma_ativa and not alerta_ativo:
        if not alerta_gesto_ativo:
            tempo_inicio_alerta = inicio_gesto
            alerta_ativo = True
            motivo_alerta = "Palma aberta"
            alerta_gesto_ativo = True
            inicio_escuro = None # reseta escuridão
    # --- DESATIVA ALERTA QUANDO LUZ VOLTA OU MÃO SAI ---
    elif nivel_escuro < LIMIAR_CLARO or (alerta_ativo and alerta_gesto_ativo and not gesto_palma_ativa):
        if alerta_ativo:
            # Registra log quando alerta desativa
            fim_alerta = time.time()
            registrar_log(motivo_alerta, tempo_inicio_alerta, fim_alerta)
            salvar_log_csv()
        alerta_ativo = False
        inicio_escuro = None
        inicio_luz = None
        alerta_gesto_ativo = False

    texto_escuro = f"Escuridao: {nivel_escuro}/255"
    status_luz = "Luz acesa" if nivel_escuro < LIMIAR_CLARO else ("Luz fraca" if nivel_escuro < LIMIAR_ESCURO else "Falta de luz")

    # Mostra landmarks
    if resultado.multi_hand_landmarks:
        for hand in resultado.multi_hand_landmarks:
            mp_draw.draw_landmarks(color, hand, mp_hands.HAND_CONNECTIONS)

    # Alerta visual e cronômetro
    if alerta_ativo:
        color = alerta_visual(color)
        desenhar_texto_centralizado(color, f"ALERTA EMITIDO ({motivo_alerta})", escala=1.5)
        tempo_ativo = time.time() - tempo_inicio_alerta
        desenhar_cronometro(color, tempo_ativo)

    # Interface e status
    cv2.putText(color, texto_escuro, (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 100, 255), 2)
    cv2.putText(color, f"Status: {status_luz}", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 100, 255), 2)
    cv2.imshow("SafeHands - Comunicação em ambientes escuros", color)
    if cv2.waitKey(1) & 0xFF == 27:
        break

video.release()
cv2.destroyAllWindows()
# Salva qualquer log pendente no fechamento
salvar_log_csv()
