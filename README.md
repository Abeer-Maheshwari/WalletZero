# WalletZero Terminal

![Streamlit](https://img.shields.io/badge/Streamlit-%23FF4B4B.svg)
![Web3.py](https://img.shields.io/badge/Web3.py-%23F16822)
![Groq](https://img.shields.io/badge/Groq-%23000000)

**Author:** Abeer Maheshwari

This is a simulated financial trading terminal designed for testing and experimenting with automated trading strategies. It integrates AI-driven decision-making to analyze market conditions and execute buy/sell actions based on user-defined strategies.

The app provides manual order entry, automated analysis cycles, real-time logs, performance metrics, and a balance history chart. **NOTE**: All transactions are simulated—buys send ETH to a burn address, and sells add balance via Tenderly RPC calls.

## Features

1. Wallet Management
   - Secure Wallet Handling: Automatically creates or loads a wallet from a JSON file, connects to Sepolia testnet via Tenderly RPC.
   - Balance and Stats Refresh: Real-time updates for ETH balance and transaction count.

2. Order Execution
   - Manual Buy/Sell: User-input order sizes for buying or selling.
   - Automated Trading: AI analyzes balance and strategy to decide on BUY_ENTRY, SELL_EXIT, or HOLD actions.

3. AI-Powered Analysis
   - Strategy Customization: Input custom trading directives.
   - LLM Integration: Uses Groq's Llama 3 model to generate thoughtful trading decisions in JSON format.

4. Visualization and Logging
   - Performance Chart: Interactive Plotly line chart showing balance history.
   - Terminal Logs: Color-coded logs for system events, executions, and algo thoughts.
   - Metrics Dashboard: Displays Net Asset Value, Total Transactions, PnL, and System Status.

## Installation

1. **Install Dependencies**
   ```
   pip install streamlit web3 requests plotly pandas groq python-dotenv
   ```

2. **Set Up API Keys**
   Create a `.env` file in the root directory and add your API keys:
   ```
   GROQ_API_KEY=gsk_your_groq_key_here
   TENDERLY_RPC_URL=https://your-tenderly-rpc-url-here  # Optional; defaults to https://rpc.sepolia.org
   ```

3. **Run the Application**
   ```
   streamlit run walletzero.py
   ```

## Usage Guide

### **Main Interface**
1. Launch the app and it will automatically connect to the wallet (creates one if none exists).
2. In the sidebar, customize the "Strategy Parameters" text area for AI guidance.
3. View metrics like Net Asset Value and PnL at the top.
4. In the "Order Entry" section:
   - Enter an amount and click "Execute Buy Order" to simulate a buy (burns ETH).
   - Enter an amount and click "Execute Sell Order" to simulate a sell (adds balance via Tenderly).
5. Click "Run Automated Analysis Cycle" to let the AI analyze and potentially execute an action based on the strategy.
6. Monitor the "System Logs" for timestamped events and the "Performance Analytics" chart for balance trends.
7. Use the "Reset Session" button in the sidebar to clear logs and charts.
8. Adjust strategy parameters to influence AI decisions.

## Notes
*This tool is for educational and simulation purposes only. It operates on a testnet with simulated balances and does not involve real funds or live trading. AI-generated decisions are not financial advice.*
