import time
import json
import prettytable
from web3 import Web3
from termcolor import colored
import requests
import math

with open('config.json', 'r') as myfile:
    keys = json.load(myfile)

w3 = Web3(Web3.HTTPProvider(keys['infura-api']))
if w3.isConnected():
    print("The bot is connected to the ethereum network")
else:
    print("The bot can't connect to the eth network")
    quit()


def getAccountLiquidity(addy):
    """
    查询账户的健康值是否安全
    :param addy: 账户地址
    :return: str
    """
    unitroller = keys["unitroller"]
    abisite = keys["unitroller_abi"]
    abi = requests.get(abisite).json()
    contract = w3.eth.contract(address=unitroller, abi=abi)
    caddress = w3.toChecksumAddress(addy)
    result = contract.functions.getAccountLiquidity(caddress).call()
    if result[0] != 0:
        return "There is an error Whoops"
    elif result[1] != 0:
        return colored("SAFU", 'green')
    elif result[2] != 0:
        return colored("NOT SAFU", 'red', attrs=['bold'])


def liquidateBorrow(targetAccount, assetBorrow, assetCollateral, requestedAmountClose):
    """

    :param targetAccount: 被清算的地址
    :param assetBorrow: 借贷币种的地址
    :param assetCollateral: 抵押币种的地址
    :param requestedAmountClose: 清算金额
    :return:
    """
    my_account = w3.eth.account.from_key(keys['account']['private_key'])
    liquidator = keys["liquidator"]
    liquidator_abi = keys["liquidator_abi"]
    abi = requests.get(liquidator_abi).json()
    contract = w3.eth.contract(address=liquidator, abi=abi)
    targetaccount_caddress = w3.toChecksumAddress(targetAccount)
    assetborrow_caddress = w3.toChecksumAddress(assetBorrow)
    assetcollateral_caddress = w3.toChecksumAddress(assetCollateral)
    txn = contract.functions.liquidateBorrow(targetaccount_caddress, assetborrow_caddress, assetcollateral_caddress,
                                             requestedAmountClose).buildTransaction(
        {'from': my_account.address, 'nonce': w3.eth.getTransactionCount(my_account.address)})
    signed = my_account.signTransaction(txn)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    return tx_hash.hex()


def CEtherliquidateBorrow(borrower, ctokencollateral):
    """

    :param borrower:
    :param ctokencollateral:
    :return:
    """
    my_account = w3.eth.account.from_key(keys['account']['private_key'])
    liquidator = keys["ceth_liquidator"]
    liquidator_abi = keys["ceth_liquidator_abi"]
    abi = requests.get(liquidator_abi).json()
    contract = w3.eth.contract(address=liquidator, abi=abi)
    borrower_caddress = w3.toChecksumAddress(borrower)
    ctokencollateral_caddress = w3.toChecksumAddress(ctokencollateral)
    txn = contract.functions.liquidateBorrow(borrower_caddress, ctokencollateral_caddress).buildTransaction(
        {'from': my_account.address, 'nonce': w3.eth.getTransactionCount(my_account.address)})
    signed = my_account.signTransaction(txn)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    return tx_hash.hex()


def CErc20liquidateBorrow(borrowtoken, borrower, repayamount, ctokencollateral):
    """

    :param borrowtoken:
    :param borrower:
    :param repayamount:
    :param ctokencollateral:
    :return:
    """
    base_abi = "http://api.etherscan.io/api?module=contract&action=getabi&address=%s&format=raw"
    my_account = w3.eth.account.from_key(keys['account']['private_key'])
    liquidator = borrowtoken
    liquidator_abi = keys["cerc20_dict"][liquidator]["abi"]
    abi = requests.get(base_abi % liquidator_abi).json()
    contract = w3.eth.contract(address=liquidator, abi=abi)
    borrower_caddress = w3.toChecksumAddress(borrower)
    ctokencollateral_caddress = w3.toChecksumAddress(ctokencollateral)
    repayamount *= math.pow(10, keys["cerc20_dict"][liquidator]["precise"])
    txn = contract.functions.liquidateBorrow(borrower_caddress, repayamount,
                                             ctokencollateral_caddress).buildTransaction(
        {'from': my_account.address, 'nonce': w3.eth.getTransactionCount(my_account.address)})
    signed = my_account.signTransaction(txn)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    return tx_hash.hex()


def api():
    """
    commpound 账户信息
    :return: 账户信息列表, str
    """
    global response
    site = "https://api.compound.finance/api/v2/account"
    params = {
        "page_size": keys['page_size'],
        "min_borrow_value_in_eth": {"value": keys['min_borrow_value_in_eth']},
        "max_health": {"value": keys["max_health"]}
    }
    try:
        req = requests.post(site, data=json.dumps(params))
        response = req.json()
    except Exception as e:
        response = []
        print(e)
    return response


def tokenToAddress(token):
    if token == "cUSDC":
        return "0x39aa39c021dfbae8fac545936693ac917d5e7563"
    if token == "cETH":
        return "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5"


def parse():
    """
    格式化账户信息，并输出
    :return:
    """
    x = prettytable.PrettyTable()
    x.field_names = ["Address", "Health", "B. ETH", "B.Tokens", "Supply", "Estimated profit", "On Chain Liquidity"]

    req = requests.get("https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD").json()

    account_list = api()
    eth_price = req
    usd_eth = float(eth_price["USD"])

    for account in account_list["accounts"]:
        balance2 = ''
        balance3 = ''
        borrow_tokens = {}
        supply_tokens = {}
        address = account["address"]
        onchainliquidity = getAccountLiquidity(address)
        try:
            health = float(account["health"]["value"])
        except Exception as e:
            health = 0
        beth = float(account["total_borrow_value_in_eth"]["value"])
        beth_format = "{:.8f} ETH".format(round(beth, 8)) + "\n" + colored(
            "{:.3f}".format(round(usd_eth * beth, 3)) + "$",
            'green')
        if (usd_eth * beth) / 2 * 0.05 < keys['profit']:
            continue
        estimated_p = "{:.3f}".format((usd_eth * beth) / 2 * 0.05) + "$"
        tokens = account["tokens"]
        for token in tokens:
            balance_borrow = token["borrow_balance_underlying"]["value"]
            balance_supply = token["supply_balance_underlying"]["value"]
            token_symbol = token['symbol']
            if float(balance_supply) > 0:
                bresult_supply = "{:.8f} ".format(round(float(balance_supply), 8)) + token_symbol
                balance3 += bresult_supply + "\n"
                supply_tokens[token_symbol] = round(float(balance_supply), 8)
            if float(balance_borrow) > 0:
                bresult_borrow = "{:.8f} ".format(round(float(balance_borrow), 8)) + token_symbol
                balance2 += bresult_borrow + "\n"
                borrow_tokens[token_symbol] = round(float(balance_borrow), 8)

        if len(supply_tokens.keys()) == 1 and supply_tokens.keys()[0] == keys['supply_token'] and \
                len(borrow_tokens.keys()) == 1 and borrow_tokens.keys()[0] == keys['borrow_token']:
            if borrow_tokens.keys()[0] == "cETH":
                tx_hash = CEtherliquidateBorrow(address, tokenToAddress(supply_tokens.keys()[0]))
            else:
                tx_hash = CErc20liquidateBorrow(tokenToAddress(borrow_tokens.keys()[0]), address, borrow_tokens.values()[0], tokenToAddress(supply_tokens.keys()[0]))
            print("交易ID: %s" % tx_hash)
        x.add_row(
            [address, round(health, 3), beth_format, balance2, balance3, colored(estimated_p, 'green', attrs=['bold']),
             onchainliquidity])

    print(x)
    time.sleep(20)
