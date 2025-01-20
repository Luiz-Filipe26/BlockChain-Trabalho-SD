import threading
import time
import requests
from blockchain_net_info import main as main_net_info
from blockchain import main as main_blockchain


def start_blockchain_net_info():
    print("Iniciando o blockchain_net_info.py na porta 5260...")
    net_info_thread = threading.Thread(target=main_net_info, args=(5260,))
    net_info_thread.start()


def start_blockchain():
    for port in range(5000, 5003):
        print(f"Iniciando o blockchain.py na porta {port}...")
        blockchain_thread = threading.Thread(target=main_blockchain, args=(port,))
        blockchain_thread.start()


def health_check_nodes(server_url, min_nodes=8, wait_for_first_try=2, wait_for_next_try=0.5, max_tries=20):
    """
    Verifica se o endpoint /nodes já possui pelo menos min_nodes nós registrados.

    :param server_url: URL do servidor a ser verificado.
    :param min_nodes: Número mínimo de nós esperados.
    :param wait_for_first_try: Tempo a ser aguardado antes da primeira tentativa (em segundos).
    :param wait_for_next_try: Intervalo entre as tentativas.
    :param max_tries: Número máximo de tentativas.
    :return: True se a condição for atendida, False caso contrário.
    """
    print(f"Verificando se {server_url} já possui pelo menos {min_nodes} nós registrados...")

    # Aguarda o tempo inicial antes de começar a primeira tentativa
    time.sleep(wait_for_first_try)

    tries = 0

    while tries < max_tries:
        try:
            response = requests.get(f'{server_url}/nodes')
            if response.status_code == 200:
                nodes = response.json().get('nodes', [])
                print(f"Nós registrados: {len(nodes)}")
                if len(nodes) >= min_nodes:
                    print(f"{server_url} possui os nós necessários.")
                    return True
            else:
                print(f"Erro ao acessar {server_url}/nodes: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar {server_url}/nodes: {e}")

        tries += 1
        time.sleep(wait_for_next_try)

    print(f"{server_url} não atingiu os {min_nodes} nós registrados após {max_tries} tentativas.")
    return False


def init_servers():
    start_blockchain_net_info()
    start_blockchain()
    # Verifica se o blockchain_net_info já possui os nós necessários
    health_check_nodes('http://localhost:5260', min_nodes=3, wait_for_first_try=2, wait_for_next_try=1, max_tries=20)


if __name__ == '__main__':
    init_servers()
