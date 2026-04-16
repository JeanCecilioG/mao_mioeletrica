from pyfirmata2 import Arduino, SERVO
import time

# Porta do Arduino
porta = '/dev/cu.usbserial-130'   # ajusta se mudar (porque sempre muda depois de desconectar)

# parâmetros (esses valores podem ser modificados ou ajustados conformes os testes foram demonstrando necessidade)
amostragem_ms   = 100       
intervalo_loop  = 0.05
limiar_bruto    = 0.70     # limiar no sinal EMG bruto (0 a 1)
repeticoes      = 8       # leituras consecutivas acima do limiar para disparar
tempo_pausa     = 2.0      # tempo mínimo entre comandos

print("MÃO ROBÓTICA")

# Codigo para iniciar o Arduino
placa = Arduino(porta)
placa.samplingOn(amostragem_ms)
time.sleep(2)

# Codigo que define cada pino dos servomotores
dedo1 = 10
dedo2 = 9
dedo3 = 8
dedo4 = 7
dedo5 = 6

# Configuração dos servos com estrutura de loop
for p in (dedo1, dedo2, dedo3, dedo4, dedo5):
    placa.digital[p].mode = SERVO

# Funcao que movimenta os dedos
def mover_servo(pino, angulo):
    placa.digital[pino].write(angulo)
    time.sleep(0.02)

# Funcao que retoma a mao para posicao original
def fechar_mao():
    mover_servo(dedo1, 0)
    mover_servo(dedo2, 0)
    mover_servo(dedo3, 90)
    mover_servo(dedo4, 0)
    mover_servo(dedo5, 90)
    time.sleep(0.3)

#Funcao que abre a mao
def abrir_mao():
    mover_servo(dedo1, 90)
    mover_servo(dedo2, 80)
    mover_servo(dedo3, 180)
    mover_servo(dedo4, 90)
    mover_servo(dedo5, 0)
    time.sleep(0.3)

# Um log para acompanhar o processo e corrigir erros durante execução
def log_acao(acao, valor, contagem, t, t_ult):
    horario = time.strftime("%H:%M:%S", time.localtime(t))
    print(
        f"\n[{horario}] {acao} | EMG={valor:.3f} (> {limiar_bruto:.3f}) | "
        f"hits={contagem}/{repeticoes} | "
        f"desde_ultimo={t - t_ult:.2f}s"
    )

emg_valor = [0.0]   # lista só pra poder alterar dentro do callback

# definindo a leitura dos dados do sensor emg
def ler_emg(valor):
    if valor is not None:
        emg_valor[0] = valor

# Configura porta do arduino pro EMG
placa.analog[0].register_callback(ler_emg)
placa.analog[0].enable_reporting()
time.sleep(1.0)

# estado inicial
abrir_mao()
estado_mao = "ABERTA"
ultimo_comando = 0.0
contador = 0

print("Lendo EMG em A0...")

while True:
    valor = emg_valor[0]   # valor vindo do callback
    agora = time.time()

    # valor bruto
    status = f"EMG:{valor:.3f}  "

    # Período refratário para evitar falso positivo com ruídos
    if (agora - ultimo_comando) < tempo_pausa:
        contador = 0
        status += f"⏳ pausa {tempo_pausa - (agora - ultimo_comando):.1f}s [{estado_mao}]"
        print(status.ljust(70), end="\r")
        time.sleep(intervalo_loop)
        continue

    # Detecção de valor bruto acima do limiar
    if valor > limiar_bruto:
        contador += 1
        status += f"detectando {contador}/{repeticoes} [{estado_mao}]"
        if contador >= repeticoes:
            estado_antigo = estado_mao

            if estado_mao == "ABERTA":
                fechar_mao()
                estado_mao = "FECHADA"
                log_acao("FECHAR", valor, contador, agora, ultimo_comando)

                time.sleep(0.7)

                abrir_mao()
                log_acao("ABRIR (auto)", valor, contador, time.time(), ultimo_comando)
                estado_mao = "ABERTA"
            else:
                abrir_mao()
                estado_mao = "ABERTA"
                log_acao("ABRIR", valor, contador, agora, ultimo_comando)

            ultimo_comando = time.time()
            contador = 0
            status = f"comando executado [{estado_mao}]"
    else:
        contador = max(0, contador - 1)
        status += f"abaixo do limiar [{estado_mao}]"

    print(status.ljust(70), end="\r")
    time.sleep(intervalo_loop)
