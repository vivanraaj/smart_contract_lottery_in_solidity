from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
import pytest


def test_get_entrance_fee():
    # line above only done when in develpment
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # 2000 eth/usd
    # usdEntryFee is 50
    # 2000/1  == 50/x == 0.025
    expected_entrance_fee = Web3.toWei(0.25, "ether")
    entrance_fee = lottery.getEntranceFee()
    # Assert
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_starter():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # Act
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert (
        lottery.players(0) == account
    )  # we checking players array and it is pushed correctly


def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(
        lottery
    )  # this func need to be called as it has the fulfillRandomness function
    lottery.endLottery({"from": account})
    assert lottery.lottery_state() == 2


# test the fullfill function work correctly
def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})  # player 1
    lottery.enter(
        {"from": get_account(index=1), "value": lottery.getEntranceFee()}
    )  # player 2
    lottery.enter(
        {"from": get_account(index=2), "value": lottery.getEntranceFee()}
    )  # player 3
    fund_with_link(lottery)
    # now choose lottery
    # to test the fulfillrandomness function
    # we notice that the VRFCoordinatorMock calls the fulfillRandomness function
    # we cannot access the end_lottery function as it has no return
    # so we do a  "event"
    # now we can listen to the emitted event
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"][
        "requestId"
    ]  # call the requestID in the requestrandomness function
    # we pretend like a chainlink node to get the random number?
    # below we pretend as the vrf coordinator
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )

    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    # 777%3=0
    # so asnwer should be zero
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery
