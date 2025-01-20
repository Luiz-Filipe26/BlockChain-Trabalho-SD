import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request
from argparse import ArgumentParser


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. E.g. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def last_valid_block_index(self, chain):
        """
        Retorna o índice do último bloco válido na cadeia.

        :param chain: A blockchain
        :return: O índice do último bloco válido
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Verifica se o bloco é válido
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash or not self.valid_proof(last_block['proof'], block['proof'],
                                                                                 last_block_hash):
                return current_index - 1  # Retorna o índice do último bloco válido

            last_block = block
            current_index += 1

        return len(chain) - 1  # Retorna o índice do último bloco se toda a cadeia for válida

    def valid_chain(self, chain):
        """
        Verifica se a blockchain é válida.

        :param chain: A blockchain
        :return: True se a cadeia for válida, False caso contrário
        """
        last_valid_index = self.last_valid_block_index(chain)
        return last_valid_index == len(chain) - 1

    def resolve_conflicts(self):
        """
        Algoritmo de consenso que resolve conflitos substituindo nossa blockchain
        pela blockchain válida mais longa que contenha o bloco de consenso (hash mais votada e mais recente).
        Caso não haja blockchains válidas externas, utiliza a maior cadeia válida localmente.

        :return: True se nossa cadeia foi substituída, False caso contrário.
        """
        neighbours = self.nodes
        valid_hashes = {}
        all_chains = [self.chain]  # Adiciona a própria cadeia no início

        # Coleta todas as blockchains dos nós vizinhos
        for node in neighbours:
            try:
                response = requests.get(f'{node}/chain')
                if response.status_code == 200:
                    chain = response.json()['chain']
                    all_chains.append(chain)
            except Exception as e:
                print(f"Erro ao conectar com {node}: {e}")

        # Filtra apenas blockchains válidas
        valid_chains = [chain for chain in all_chains if self.valid_chain(chain)]

        if not valid_chains:
            # Nenhuma blockchain válida, escolhe a maior entre as válidas localmente
            longest_chain = max(all_chains, key=lambda current_chain: self.last_valid_block_index(current_chain))

            # Obtém o índice do último bloco válido
            last_valid_index = self.last_valid_block_index(longest_chain)

            # Corta a cadeia para incluir apenas os blocos válidos
            self.chain = longest_chain[:last_valid_index + 1]

            return True

        # Processar apenas blockchains válidas
        for chain in valid_chains:
            chain_hashes = [self.hash(block) for block in chain]

            # Armazena relação de hashes para votos e posição
            for index, hash_value in enumerate(chain_hashes):
                if hash_value not in valid_hashes:
                    valid_hashes[hash_value] = {"votes": 1, "position": index}
                else:
                    valid_hashes[hash_value]["votes"] += 1

        # Encontrar a hash com mais votos e maior posição
        most_valid_hash = max(
            valid_hashes.items(),
            key=lambda item: (item[1]["votes"], item[1]["position"])
        )[0]

        print(f"Hash mais validada: {most_valid_hash} com {valid_hashes[most_valid_hash]['votes']} votos.")

        # Encontrar todas as blockchains que contêm o bloco de consenso
        consensus_chains = [
            chain for chain in valid_chains
            if most_valid_hash in [self.hash(block) for block in chain]
        ]

        # Escolher a blockchain mais longa
        new_chain = max(consensus_chains, key=lambda current_chain: (len(current_chain), self.hash(current_chain[-1])))

        # Verificar se a cadeia deve ser substituída
        if len(self.chain) != len(new_chain) or self.hash(self.chain[-1]) != self.hash(new_chain[-1]):
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.

        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

# The adress where the program receives requests
my_node_address = None


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def resolve():
    """
    Resolve conflitos apenas na blockchain atual.
    """
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


@app.route('/nodes/resolve_net', methods=['GET'])
def resolve_net():
    """
    Resolve conflitos nas blockchains de todos os nós vizinhos,
    sem afetar a blockchain atual.
    """
    for node in blockchain.nodes:
        try:
            response = requests.get(f'{node}/nodes/resolve')
            if response.status_code == 200:
                print(f"Conflitos resolvidos no nó {node}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao tentar resolver conflitos no nó {node}: {e}")

    response = {
        'message': 'Attempted to resolve conflicts on neighboring nodes'
    }

    return jsonify(response), 200


@app.route('/nodes/new_blockchain', methods=['POST'])
def new_blockchain():
    """
    Endpoint chamado quando um novo blockchain é anunciado. Busca os nós registrados.
    """
    try:
        # Usando o get_nodes para obter a lista de nós, removendo o próprio
        blockchain.nodes = get_nodes(my_node_address)
        # print(f"Nó atualizado com nova lista de nós: {blockchain.nodes}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar buscar nós: {e}")
        return "Erro ao buscar nós", 500

    return jsonify({
        'message': 'Blockchain e lista de nós atualizados com sucesso',
        'total_nodes': list(blockchain.nodes),
    }), 200


def get_nodes(node_address):
    response = requests.get('http://localhost:5260/nodes')
    if response.status_code == 200:
        nodes = response.json().get('nodes', [])
        # Remove o próprio nó da lista de nós
        nodes = [node for node in nodes if node != node_address]
        blockchain.nodes = set(nodes)
        # print(f"Lista de nós registrados obtida: {nodes}")
        return nodes
    else:
        print(f"Erro ao obter nós registrados: {response.status_code}")
    return []


def main(port):
    global my_node_address
    # Obtém o endereço do nó com base na porta fornecida
    my_node_address = f'http://localhost:{port}'

    # Registra automaticamente este nó no servidor de registro
    requests.post('http://localhost:5260/nodes/register', json={'address': my_node_address})

    # Obtém a lista de nós registrados
    blockchain.nodes = get_nodes(my_node_address)

    # Inicia o aplicativo Flask
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    main(args.port)
