import requests
import argparse

BASE_URL = None  # Será inicializado após leitura dos argumentos


def print_menu():
    print("1. Mine a new block")
    print("2. Add a new transaction")
    print("3. View the blockchain")
    print("4. Resolve conflicts (consensus)")
    print("5. Register new nodes")
    print("0. Exit")


def mine_block():
    response = requests.get(f"{BASE_URL}/mine")
    if response.status_code == 200:
        block = response.json()
        print("New block mined successfully:")
        print(f"Block Index: {block['index']}")
        print(f"Transactions: {block['transactions']}")
        print(f"Proof: {block['proof']}")
        print(f"Previous Hash: {block['previous_hash']}")
    else:
        print("Failed to mine block")


def add_transaction():
    sender = input("Enter sender: ")
    recipient = input("Enter recipient: ")
    amount = float(input("Enter amount: "))
    transaction_data = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount
    }
    response = requests.post(f"{BASE_URL}/transactions/new", json=transaction_data)
    if response.status_code == 201:
        print(response.json()['message'])
    else:
        print("Failed to add transaction")


def view_blockchain():
    response = requests.get(f"{BASE_URL}/chain")
    if response.status_code == 200:
        blockchain = response.json()
        print("Blockchain:")
        for block in blockchain['chain']:
            print(f"Index: {block['index']}")
            print(f"Transactions: {block['transactions']}")
            print(f"Proof: {block['proof']}")
            print(f"Previous Hash: {block['previous_hash']}")
            print("----")
    else:
        print("Failed to retrieve blockchain")


def resolve_conflicts():
    response = requests.get(f"{BASE_URL}/nodes/resolve")
    if response.status_code == 200:
        result = response.json()
        print(result['message'])
        if 'new_chain' in result:
            print("Replaced chain:")
            for block in result['new_chain']:
                print(f"Index: {block['index']}")
                print(f"Transactions: {block['transactions']}")
                print(f"Proof: {block['proof']}")
                print(f"Previous Hash: {block['previous_hash']}")
                print("----")
    else:
        print("Failed to resolve conflicts")


def register_nodes():
    print("Register nodes:")
    nodes = input("Enter nodes (comma-separated, e.g., 127.0.0.1:5001,127.0.0.1:5002): ")
    node_list = [node.strip() for node in nodes.split(",")]

    response = requests.post(f"{BASE_URL}/nodes/register", json={'nodes': node_list})
    if response.status_code == 201:
        print("Nodes registered successfully:")
        print(response.json()['total_nodes'])
    else:
        print("Failed to register nodes")


def main():
    global BASE_URL  # Define BASE_URL como uma variável global
    parser = argparse.ArgumentParser(description="Blockchain Client")
    parser.add_argument('-p', '--port', type=int, default=5000, help="Server port (default: 5000)")
    args = parser.parse_args()

    BASE_URL = f"http://127.0.0.1:{args.port}"

    while True:
        print_menu()
        choice = input("Select an option: ")

        if choice == '1':
            mine_block()
        elif choice == '2':
            add_transaction()
        elif choice == '3':
            view_blockchain()
        elif choice == '4':
            resolve_conflicts()
        elif choice == '5':
            register_nodes()
        elif choice == '0':
            break
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()