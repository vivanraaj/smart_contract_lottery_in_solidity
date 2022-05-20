from scripts.helpful_scripts import get_account, get_contract, fund_with_link
from brownie import Lottery, network, config
import time


def deploy_lottery():
    account = get_account()
    # if look at lottery.sol, there is parameters to be inserted
    # below return actual contract and we want the address
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("Deployed lottery!")
    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]  # the most recent deployment
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)  # need to do this otherwise it hangs?
    print("The lottery is started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 10000000000
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You entered the lottery!")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # need some LINK token as there is call randomness in end loter
    # fund the contract
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    time.sleep(60)  # above transaction takes time so we take time off?
    print(
        f"{lottery.recentWinner()} is the new winner!"
    )  # although recent winner is not
    ## a function, you can still call it this way coz its an event?


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()  # should be no winner in local blockchain as the fullfill randomness function is not called by chainlink node
