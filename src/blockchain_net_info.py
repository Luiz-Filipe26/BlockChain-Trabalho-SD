import re
import requests
from flask import Flask, jsonify, request
from argparse import ArgumentParser

app = Flask(__name__)

# Conjunto global de nós registrados
nodes = set()

# Regex para validar o formato de um endereço de nó (URL)
url_pattern = re.compile(r'^(http://)?([a-zA-Z0-9.-]+)(:\d+)?$')


def notify_new_blockchain(registered_node=None):
    """
    Notifica todos os nós registrados sobre a nova blockchain, exceto o nó registrado.

    :param registered_node: O nó que será ignorado na notificação
    :return: Nenhum valor, apenas envia as notificações
    """
    # print(f"Iniciando a notificação para todos os {len(nodes)} nós registrados.")

    for node in nodes.copy():
        # Ignora o nó registrado
        if node == registered_node:
            # print(f"Ignorando o nó {node} na notificação.")
            continue

        try:
            response = requests.post(f'{node}/nodes/new_blockchain')
            if response.status_code == 200:
                # print(f'Notificação enviada para {node}')
                pass
            else:
                print(f'Falha ao notificar {node}. Status: {response.status_code}')
        except requests.exceptions.RequestException as e:
            print(f'Erro ao tentar notificar {node}: {e}')

    # print("Notificação enviada para todos os nós (exceto o nó registrado).")


@app.route('/nodes/register', methods=['POST'])
def register_node():
    """
    Registra um novo nó na rede.

    :return: Resposta indicando o sucesso ou erro no registro
    """
    values = request.get_json()
    address = values.get('address')  # O endereço do nó

    print(f"Recebido endereço para registro: {address}")

    if not address:
        print("Erro: O endereço não foi fornecido")
        return 'Erro: O endereço é necessário', 400

    # Verifica se o formato do endereço está correto usando regex
    match = url_pattern.match(address)
    if not match:
        print(f"Erro: O formato do endereço '{address}' é inválido")
        return 'Erro: O formato do endereço é inválido', 400

    # Garante que o endereço tenha o prefixo 'http://'
    if not address.startswith('http://'):
        address = f'http://{address}'
        print(f"Prefixo 'http://' adicionado ao endereço: {address}")

    # Verifica se a porta foi especificada, caso contrário, usa a porta padrão
    if not match.group(3):
        address = f"{address}:5260"  # Porta padrão
        print(f"Porta padrão 5260 adicionada ao endereço: {address}")

    nodes.add(address)
    print(f"Nó {address} registrado com sucesso. Total de nós: {len(nodes)}")

    # Chama a função de notificação após o registro, ignorando o nó registrado
    notify_new_blockchain(address)

    return jsonify({
        'message': f'Nó {address} registrado com sucesso.',
        'total_nodes': list(nodes)
    }), 201


@app.route('/nodes', methods=['GET'])
def get_nodes():
    """
    Retorna todos os nós registrados na rede.

    :return: Lista de nós registrados
    """
    print(f"Requisitado a lista de nós. Total de nós registrados: {len(nodes)}")
    return jsonify({'nodes': list(nodes)}), 200


def main(port):
    """
    Função principal que inicia o servidor Flask na porta fornecida.

    :param port: Porta onde o servidor irá escutar.
    """
    print(f"Servidor iniciado na porta {port}")
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5260, type=int, help='Porta para o servidor')
    args = parser.parse_args()
    main(args.port)
