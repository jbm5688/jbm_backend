import sys
import time
from stable_api import Avalona

email, senha, tipo_conta, valor_entrada, stop_gain, stop_loss, ativo = sys.argv[1:]
valor_entrada = float(valor_entrada)
stop_gain = float(stop_gain)
stop_loss = float(stop_loss)

api = Avalona()
api.demo = tipo_conta.lower() == "demo"
api.connect(email, senha)
api.save_credentials("credencial_corretor.json", "encript_corretora.key")

total_lucro = 0
operacao = 0

print("IA iniciada. Executando operações...")

while True:
    direcao = "call" if operacao % 2 == 0 else "put"  # lógica temporária
    resultado = api.entrar_ordem(ativo, direcao, valor_entrada)
    operacao += 1

    if resultado == "GAIN":
        total_lucro += valor_entrada
    else:
        total_lucro -= valor_entrada

    print(f"Operação {operacao}: {resultado} | Lucro acumulado: {total_lucro:.2f}")

    if total_lucro >= stop_gain:
        print("STOP GAIN atingido. Encerrando IA.")
        break
    elif abs(total_lucro) >= stop_loss:
        print("STOP LOSS atingido. Encerrando IA.")
        break

    time.sleep(5)