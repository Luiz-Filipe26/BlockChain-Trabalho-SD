import tkinter as tk
from tkinter import ttk, messagebox
import requests
from init_servers import init_servers

# Variáveis globais
NODES_SERVER_URL = "http://localhost:5260"  # URL base do servidor
TRANSACTIONS_ENDPOINT = "/transactions/new"  # Endpoint para criação de transações
NODES_ENDPOINT = "/nodes"  # Endpoint para obter a lista de nós
MINER_ENDPOINT = "/mine"  # Endpoint para iniciar a mineração (corrigido)
RESOLVE_CONFLICTS_ENDPOINT = "/nodes/resolve"  # Endpoint para resolver conflitos na blockchain
RESOLVE_NET_ENDPOINT = "/nodes/resolve_net"  # Endpoint para resolver conflitos na rede


class BlockchainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blockchain User Interface")

        # Usando a variável global NODES_SERVER_URL
        self.NODES_SERVER_URL = NODES_SERVER_URL
        self.blockchain_url = None  # Inicializa a variável do nó blockchain como None

        # Adicionar componentes da interface
        self.create_widgets()

        # Obter e preencher a lista de nós
        self.get_nodes()

    def create_widgets(self):
        """Cria os widgets da interface gráfica."""

        # Combobox para selecionar o nó
        self.node_label = tk.Label(self.root, text="Escolha o servidor Blockchain:")
        self.node_label.grid(row=0, column=0, padx=10, pady=10)

        self.node_combobox = ttk.Combobox(self.root)
        self.node_combobox.grid(row=0, column=1, padx=10, pady=10)

        # Botão para conectar ao servidor
        self.connect_button = tk.Button(self.root, text="Conectar", command=self.connect_to_node)
        self.connect_button.grid(row=0, column=2, padx=10, pady=10)

        # Campos para transação
        self.sender_label = tk.Label(self.root, text="Remetente:")
        self.sender_label.grid(row=1, column=0, padx=10, pady=10)

        self.recipient_label = tk.Label(self.root, text="Destinatário:")
        self.recipient_label.grid(row=2, column=0, padx=10, pady=10)

        self.amount_label = tk.Label(self.root, text="Quantia:")
        self.amount_label.grid(row=3, column=0, padx=10, pady=10)

        self.sender_entry = tk.Entry(self.root)
        self.sender_entry.grid(row=1, column=1, padx=10, pady=10)

        self.recipient_entry = tk.Entry(self.root)
        self.recipient_entry.grid(row=2, column=1, padx=10, pady=10)

        self.amount_entry = tk.Entry(self.root)
        self.amount_entry.grid(row=3, column=1, padx=10, pady=10)

        # Botão para enviar transação
        self.transaction_button = tk.Button(self.root, text="Enviar Transação", command=self.create_transaction)
        self.transaction_button.grid(row=4, column=1, padx=10, pady=10)

        # TextArea para mostrar transações
        self.transactions_text = tk.Text(self.root, width=50, height=10)
        self.transactions_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10)
        self.transactions_text.insert(tk.END, "Transações realizadas:\n")

    def get_nodes(self):
        """Obtém a lista de nós registrados via API."""
        try:
            response = requests.get(f'{self.NODES_SERVER_URL}{NODES_ENDPOINT}')
            if response.status_code == 200:
                nodes = response.json().get('nodes', [])
                self.node_combobox['values'] = nodes
                if nodes:
                    self.node_combobox.set(nodes[0])  # Seleciona o primeiro nó por padrão
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro ao buscar nós: {e}")

    def connect_to_node(self):
        """Conecta ao nó selecionado e exibe a mensagem de conexão."""
        node_address = self.node_combobox.get()
        if node_address:
            # Atualiza a URL da blockchain com o nó selecionado
            self.blockchain_url = node_address
            messagebox.showinfo("Conectado", f"Conectado ao servidor {node_address}")
        else:
            messagebox.showerror("Erro", "Por favor, selecione um nó para conectar.")

    def create_transaction(self):
        """Cria uma nova transação seguindo a ordem correta dos passos."""
        sender = self.sender_entry.get()
        recipient = self.recipient_entry.get()
        amount = self.amount_entry.get()

        if not sender or not recipient or not amount:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
            return

        # Enviar transação para a API
        transaction_data = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }

        try:
            # Resolver conflitos da blockchain conectada
            self.resolve_conflicts()

            # Resolver conflitos da rede
            self.resolve_net()

            # Criar a transação
            response = requests.post(f'{self.blockchain_url}{TRANSACTIONS_ENDPOINT}', json=transaction_data)
            if response.status_code == 201:
                # Após criar a transação, iniciar a mineração
                self.start_mining()
            else:
                messagebox.showerror("Erro", "Erro ao criar transação.")
                return
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro ao processar a transação: {e}")
            return

        # Limpar campos após envio
        self.sender_entry.delete(0, tk.END)
        self.recipient_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)

        # Exibir todas as transações após criação
        self.show_transaction_in_text()

    def start_mining(self):
        """Chama a API de mineração e resolve conflitos na rede após a mineração."""
        try:
            # Chama o endpoint de mineração
            response = requests.get(f'{self.blockchain_url}{MINER_ENDPOINT}')
            if response.status_code == 200:
                # Após minerar, resolver conflitos na rede
                self.resolve_net()
            else:
                messagebox.showerror("Erro", "Erro ao iniciar mineração.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro ao iniciar mineração: {e}")

    def show_transaction_in_text(self):
        """Exibe todas as transações da blockchain com sender diferente de 0 na TextArea."""
        try:
            response = requests.get(f'{self.blockchain_url}/chain')  # Supondo que o endpoint da blockchain seja /chain
            if response.status_code == 200:
                blockchain = response.json()
                all_transactions = []
                for block in blockchain.get('chain', []):
                    all_transactions.extend(block.get('transactions', []))

                # Filtrar transações cujo sender seja diferente de 0
                filtered_transactions = [
                    tx for tx in all_transactions if tx.get('sender') != '0'
                ]

                # Formatar as transações filtradas para exibição
                formatted_transactions = "\n".join(
                    [f"Sender: {tx['sender']} | Recipient: {tx['recipient']} | Amount: {tx['amount']}" for tx in
                     filtered_transactions]
                )

                self.transactions_text.delete(1.0, tk.END)  # Limpa o TextArea
                self.transactions_text.insert(tk.END, f"Transações atuais:\n{formatted_transactions}\n")
            else:
                messagebox.showerror("Erro", "Erro ao obter a blockchain para exibir transações.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro ao acessar a blockchain: {e}")

    def resolve_conflicts(self):
        """Chama a API de resolução de conflitos na blockchain."""
        try:
            response = requests.get(f'{self.blockchain_url}{RESOLVE_CONFLICTS_ENDPOINT}')
            if response.status_code == 200:
                result = response.json()
                if 'new_chain' in result:
                    self.transactions_text.insert(tk.END, "Conflitos resolvidos. A cadeia foi substituída.\n")
                else:
                    self.transactions_text.insert(tk.END,
                                                  "A cadeia está autoritária. Nenhuma substituição foi feita.\n")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro ao resolver conflitos na blockchain: {e}")

    def resolve_net(self):
        """Chama a API de resolução de conflitos na rede."""
        try:
            response = requests.get(f'{self.blockchain_url}{RESOLVE_NET_ENDPOINT}')
            if response.status_code == 200:
                self.transactions_text.insert(tk.END, "Conflitos resolvidos na rede.\n")
            else:
                messagebox.showerror("Erro", "Erro ao resolver conflitos na rede.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro ao resolver conflitos na rede: {e}")


if __name__ == "__main__":
    init_servers()
    print("Servidores iniciados!")
    my_root = tk.Tk()
    app = BlockchainApp(my_root)
    my_root.mainloop()
