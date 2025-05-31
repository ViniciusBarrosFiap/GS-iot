import cv2
import mediapipe as mp
import pyttsx3
import numpy as np
import time
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7, 
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

video = cv2.VideoCapture(0)

gesto_detectado = ""
tempo_ultimo_gesto = 0
TEMPO_GESTO = 5

TEMPO_MIN_GESTO = 10
inicio_gesto = 0
gesto_confirmado = False

LIMIAR_ESCURO = 200           # ≥ 200 é escuro
LIMIAR_CLARO = 160            # < 160 é claro
TEMPO_MIN_ESCURO = 3          # segundos para acionar alerta

inicio_escuro = None
alerta_ativo = False

#Função para detectar movimentos com as mãos
def detecta_gesto(resultado):
    global gesto_detectado, inicio_gesto,gesto_confirmado, tempo_ultimo_gesto
    if resultado.multi_hand_landmarks:
        for hand in resultado.multi_hand_landmarks:
            dedos = hand.landmark
            
            dedos_levantados = 0
            if dedos[8].y < dedos[6].y: #Indicador
                dedos_levantados += 1
            if dedos[12].y < dedos[10].y: #Médio
                dedos_levantados += 1
            if dedos[16].y < dedos[14].y: #Anelar
                dedos_levantados += 1
            if dedos[20].y < dedos[18].y: #Mínimo
                dedos_levantados += 1
            
            if dedos_levantados >= 4:
                if not gesto_confirmado:
                    inicio_gesto = time.time()
                    gesto_confirmado = True
                else:
                    duracao = time.time() - inicio_gesto
                    if duracao >= TEMPO_MIN_GESTO:
                        gesto_detectado = "palma detectada"
                        tempo_ultimo_gesto = time.time()
                        gesto_confirmado = False
            
            else:
                gesto_confirmado = False      
    else:
        gesto_confirmado = False

def alerta_visual(frame):
    brilho_frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=50)
    
    #Alerta vermelho na tela
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
    
while video.isOpened():
    sucess, frame = video.read()
    if not sucess:
        break
    
    #Melhora a visibilidade em ambientes escuros
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    color = cv2.cvtColor(eq, cv2.COLOR_GRAY2BGR)
    
    media_luminosidade = np.mean(gray)
    nivel_escuro = 255 - int(media_luminosidade) #Quanto menor o brilho mais escuro
    
    # Lógica de ativação e desativação do alerta por luminosidade
    if nivel_escuro >= LIMIAR_ESCURO:
        inicio_luz = None
        if inicio_escuro is None:
            inicio_escuro = time.time()
        elif not alerta_ativo and (time.time() - inicio_escuro >= TEMPO_MIN_ESCURO):
            alerta_ativo = True
    
    # Desativação do alerta (após tempo contínuo com luz clara)
    elif nivel_escuro < LIMIAR_CLARO:
        inicio_escuro = None  # reseta tempo de escuridão
        if alerta_ativo:
            if inicio_luz is None:
                inicio_luz = time.time()
            elif time.time() - inicio_luz >= 2:
                alerta_ativo = False
                inicio_luz = None
    else:
    # zona intermediária: não altera estados, apenas zera tempos se necessário
        inicio_escuro = None
        inicio_luz = None
    texto_escuro = f"Escuridao: {nivel_escuro}/255"
    
    #Detecta mãos
    resultado = hands.process(cv2.cvtColor(color, cv2.COLOR_BGR2RGB))
    detecta_gesto(resultado)
    
    #Mostra landmarks
    if resultado.multi_hand_landmarks:
        for hand in resultado.multi_hand_landmarks:
            mp_draw.draw_landmarks(color, hand, mp_hands.HAND_CONNECTIONS)
    
    if alerta_ativo:
        color = alerta_visual(color)
        desenhar_texto_centralizado(color, "ALERTA EMITIDO", escala=2.0)
        if inicio_escuro is not None:
            tempo_escuro = time.time() - inicio_escuro
            desenhar_cronometro(color, tempo_escuro)
        cv2.putText(color, gesto_detectado, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255, 0), 2)
    
    cv2.putText(color, texto_escuro, (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 100, 255), 2)
    status_luz = "Luz acesa" if nivel_escuro < LIMIAR_CLARO else ("Luz fraca" if nivel_escuro < LIMIAR_ESCURO else "Falta de luz")
    cv2.putText(color, f"Status: {status_luz}", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 100, 255), 2)
    cv2.imshow("SafeHands - Comunicação em ambientes escuros", color)
    if cv2.waitKey(1) & 0xFF == 27: #ESC fecha o programa
        break

video.release()
cv2.destroyAllWindows()