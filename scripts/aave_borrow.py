from brownie import network, config, interface
from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
from web3 import Web3

AMOUNT = Web3.toWei(0.01, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]

    # get_weth()

    lending_pool = get_lending_pool()
    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)

    print("Depositing...")
    tx = lending_pool.deposit(
        erc20_address, AMOUNT, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited!")

    borrowable_eth, total_collateral, total_debt = get_borrowable_data(
        lending_pool, account
    )

    dai_eth_price_feed = config["networks"][network.show_active()]["dai_eth_price_feed"]
    dai_eth_price = get_asset_price(dai_eth_price_feed)

    borrowable_dai = (1 / dai_eth_price) * (borrowable_eth * 0.5)

    print(f"We can borrow {borrowable_dai} DAI!!")

    dai_address = config["networks"][network.show_active()]["dai_token_address"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(borrowable_dai, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)

    print("Borrowed some DAI!!!")

    get_borrowable_data(lending_pool, account)  # print

    return float(dai_eth_price)


def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.IAggregatorV3(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_price}")
    return float(converted_price)


def get_borrowable_data(lending_pool, account):
    (
        totalCollateralETH,
        totalDebtETH,
        availableBorrowsETH,
        currentLiquidationThreshold,
        ltv,
        healthFactor,
    ) = lending_pool.getUserAccountData(account.address)

    available_borrow_eth = Web3.fromWei(availableBorrowsETH, "ether")
    total_collateral_eth = Web3.fromWei(totalCollateralETH, "ether")
    total_debt_eth = Web3.fromWei(totalDebtETH, "ether")

    print(
        f"Available to borrow: {available_borrow_eth}, Total collateral: {total_collateral_eth}, Total debt: {total_debt_eth}"
    )

    return (
        float(available_borrow_eth),
        float(total_collateral_eth),
        float(total_debt_eth),
    )


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    print(lending_pool)
    return lending_pool
