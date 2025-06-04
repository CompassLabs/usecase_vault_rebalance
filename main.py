import streamlit as st
import plotly.graph_objects as go

from compass_api_sdk import CompassAPI
from compass_api_sdk.models import (
    Chain,
    TokenEnum,
    TokenAddressToken,
    MorphoVault,
    AaveUserPositionPerTokenToken,
)
from dotenv import load_dotenv
import os
from aaa import do_rebalance
import json

load_dotenv()


compass: CompassAPI = CompassAPI(
    api_key_auth=os.environ.get("COMPASS_KEY"),
)


st.set_page_config(layout="wide")
address = st.text_input(
    label="Choose the deposit address",
    value="0xa829B388A3DF7f581cE957a95edbe419dd146d1B",
)
chain = st.selectbox(label="Chain", options=[Chain.ARBITRUM_MAINNET], index=0)


TOKENS = [TokenEnum.USDC, TokenEnum.WETH, TokenEnum.USDT, TokenEnum.LINK]

token_prices = {
    token: float(compass.token.price(chain=chain, token=token).price)
    for token in TOKENS
}

st.text(token_prices)

user_positions = [
    compass.aave_v3.user_position_per_token(
        chain=Chain.ARBITRUM_MAINNET, user=address, token=token
    )
    for token in TOKENS
]
user_positions = [u for u in user_positions if float(u.token_balance) != 0.0]


st.title("Vault rebalance demo")
st.text("""Demoing rebalaning USDC over several vaults.
We are assuming all depoists are made from the same address, but that could easily be changed.
""")


cols = st.columns(3)

with cols[0]:
    st.subheader("Current State")
    for i, position in enumerate(user_positions):
        if float(position.token_balance) == 0.0:
            continue
        c = st.container(border=True, height=200)
        c.markdown(f"#### {TOKENS[i].value}")
        c.markdown(f"{round(float(position.token_balance), 8)} balance")
        c.markdown(
            f"{round(float(position.token_balance) * token_prices[TOKENS[i]], 4)} USD"
        )
        c.markdown(f"{round(float(position.liquidity_rate) * 100, 2)} % interest")
    #     c.markdown(f"**{round(float(position.state.assets_usd), 2)}** USD deposits")
    #     c.markdown(f"**{round(float(position.vault.daily_apys.apy) * 100, 2)} %** APY")
    #
    deposits_arr = [
        float(pos.token_balance) * token_prices[TOKENS[i]]
        for i, pos in enumerate(user_positions)
    ]
    vault_names = [TOKENS[i].value for i, pos in enumerate(user_positions)]
    vault_symbol = [TOKENS[i].value for i, pos in enumerate(user_positions)]
    trace = go.Pie(
        labels=vault_names,
        values=deposits_arr,
    )
    st.plotly_chart(go.Figure(trace))


with cols[1]:
    st.subheader("Target Distribution")
    sliders = []
    for i, position in enumerate(user_positions):
        if float(position.token_balance) == 0.0:
            continue
        c = st.container(border=True, height=200)
        c.markdown(f"#### {TOKENS[i].value}")
        c.markdown(
            f"Current percentage: {round(deposits_arr[i] / sum(deposits_arr) * 100, 2)} %"
        )
        value = c.slider(
            key=f"slider_{TOKENS[i].value}",
            label="Choose percentage",
            value=deposits_arr[i] / sum(deposits_arr) * 100,
            min_value=0.0,
            max_value=100.0,
        )
        sliders.append(value)

    sum = sum(sliders)
    if sum < 99.8 or sum > 100.2:
        st.warning("Rebalance percentages need to add up to 100%")
    else:
        st.success("This is a success message!", icon="✅")
        bt1 = st.button("Rebalance")
        if bt1:
            st.text(
                "Here's the single transaction to rebalance all positions.\nSign this transaction with the wallet of your choice and then submit to chain."
            )
            result = do_rebalance()
            st.code(json.dumps(result, indent=4))

    with cols[2]:
        st.subheader("Batched Transaction")
        st.text(
            "Below if the full code to make the rebalance happen programticallyusing the comopass SDK"
        )

        with open("./rebalance.py", "r") as f:
            t = f.read()
        t = t.split("# CODE START")[1].split("# CODE END")[0]
        t = f"target_percentages={[i / 100 for i in sliders]}\n" + t
        st.code(t)
