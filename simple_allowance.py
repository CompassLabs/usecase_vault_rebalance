from aiohttp.helpers import TOKEN
from compass_api_sdk import CompassAPI
from compass_api_sdk.models import (
    Chain,
    MorphoVault,
    UserOperation,
    MulticallActionType,
    AaveWithdrawParams,
    MorphoWithdrawParams,
    MorphoDepositParams,
    IncreaseAllowanceParams,
    UniswapBuyExactlyParams,
    IncreaseAllowanceParamsContractName,
    MorphoSetVaultAllowanceParams,
    TokenEnum,
    IncreaseAllowanceParamsContractName,
    FeeEnum,
)
from dotenv import load_dotenv
import os
from decimal import Decimal
from eth_account import Account

from web3 import Web3

w3 = Web3(Web3.HTTPProvider(os.environ.get("ETH_RPC")))

load_dotenv()

CHAIN = Chain.ETHEREUM_MAINNET
ADDRESS = "0xa829B388A3DF7f581cE957a95edbe419dd146d1B"


compass = CompassAPI(
    api_key_auth=os.environ.get("COMPASS_KEY"),
    server_url="http://localhost:8000",
)

account = Account.from_key(os.environ.get("PK"))
unsigned_auth = compass.transaction_batching.authorization(chain=CHAIN, sender=ADDRESS)

signed_auth = Account.sign_authorization(
    unsigned_auth.model_dump(by_alias=True), os.environ.get("PK")
).model_dump()


actions = [
    UserOperation(
        action_type=MulticallActionType.AAVE_WITHDRAW,
        body=AaveWithdrawParams(token=TokenEnum.USDC, amount="1.5", recipient=ADDRESS),
    )
    # UserOperation(
    #     action_type=MulticallActionType.ALLOWANCE_INCREASE,
    #     body=IncreaseAllowanceParams(
    #         token=TokenEnum.USDC,
    #         amount='100',
    #         contract_name=IncreaseAllowanceParamsContractName.UNISWAP_V3_ROUTER,
    #     )
    # ),
    # UserOperation(
    #     action_type=MulticallActionType.UNISWAP_BUY_EXACTLY,
    #     body=UniswapBuyExactlyParams(
    #         max_slippage_percent=0.5,
    #         amount=0.0001,
    #         fee=FeeEnum.ZERO_DOT_01,
    #         token_in=TokenEnum.USDC,
    #         token_out=TokenEnum.WETH,
    #     )
    # )
]
multicall_transaction = compass.transaction_batching.execute(
    chain=CHAIN,
    sender=ADDRESS,
    signed_authorization=signed_auth,
    actions=actions,
    server_url="http://localhost:8000",
)

multicall_transaction.gas = 99999
print(multicall_transaction)


# signed_multicall_transaction = Account.sign_transaction(
#     multicall_transaction.model_dump(by_alias=True), os.environ.get("PK")
# )
# # print(f"{w3.eth.get_code(IMPERSONATED_ADDRESS)=}")
# tx_hash = w3.eth.send_raw_transaction(signed_multicall_transaction.raw_transaction)
# # print(f"{w3.eth.get_code(IMPERSONATED_ADDRESS)=}")
# # tx_hash = w3.eth.send_transaction(multicall_transaction)
# # print(f"Multicall transaction hash: {tx_hash.hex()}")
# receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
# print(f"{receipt=}")
#
#
# ####
#
# w3.eth.get_code(ADDRESS)
