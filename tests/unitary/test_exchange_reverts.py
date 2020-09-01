import itertools

import brownie
import pytest

from tests.conftest import PRECISIONS

INITIAL_AMOUNTS = [10**(i+6) for i in PRECISIONS]


@pytest.fixture(scope="module", autouse=True)
def setup(alice, bob, bank, coins, swap):
    for coin, amount in zip(coins[:-1], INITIAL_AMOUNTS[:-1]):
        coin._mint_for_testing(alice, amount, {'from': alice})
        coin.approve(swap, 2**256-1, {'from': alice})
        coin.approve(swap, 2**256-1, {'from': bob})
        coin._mint_for_testing(bank, amount, {'from': bank})

    # Leave Alice 1 million of metacoins
    coins[-1].transfer(
            bank, coins[-1].balanceOf(alice) - INITIAL_AMOUNTS[-1],
            {'from': alice})
    coins[-1].approve(swap, 2**256-1, {'from': alice})
    coins[-1].approve(swap, 2**256-1, {'from': bob})

    swap.add_liquidity(INITIAL_AMOUNTS, 0, {'from': alice})


@pytest.mark.parametrize("sending,receiving", itertools.permutations([0, 1], 2))
def test_insufficient_balance(bob, bank, swap, coins, sending, receiving):
    amount = 10**PRECISIONS[sending]
    coins[sending].transfer(bob, amount, {'from': bank})

    with brownie.reverts():
        swap.exchange(sending, receiving, amount+1, 0, {'from': bob})


@pytest.mark.parametrize("sending,receiving", itertools.permutations([0, 1], 2))
def test_min_dy_too_high(bob, bank, swap, coins, sending, receiving):
    amount = 10**PRECISIONS[sending]
    coins[sending].transfer(bob, amount, {'from': bank})

    min_dy = swap.get_dy(sending, receiving, amount)
    with brownie.reverts("Exchange resulted in fewer coins than expected"):
        swap.exchange(sending, receiving, amount, min_dy+1, {'from': bob})


@pytest.mark.parametrize("idx", range(2))
def test_same_coin(bob, swap, coins, idx):
    with brownie.reverts("dev: same coin"):
        swap.exchange(idx, idx, 0, 0, {'from': bob})


@pytest.mark.parametrize("idx", [-1, -2**127])
def test_i_below_zero(bob, swap, coins, idx):
    with brownie.reverts():
        swap.exchange(idx, 0, 0, 0, {'from': bob})


@pytest.mark.parametrize("idx", [3, 2**127-1])
def test_i_above_n_coins(bob, swap, coins, idx):
    with brownie.reverts():
        swap.exchange(idx, 0, 0, 0, {'from': bob})


@pytest.mark.parametrize("idx", [-1, -2**127])
def test_j_below_zero(bob, swap, coins, idx):
    with brownie.reverts("dev: j below zero"):
        swap.exchange(0, idx, 0, 0, {'from': bob})


@pytest.mark.parametrize("idx", [3, 2**127-1])
def test_j_above_n_coins(bob, swap, coins, idx):
    with brownie.reverts("dev: j above N_COINS"):
        swap.exchange(0, idx, 0, 0, {'from': bob})
