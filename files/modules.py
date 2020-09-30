import time
import json
import prettytable
from web3 import Web3
from termcolor import colored
import requests

with open('config.json', 'r') as myfile:
    keys = json.load(myfile)

w3 = Web3(Web3.HTTPProvider(keys['infura-api']))
if w3.isConnected():
    print("The bot is connected to the ethereum network")
else:
    print("The bot can't connect to the eth network")
    quit()


def getAccountLiquidity(addy):
    '''
    查询账户的健康值是否安全
    :param addy: 账户地址
    :return: str
    '''
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


def api():
    '''
    commpound 账户信息
    :return: 账户信息列表, str
    '''
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


def parse():
    '''
    格式化账户信息，并输出
    :return:
    '''
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
        beth_format = "{:.8f} ETH".format(round(beth, 8)) + "\n" + colored("{:.3f}".format(round(usd_eth * beth, 3)) + "$",
                                                                         'green')
        estimated_p = "{:.3f}".format(((usd_eth * beth) / 2) * 0.05) + "$"
        tokens = account["tokens"]
        for token in tokens:
            balance_borrow = token["borrow_balance_underlying"]["value"]
            balance_supply = token["supply_balance_underlying"]["value"]
            token_symbol = token['symbol']
            if float(balance_supply) > 0:
                bresult_supply = "{:.8f} ".format(round(float(balance_supply), 8)) + token_symbol
                balance3 += bresult_supply + "\n"
            if float(balance_borrow) > 0:
                bresult_borrow = "{:.8f} ".format(round(float(balance_borrow), 8)) + token_symbol
                balance2 += bresult_borrow + "\n"
        x.add_row(
            [address, round(health, 3), beth_format, balance2, balance3, colored(estimated_p, 'green', attrs=['bold']),
             onchainliquidity])
        if (((usd_eth * beth) / 2) * 0.05 > 10) and (onchainliquidity == colored("NOT SAFU", 'red', attrs=['bold'])):
            pass
    print(x)
    time.sleep(20)
