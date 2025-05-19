import streamlit as st
import plotly.graph_objects as go

from compass_api_sdk import CompassAPI
from compass_api_sdk.models import Chain, TokenEnum, TokenAddressToken, MorphoVault
from dotenv import load_dotenv
import os

load_dotenv()
st.set_page_config(layout="wide")

st.title("Compass vault rebalance demo")
address = st.text_input(label="Address", value='0xa829B388A3DF7f581cE957a95edbe419dd146d1B')
chain = st.selectbox(
    label="Chain", options=[Chain.ETHEREUM_MAINNET, Chain.ARBITRUM_MAINNET]
)

TOTAL = 1.1e6

ORIGINAL_SPLIT = [0.41, 0.05, 0.28, 1 - 0.41 - 0.05 - 0.28]


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


cols = st.columns(3)

with cols[0]:
    st.subheader("Current State")
    for i, position in enumerate(user_positions):
        c = st.container(border=True, height=200)
        c.markdown(f"#### {position.vault.name}")
        c.text(position.vault.address)
        c.markdown(f"**{round(float(position.state.assets_usd), 2)}** USD deposits")
        # c.progress(
        #     ORIGINAL_SPLIT[i],
        #     text=f"{round(ORIGINAL_SPLIT[i] * 100, 2)} % | {round(TOTAL * ORIGINAL_SPLIT[i], 2)} USDC",
        # )
    deposits_arr = [pos.state.assets_usd for pos in user_positions]
    vault_names = [
        pos.vault.name for pos in user_positions
    ]  # position.vault.asset.name
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
        # st.markdown(
        #     """
        #     <div style="height: 200px; border: 1px solid gray; padding: 10px;">
        #         <p>This container has a fixed height of 200px.</p>
        #         <p>You can add more content here.</p>
        #     </div>
        #     """,
        #     unsafe_allow_html=True,
        # )
        c = st.container(border=True, height=200)

        c.markdown(f"#### {position.vault.name}")
        # c.text(position.vault.address)
        value = c.slider(
            key=f"slider_{position.vault.address}", label="Choose percentage"
        )
        sliders.append(value)

    # sliders=[st.slider(key=f'slider_{pos.vault.address}', label='aaa') for pos in user_positions]
    sum = sum(sliders)
    if sum != 100:
        st.warning("Rebalance percentages need to add up to 100%")
    else:
        st.success("This is a success message!", icon="✅")
        st.button("Rebalance")

with cols[2]:
    st.subheader("Required Code")
    st.code("""
with cols[2]:
    st.subheader("Desired State")
    st.markdown(f"**TOTAL:** {TOTAL} USDC")
    for i, vault in enumerate(vaults):
        c = st.container(border=True)
        c.markdown(f"#### {vault.name}")
        c.text(vault.address)
        c.progress(
            ORIGINAL_SPLIT[i],
            text=f"{round(ORIGINAL_SPLIT[i] * 100, 2)} % | {round(TOTAL * ORIGINAL_SPLIT[i], 2)} USDC",
        )
""")


# changes = [0, 0, 0, 0]
#
# with cols[1]:
#     st.subheader("Change")
#     st.markdown(f"**TOTAL:** {TOTAL} USDC")
#     for i, vault in enumerate(vaults):
#         c = st.container(border=True)
#         c.markdown(f"#### {vault.name}")
#         c.text(vault.address)
#         changes[i] = c.number_input(
#             label=f"Change {i}",
#             min_value=-TOTAL * ORIGINAL_SPLIT[i],
#             max_value=TOTAL - TOTAL * ORIGINAL_SPLIT[i],
#             value=0.0,
#             step=1.0,
#         )
#
#
# with cols[2]:
#     st.subheader("Desired State")
#     st.markdown(f"**TOTAL:** {TOTAL} USDC")
#     for i, vault in enumerate(vaults):
#         c = st.container(border=True)
#         c.markdown(f"#### {vault.name}")
#         c.text(vault.address)
#         c.progress(
#             ORIGINAL_SPLIT[i],
#             text=f"{round(ORIGINAL_SPLIT[i] * 100, 2)} % | {round(TOTAL * ORIGINAL_SPLIT[i], 2)} USDC",
#         )
