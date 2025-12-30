import streamlit as st
import time
import os
import json
import random
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from langchain_groq import ChatGroq

st.set_page_config(page_title="WalletZero Terminal", layout="wide")
load_dotenv()

WALLET_FILE = "zero_wallet_groq.json"
RPC_URL = os.getenv("TENDERLY_RPC_URL", "https://rpc.sepolia.org")
BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Consolas', monospace;
        color: #e0e0e0;
        font-size: 1.8rem;
    }
    div[data-testid="stMetricLabel"] {
        color: #888;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    .terminal-window {
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: #000000;
        border: 1px solid #333;
        border-left: 2px solid #555;
        padding: 10px;
        height: 450px;
        overflow-y: auto;
        font-size: 0.8rem;
        color: #ccc;
        line-height: 1.4;
    }
    .log-timestamp { color: #555; margin-right: 10px; }
    .log-sys { color: #00aaff; font-weight: 600; }
    .log-buy { color: #ff5252; font-weight: 600; }
    .log-sell { color: #4caf50; font-weight: 600; }
    .log-algo { color: #ff9800; font-weight: 600; }
    div.stButton > button {
        background-color: #1f2937;
        color: #e0e0e0;
        border: 1px solid #374151;
        border-radius: 4px;
        font-size: 0.85rem;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #374151;
        border-color: #4b5563;
    }
    .stNumberInput input {
        background-color: #111;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

class TenderlyWallet:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.account = None
        self.address = "Initializing..."
        self.balance = 0.0
        self.tx_count = 0

    def connect(self):
        try:
            if not self.w3.is_connected(): return False, "Error: RPC Connection Failed"
            if os.path.exists(WALLET_FILE):
                with open(WALLET_FILE, "r") as f:
                    data = json.load(f)
                    self.account = self.w3.eth.account.from_key(data['private_key'])
            else:
                self.account = self.w3.eth.account.create()
                with open(WALLET_FILE, "w") as f:
                    json.dump({'private_key': self.account._private_key.hex()}, f)
            self.address = self.account.address
            self.refresh_stats()
            return True, "System Connected"
        except Exception as e:
            return False, f"Critical Error: {e}"

    def refresh_stats(self):
        try:
            wei = self.w3.eth.get_balance(self.address)
            self.balance = float(self.w3.from_wei(wei, 'ether'))
            self.tx_count = self.w3.eth.get_transaction_count(self.address)
        except:
            pass
        return self.balance

    def sell_asset(self, amount_eth):
        try:
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            payload = {
                "jsonrpc": "2.0",
                "method": "tenderly_addBalance",
                "params": [[self.address], hex(amount_wei)],
                "id": 1
            }
            res = requests.post(RPC_URL, json=payload)
            if res.status_code == 200 and 'result' in res.json():
                self.refresh_stats()
                return True, f"Liquidity Added: +{amount_eth} ETH"
            return False, f"RPC Error: {res.text}"
        except Exception as e:
            return False, f"Exception: {e}"

    def buy_asset(self, amount_eth):
        return self.sign_and_send(amount_eth, to_address=BURN_ADDRESS)

    def sign_and_send(self, amount_eth, to_address=None, data_hex="0x"):
        if not to_address: to_address = self.address 
        try:
            tx_config = {
                'nonce': self.tx_count,
                'to': to_address,
                'value': self.w3.to_wei(amount_eth, 'ether'),
                'gas': 100000, 
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
                'data': data_hex 
            }
            signed = self.w3.eth.account.sign_transaction(tx_config, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.refresh_stats()
            return f"{tx_hash.hex()}"
        except Exception as e:
            return f"Error: {str(e)}"

class AlgoEngine:
    def __init__(self):
        self.llm = None

    def initialize(self):
        key = os.getenv("GROQ_API_KEY")
        if not key:
            st.error("Configuration Error: API Key Missing")
            return False
        
        try:
            self.llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3, api_key=key)
            return True
        except Exception as e:
            st.error(f"Initialization Failed: {e}")
            return False

    def analyze(self, balance, strategy):
        if not self.llm: 
            return {"thought": "System Offline", "action": "HOLD", "amount": 0}

        prompt = f"""
        Role: Automated Trading System.
        Current Balance: {balance:.4f} ETH.
        Strategy Directive: "{strategy}"

        ACTIONS:
        1. BUY_ENTRY (Simulates capital deployment)
        2. SELL_EXIT (Simulates profit realization)
        3. HOLD (No action)
        
        Output valid JSON only.
        
        Example:
        {{
            "thought": "Market conditions optimal for entry.",
            "action": "BUY_ENTRY",
            "amount": 0.05
        }}
        """
        try:
            res = self.llm.invoke(prompt).content
            cleaned_res = res.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_res)
        except Exception as e:
            print(f"Algorithm Error: {e}") 
            return {"thought": f"Logic Failure: {str(e)}", "action": "HOLD", "amount": 0}

def main():
    if "system" not in st.session_state:
        st.session_state.system = TenderlyWallet()
        st.session_state.algo = AlgoEngine()
        st.session_state.logs = [] 
        st.session_state.balance_chart = [] 
        st.session_state.system.connect()
        st.session_state.algo.initialize()

    with st.sidebar:
        st.markdown("### Configuration")
        strategy = st.text_area("Strategy Parameters", "High-frequency arbitrage. Risk tolerance: Moderate.")
        st.markdown("---")
        if st.button("Reset Session"):
            st.session_state.logs = []
            st.session_state.balance_chart = []
            st.rerun()

    st.markdown("## WalletZero // Financial Terminal")
    st.markdown("---")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Net Asset Value (ETH)", f"{st.session_state.system.balance:.4f}")
    m2.metric("Total Transactions", st.session_state.system.tx_count)
    m3.metric("PnL (Session)", f"{st.session_state.system.balance - 10.0:.3f}") 
    m4.metric("System Status", "Active")

    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.markdown("#### Performance Analytics")
        if len(st.session_state.balance_chart) > 0:
            fig = go.Figure(data=go.Scatter(
                y=st.session_state.balance_chart,
                mode='lines',
                line=dict(color='#cccccc', width=1.5),
            ))
            fig.update_layout(
                height=250, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(visible=False), yaxis=dict(gridcolor='#333'),
                showlegend=False
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Awaiting market data...")

        st.markdown("#### Order Entry")
        c1, c2 = st.columns(2)
        
        with c1:
            buy_amount = st.number_input("Order Size (ETH)", 0.01, 10.0, 0.1, key="b_amt")
            if st.button("Execute Buy Order"):
                with st.spinner("Processing Order..."):
                    tx_hash = st.session_state.system.buy_asset(buy_amount)
                    ts = datetime.now().strftime('%H:%M:%S')
                    st.session_state.logs.insert(0, f"<span class='log-timestamp'>{ts}</span> <span class='log-buy'>[EXECUTION]</span> Buy Order Filled: {buy_amount} ETH")
                    st.session_state.balance_chart.append(st.session_state.system.balance)
                    st.rerun()

        with c2:
            sell_amount = st.number_input("Liquidation Size (ETH)", 0.01, 10.0, 0.5, key="s_amt")
            if st.button("Execute Sell Order"):
                with st.spinner("Processing Order..."):
                    success, msg = st.session_state.system.sell_asset(sell_amount)
                    ts = datetime.now().strftime('%H:%M:%S')
                    if success:
                        st.session_state.logs.insert(0, f"<span class='log-timestamp'>{ts}</span> <span class='log-sell'>[EXECUTION]</span> Sell Order Filled: {msg}")
                        st.session_state.balance_chart.append(st.session_state.system.balance)
                        st.rerun()

        st.markdown("---")
        if st.button("Run Automated Analysis Cycle"):
            with st.spinner("Running Algorithm..."):
                d = st.session_state.algo.analyze(st.session_state.system.balance, strategy)
                ts = datetime.now().strftime('%H:%M:%S')
                st.session_state.logs.insert(0, f"<span class='log-timestamp'>{ts}</span> <span class='log-algo'>[ALGO]</span> {d['thought']}")
                
                if d['action'] == "BUY_ENTRY":
                    st.session_state.system.buy_asset(d['amount'])
                    st.session_state.logs.insert(0, f"<span class='log-timestamp'>{ts}</span> <span class='log-buy'>[AUTO]</span> Buy Executed: {d['amount']} ETH")
                elif d['action'] == "SELL_EXIT":
                    st.session_state.system.sell_asset(d['amount'])
                    st.session_state.logs.insert(0, f"<span class='log-timestamp'>{ts}</span> <span class='log-sell'>[AUTO]</span> Sell Executed: {d['amount']} ETH")
                
                st.session_state.balance_chart.append(st.session_state.system.balance)
                st.rerun()

    with c_right:
        st.markdown("#### System Logs")
        log_html = "<br>".join(st.session_state.logs)
        st.markdown(f"<div class='terminal-window'>{log_html}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()