import time
import json
import prettytable
from modules import *
from web3 import Web3
from termcolor import colored
import requests

with open('keys.txt', 'r') as myfile:
    keys = json.load(myfile)

w3 = Web3(Web3.HTTPProvider(keys['infura-api']))
if w3.isConnected():
    print("The bot is connected to the ethereum network")
else:
    print("The bot can't connect to the eth network")
    quit()


def getAccountLiquidity(addy):
    unitroller = keys["unitroller"]
    abisite = keys["abi"]
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


def token_symbol(tokenname):
    if tokenname == "0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e":
        return "BAT"
    if tokenname == "0xf5dce57282a584d2746faf1593d3121fcac444dc":
        return "DAI"
    if tokenname == "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5":
        return "Ξ"
    if tokenname == "0x158079ee67fce2f58472a96584a73c7ab9ac95c1":
        return "REP"
    if tokenname == "0x39aa39c021dfbae8fac545936693ac917d5e7563":
        return "USDC"
    if tokenname == "0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407":
        return "ZRX"
    if tokenname == "0xc11b1268c1a384e55c48c2391d8d480264a3a7f4":
        return "wBTC"
    if tokenname == "0x5d3a536e4d6dbd6114cc1ead35777bab948e3643":
        return "cDAI"


def api():
    global response
    site = "https://api.compound.finance/api/v2/account"
    params = {
        "page_size": 20,
        "min_borrow_value_in_eth": {"value": "1.0"}
    }
    try:
        req = requests.post(site, data=json.dumps(params))
        response = req.json()
    except Exception as e:
        response = []
        print(e)
    return response


def parse():
    x = prettytable.PrettyTable()
    x.field_names = ["Address", "Health", "B. ETH", "B.Tokens", "Supply", "Estimated profit", "On Chain Liquidity"]

    req = requests.get("https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD").json()

    account_list = api()
    eth_price = req
    usd_eth = float(eth_price["USD"])

    for account in account_list["accounts"]:
        balance2 = ''
        balance3 = ''
        address = account["address"]
        onchainliquidity = getAccountLiquidity(address)
        try:
            health = float(account["health"]["value"])
        except Exception as e:
            health = 0
        beth = float(account["total_borrow_value_in_eth"]["value"])
        beth_format = "{:.8f} Ξ".format(round(beth, 8)) + "\n" + colored("{:.3f}".format(round(usd_eth * beth, 3)) + "$",
                                                                         'green')
        estimated_p = "{:.3f}".format(((usd_eth * beth) / 2) * 0.05) + "$"
        tokens = account["tokens"]
        for token in tokens:
            balance_borrow = token["borrow_balance_underlying"]["value"]
            balance_supply = token["supply_balance_underlying"]["value"]
            token_address = token["address"]
            if float(balance_supply) > 0:
                bresult_supply = "{:.8f} ".format(round(float(balance_supply), 8)) + token_symbol(token_address)
                balance3 += bresult_supply + "\n"
            if float(balance_borrow) > 0:
                bresult_borrow = "{:.8f} ".format(round(float(balance_borrow), 8)) + token_symbol(token_address)
                balance2 += bresult_borrow + "\n"
        x.add_row(
            [address, round(health, 3), beth_format, balance2, balance3, colored(estimated_p, 'green', attrs=['bold']),
             onchainliquidity])
        if (((usd_eth * beth) / 2) * 0.05 > 10) and (onchainliquidity == colored("NOT SAFU", 'red', attrs=['bold'])):
            pass
    print(x)
    time.sleep(20)
