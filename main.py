import streamlit as st
import plotly.graph_objects as go

from compass_api_sdk import CompassAPI
from compass_api_sdk.models import Chain, TokenEnum, TokenAddressToken, MorphoVault
from dotenv import load_dotenv
import os

load_dotenv()
st.set_page_config(layout="wide")

st.title("Vault rebalance demo")
st.text("""Demoing rebalaning USDC over several vaults.
We are assuming all depoists are made from the same address, but that could easily be changed.
""")
address = st.text_input(
    label="Choose the deposit address",
    value="0xa829B388A3DF7f581cE957a95edbe419dd146d1B",
)
chain = st.selectbox(
    label="Chain", options=[Chain.ETHEREUM_MAINNET, Chain.ARBITRUM_MAINNET]
)


def horizontal_bar(container, value: float, color: str = "#4CAF50"):
    """
    Draws a horizontal bar inside the given container.
    """
    percentage = int(value * 100)
    bar_html = f"""
    <div style="background-color: #ddd; width: 100%; height: 20px; border-radius: 5px; overflow: hidden; margin-bottom: 10px;">
        <div style="
            width: {percentage}%;
            height: 100%;
            background-color: {color};
            border-radius: 5px;
        "></div>
    </div>
    """
    container.markdown(bar_html, unsafe_allow_html=True)


compass = CompassAPI(
    api_key_auth=os.environ.get("COMPASS_KEY"),
)

COLLATERAL = TokenEnum.USDC
COLLATERAL_ADDRESS = compass.token.address(
    chain=Chain.ARBITRUM_MAINNET, token=TokenAddressToken.WETH
).address


address2vault: dict[str, MorphoVault] = {
    vault.address for vault in compass.morpho.vaults().vaults
}
user_positions = compass.morpho.user_position(
    chain=chain,
    user_address=address,
).vault_positions

user_positions = [
    position for position in user_positions if position.vault.asset.symbol == "USDC"
]

cols = st.columns(3)

with cols[0]:
    st.subheader("Current State")
    for i, position in enumerate(user_positions):
        c = st.container(border=True, height=200)
        c.markdown(f"#### {position.vault.name}")
        c.text(position.vault.address)
        c.markdown(f"**{round(float(position.state.assets_usd), 2)}** USD deposits")
        c.markdown(f"**{round(float(position.vault.daily_apys.apy) * 100, 2)} %** APY")

    deposits_arr = [pos.state.assets_usd for pos in user_positions]
    vault_names = [pos.vault.name for pos in user_positions]
    vault_symbol = [position.vault.asset.name for pos in user_positions]
    trace = go.Pie(
        labels=vault_names,
        values=deposits_arr,
    )
    st.plotly_chart(go.Figure(trace))


with cols[1]:
    st.subheader("Target Distribution")
    sliders = []
    for i, position in enumerate(user_positions):
        c = st.container(border=True, height=200)
        c.markdown(f"#### {position.vault.name}")
        value = c.slider(
            key=f"slider_{position.vault.address}",
            label="Choose percentage",
            value=100 if i == 0 else 0,
        )
        sliders.append(value)

    sum = sum(sliders)
    if sum != 100:
        st.warning("Rebalance percentages need to add up to 100%")
    else:
        st.success("This is a success message!", icon="✅")
        bt1 = st.button("Rebalance")

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
