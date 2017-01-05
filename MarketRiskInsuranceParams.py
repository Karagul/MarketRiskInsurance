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
TRIANGLE_PAY = 100  # amount payed by the seller if the event is TRIANGLE
STAR_PAY = 100  # amount payed by the seller if the event is STAR


# parameters -------------------------------------------------------------------
TREATMENT = MARKET_CONTRACT
MARKET_TIME = time(0, 2, 0)  # hour, minute, second
DECIMALS = 2
OFFER_MAX = 500

NOMBRE_PERIODES = 10
TAILLE_GROUPES = 4
PERIODE_ESSAI = False

TAUX_CONVERSION = 1
MONNAIE = u"ecu"


