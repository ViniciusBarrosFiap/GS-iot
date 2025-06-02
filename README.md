
# Detecção de Gestos e Monitoramento de Falta de Luz com Python e MediaPipe

##  Autor

**RM97824 - Vinicius Oliveira de Barros** 
**RM97937 - Pedro Henrique Fernandes Lô de Barros**  


Um sistema inteligente criado em Python que utiliza a biblioteca [MediaPipe](https://mediapipe.dev/) para detectar gestos com as mãos e monitorar automaticamente quedas de luz em ambientes fechados. 

O objetivo é oferecer uma solução de **acessibilidade e segurança** em situações de emergência, como apagões, auxiliando tanto em ambientes hospitalares quanto residenciais ou corporativos.

## Funcionalidades

-  **Detecção de gestos com as mãos** (ex: palma aberta, dedo indicador levantado)
-  **Monitoramento de luminosidade ambiente** em tempo real
-  **Ativação automática de alerta visual** após alguns segundos de escuridão
-  **Cronômetro mostrando duração da falta de luz** (formato HH:mm:ss)
-  **Desativação inteligente do alerta** após tempo mínimo com a luz restaurada
-  **Ajuste dinâmico de sensibilidade de luminosidade** baseado no seu ambiente
-  **Efeito visual com brilho e sobreposição vermelha** durante o alerta

##  Tecnologias utilizadas

- [Python 3.10+](https://www.python.org/)
- [MediaPipe (Hands)](https://google.github.io/mediapipe/solutions/hands.html)
- [OpenCV](https://opencv.org/)
- `NumPy` e `time` para cálculos e controle temporal

## Instalação

1. **Clone o repositório**:

git clone https://github.com/seu-usuario/safehands-mediapipe.git
cd safehands-mediapipe


2. **Crie um ambiente virtual (opcional, mas recomendado)**:

python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows


3. **Instale as dependências**:

pip install -r requirements.txt


## Como executar

Execute o arquivo principal:


python main.py


A webcam será ativada automaticamente.

##  Parâmetros personalizáveis

Você pode ajustar no código:

| Variável                  | Descrição                                                | Valor sugerido |
|---------------------------|------------------------------------------------------------|----------------|
| `LIMIAR_ESCURO`           | Nível mínimo para considerar ambiente escuro               | `200`          |
| `LIMIAR_CLARO`            | Nível máximo para considerar ambiente claro                | `160`          |
| `TEMPO_MIN_ESCURO`        | Tempo em segundos para disparar o alerta após escurecer    | `3`            |
| `TEMPO_DESATIVAR_ALERTA`  | Tempo em segundos para desativar o alerta após clarear     | `3`            |

##  Casos de uso

- **Ambientes hospitalares**: detectar falhas de energia e ativar alertas visuais
- **Acessibilidade**: para pessoas com deficiência visual, usando gestos simples para pedir ajuda
- **Casas e escritórios**: monitoramento de queda de energia
- **Centros de comando**: exibição clara do tempo sem luz e reforço visual de alerta

##  Estrutura do Projeto


safehands/
├── main.py               # Código principal da aplicação
├── requirements.txt      # Bibliotecas necessárias
├── README.md             # Este arquivo



