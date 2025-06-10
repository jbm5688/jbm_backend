# Simulação da classe Avalona, substitua com sua implementação real
class Avalona:
    def __init__(self):
        self.demo = True
    def connect(self, email, senha):
        print(f"Conectando como {email} no modo {'demo' if self.demo else 'real'}")
    def save_credentials(self, cred_path, key_path):
        print("Credenciais salvas")
    def entrar_ordem(self, ativo, direcao, valor):
        from random import choice
        return choice(["GAIN", "LOSS"])