# -*- coding: utf-8 -*-
"""=============================================================================
This modules contains the variables and the parameters.
Do not change the variables.
Parameters that can be changed without any risk of damages should be changed
by clicking on the configure sub-menu at the server screen.
If you need to change some parameters below please be sure of what you do,
otherwise ask to the developer ;-)
============================================================================="""
from datetime import time

# variables --------------------------------------------------------------------
MARKET_CONTRACT = 0
MARKET_SWAP = 1
TREATMENTS_NAMES = {MARKET_CONTRACT: u"Contract", MARKET_SWAP: u"Swap"}
BUY = BUYER = 0
SELL = SELLER = 1
# status of propositions
IN_PROGRESS = 0
TRANSACTION = 1
DELETED = 2
DEPRECATED = 3
# events
TRIANGLE = 0
STAR = 1
# sender_type
PRICE_TAKER = 0
PRICE_MAKER = 1

# parameters -------------------------------------------------------------------
TREATMENT = MARKET_CONTRACT
MARKET_TIME = time(0, 1, 0)  # hour, minute, second
ENDOWMENT = 10
TRIANGLE_PAY = 1  # amount payed by the seller if the event is TRIANGLE
STAR_PAY = 1  # amount payed by the seller if the event is STAR
DECIMALS = 2
OFFER_MAX = 100
BALANCE_THRESHOLD = 0

NOMBRE_PERIODES = 1
TAILLE_GROUPES = 2
PERIODE_ESSAI = False

TAUX_CONVERSION = 1
MONNAIE = u"euro"


