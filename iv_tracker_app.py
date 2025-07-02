
import streamlit as st
import pandas as pd
import requests
import datetime
import statistics

st.set_page_config(page_title="Expiry IV Tracker", layout="wide")
st.title("📈 Expiry Day IV Tracker for NIFTY")

if "iv_history" not in st.session_state:
    st.session_state.iv_history = []

NSE_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def fetch_option_data():
    with requests.Session() as s:
        s.get("https://www.nseindia.com", headers=headers)
        response = s.get(NSE_URL, headers=headers)
        return response.json()['records']['data']

def get_atm_iv(data):
    spot_price = data[0]['CE']['underlyingValue']
    atm_strike = round(spot_price / 50) * 50
    for entry in data:
        if entry['strikePrice'] == atm_strike and 'CE' in entry:
            iv = entry['CE'].get('impliedVolatility')
            return atm_strike, iv, spot_price
    return None, None, spot_price

def detect_sigma_spike(iv_list):
    if len(iv_list) < 10:
        return 0, False
    mean_iv = statistics.mean(iv_list[:-1])
    std_iv = statistics.stdev(iv_list[:-1])
    current_iv = iv_list[-1]
    sigma = (current_iv - mean_iv) / std_iv if std_iv else 0
    return round(sigma, 2), sigma >= 3

try:
    data = fetch_option_data()
    atm_strike, iv, spot = get_atm_iv(data)

    if iv:
        st.session_state.iv_history.append(iv)
        timestamps = st.session_state.get("timestamps", [])
        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        timestamps.append(current_time)
        st.session_state.timestamps = timestamps

        sigma, alert = detect_sigma_spike(st.session_state.iv_history)

        col1, col2, col3 = st.columns(3)
        col1.metric("Spot Price", f"{spot:.2f}")
        col2.metric("ATM Strike", atm_strike)
        col3.metric("ATM IV", f"{iv:.2f}%")

        if alert:
            st.error(f"🚨 IV Spike Detected: {sigma}σ move — Possible Violent Expiry Setup!")

        df = pd.DataFrame({
            "Time": st.session_state.timestamps,
            "IV (%)": st.session_state.iv_history
        })
        st.line_chart(df.set_index("Time"))

    else:
        st.warning("Could not extract ATM IV. Try again shortly.")

except Exception as e:
    st.error(f"❌ Error fetching data: {e}")
