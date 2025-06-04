from compass_api_sdk import CompassAPI
from compass_api_sdk.models import (
    Chain,
    MorphoVault,
    UserOperation,
    BatchedUserOperationsRequest,
    UserOperationTypedDict,
    MorphoWithdrawParams,
    MorphoDepositParams,
    MorphoSetVaultAllowanceParams,
    TokenEnum,
)
from dotenv import load_dotenv
import os
from decimal import Decimal
from eth_account import Account
from compass_api_sdk.models.useroperation import UserOperation

from compass.api_backend.config.contract import ContractName
from compass.api_backend.models.aave.transact.request.supply import AaveSupplyParams
from compass.api_backend.models.aave.transact.request.withdraw import AaveWithdrawParams
from compass.api_backend.models.generic.transact import IncreaseAllowanceAnyParams
from compass.api_backend.models.uniswap.transact.swap.request.sell_exactly import UniswapSellExactlyParams

load_dotenv()

CHAIN = Chain.ETHEREUM_MAINNET
ADDRESS = "0xa829B388A3DF7f581cE957a95edbe419dd146d1B"
TOKENS = [TokenEnum.USDC, TokenEnum.WETH, TokenEnum.USDT, TokenEnum.LINK]


compass = CompassAPI(
    api_key_auth=os.environ.get("COMPASS_KEY"),
)

token_prices = {
    token: float(compass.token.price(chain=CHAIN, token=token).price)
    for token in TOKENS
}

user_positions = [
    compass.aave_v3.user_position_per_token(
        chain=Chain.ARBITRUM_MAINNET, user=ADDRESS, token=token
    )
    for token in TOKENS
]
user_positions = [u for u in user_positions if float(u.token_balance) != 0.0]


####
deposits_arr = [
    float(pos.token_balance) * token_prices[TOKENS[i]]
    for i, pos in enumerate(user_positions)
]
account = Account.from_key(os.environ.get("PK"))
unsigned_auth = compass.transaction_batching.authorization(chain=CHAIN, sender=ADDRESS)

signed_auth = Account.sign_authorization(
    unsigned_auth.model_dump(by_alias=True), os.environ.get("PK")
)


target_percentages = [0.3, 0.4, 0.3]
# CODE START
target_absolutes = [Decimal(p) * sum(deposits_arr) for p in target_percentages]
actions = []
# Withdraw all and sell into USDT
for position in user_positions:
    actions.append(
        UserOperation(
            body=AaveWithdrawParams(
                action_type="AAVE_WITHDRAW",
                vault_address=position.vault.address,
                amount="ALL",
                receiver=ADDRESS,
            ),
        )
    )
    actions.append(
        UserOperation(
            body=UniswapSellExactlyParams(
                action_type="UNSIWAP_SELL_EXACTLY",
                vault_address=position.vault.address,
                amount="ALL",
                receiver=ADDRESS,
            ),
        )
    )
# Buy the appropriate tokens, then supply to AAVE
for i, position in enumerate(user_positions):
    actions.append(
        UserOperation(
            body=UniswapSellExactlyParams(
                vault_address=position.vault.address,
                amount="ALL",
                receiver=ADDRESS,
            ),
        )
    )
    actions.append(
        UserOperation(
            body=IncreaseAllowanceAnyParams(
                token=TOKENS[i],
                contract_name=ContractName.UniswapV3Router,
                amount=sell_amounts[i]
        )
    )
    actions.append(
        UserOperation(
            body=AaveSupplyParams(
                vault_address=position.vault.address,
                amount=target_absolutes[i],
                receiver=ADDRESS,
            ),
        )
    )


unsigned_transaction = compass.transaction_batching.execute(
    chain=CHAIN,
    sender=ADDRESS,
    signed_authorization=signed_auth.model_dump(),
    actions=actions,
)

print(unsigned_transaction)
# CODE END
