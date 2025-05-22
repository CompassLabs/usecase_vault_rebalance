from compass_api_sdk import CompassAPI
from compass_api_sdk.models import (
    Chain,
    MorphoVault,
    UserOperation,
    MulticallActionType,
    MorphoWithdrawParams,
    MorphoDepositParams,
    MorphoSetVaultAllowanceParams,
)
from dotenv import load_dotenv
import os
from decimal import Decimal
from eth_account import Account

load_dotenv()

CHAIN = Chain.ETHEREUM_MAINNET
ADDRESS = "0xa829B388A3DF7f581cE957a95edbe419dd146d1B"


compass = CompassAPI(
    api_key_auth=os.environ.get("COMPASS_KEY"),
)


address2vault: dict[str, MorphoVault] = {
    vault.address for vault in compass.morpho.vaults().vaults
}
user_positions = compass.morpho.user_position(
    chain=CHAIN,
    user_address=ADDRESS,
).vault_positions
user_positions = [
    position for position in user_positions if position.vault.asset.symbol == "USDC"
]

deposits_arr = [Decimal(pos.state.assets_usd) for pos in user_positions]
account = Account.from_key(os.environ.get("PK"))
unsigned_auth = compass.transaction_batching.authorization(chain=CHAIN, sender=ADDRESS)

signed_auth = Account.sign_authorization(
    unsigned_auth.model_dump(by_alias=True), os.environ.get("PK")
)


target_percentages = [0.3, 0.4, 0.3]
# CODE START
target_absolutes = [Decimal(p) * sum(deposits_arr) for p in target_percentages]
actions = []
for position in user_positions:
    actions.append(
        UserOperation(
            action_type=MulticallActionType.MORPHO_WITHDRAW,
            body=MorphoWithdrawParams(
                vault_address=position.vault.address, amount="ALL", receiver=ADDRESS
            ),
        )
    )
for i, position in enumerate(user_positions):
    actions.append(
        UserOperation(
            action_type=MulticallActionType.MORPHO_SET_VAULT_ALLOWANCE,
            body=MorphoSetVaultAllowanceParams(
                vault_address=position.vault.address, amount=target_absolutes[i]
            ),
        )
    )
    actions.append(
        UserOperation(
            action_type=MulticallActionType.MORPHO_DEPOSIT,
            body=MorphoDepositParams(
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
# CODE END
