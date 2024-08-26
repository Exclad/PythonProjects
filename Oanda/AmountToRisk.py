import requests
import tkinter as tk
from tkinter import messagebox

# Oanda API settings
API_TOKEN = 'YOUR_API_TOKEN_HERE'
ACCOUNT_ID = 'YOUR_ACCOUNT_ID_HERE'
API_URL = 'https://api-fxpractice.oanda.com/v3/accounts/'

# Function to get balance from Oanda API
def get_balance():
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
    }
    response = requests.get(f'{API_URL}{ACCOUNT_ID}', headers=headers)
    if response.status_code == 200:
        account_data = response.json()
        return float(account_data['account']['balance'])
    else:
        messagebox.showerror("Error", "Failed to retrieve balance")
        return 0

# Function to update the balance and risk values
def update_values():
    balance = get_balance()
    balance_label.config(text=f"Balance: ${balance:.2f}")
    risk_1_label.config(text=f"1% Risk: ${balance * 0.01:.2f}")
    risk_2_label.config(text=f"2% Risk: ${balance * 0.02:.2f}")
    risk_3_label.config(text=f"3% Risk: ${balance * 0.03:.2f}")

# Create the main window
root = tk.Tk()
root.title("Oanda Balance and Risk Calculator")

# Create labels to display balance and risk values
balance_label = tk.Label(root, text="Balance: $0.00", font=("Arial", 14))
balance_label.pack(pady=10)

risk_1_label = tk.Label(root, text="1% Risk: $0.00", font=("Arial", 12))
risk_1_label.pack(pady=5)

risk_2_label = tk.Label(root, text="2% Risk: $0.00", font=("Arial", 12))
risk_2_label.pack(pady=5)

risk_3_label = tk.Label(root, text="3% Risk: $0.00", font=("Arial", 12))
risk_3_label.pack(pady=5)

# Create a refresh button to update the values
refresh_button = tk.Button(root, text="Refresh", command=update_values)
refresh_button.pack(pady=20)

# Initialize the values when the program starts
update_values()

# Run the GUI main loop
root.mainloop()
