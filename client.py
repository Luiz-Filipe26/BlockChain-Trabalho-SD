import requests
import argparse

BASE_URL = None  # Será inicializado após leitura dos argumentos


def print_menu():
    print("1. Mine a new block")
    print("2. Add a new transaction")
    print("3. View the blockchain")
    print("4. Check if the blockchain is valid")
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


def check_validity():
    response = requests.get(f"{BASE_URL}/nodes/resolve")
    if response.status_code == 200:
        print(response.json()['message'])
    else:
        print("Failed to check blockchain validity")


def main():
    global BASE_URL  # Define BASE_URL como uma variável global
    parser = argparse.ArgumentParser(description="Blockchain Client")
    parser.add_argument('-i', '--ip', type=str, default="127.0.0.1", help="Server IP address (default: 127.0.0.1)")
    parser.add_argument('-p', '--port', type=int, default=5000, help="Server port (default: 5000)")
    args = parser.parse_args()

    BASE_URL = f"http://{args.ip}:{args.port}"

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
            check_validity()
        elif choice == '0':
            break
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()