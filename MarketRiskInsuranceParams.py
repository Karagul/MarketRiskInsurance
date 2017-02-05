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
from random import randint

# variables --------------------------------------------------------------------
FIVE_TEN_FIX = 0
FIVE_TEN_RANDOM = 1
TREATMENTS_NAMES = {FIVE_TEN_FIX: u"5_10_FIX", FIVE_TEN_RANDOM: u"5_10_RANDOM"}
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
TREATMENT = FIVE_TEN_FIX
MARKET_TIME = time(0, 1, 0)  # hour, minute, second
PROB_TRIANGLE = 50  # An integer between 1 and 100
TRIANGLE_PAY = 1  # amount payed by the seller if the event is TRIANGLE
STAR_PAY = 1  # amount payed by the seller if the event is STAR
DECIMALS = 2
OFFER_MAX = 100
BALANCE_THRESHOLD = 0
PERIODE_ESSAI = False

NOMBRE_PERIODES = 5
TAILLE_GROUPES = 8
NUMBER_OF_PAID_PERIODS = 3

TAUX_CONVERSION = 1
MONNAIE = u"euro"


# Endowments
def get_endowments():
    endowments = list()
    if TREATMENT == FIVE_TEN_FIX:
        endowments = zip((5, 10) * (TAILLE_GROUPES / 2),
                         (10, 5) * (TAILLE_GROUPES / 2))

    elif TREATMENT == FIVE_TEN_RANDOM:
        def get_values():
            values = []
            while sum(values) != (7.5 * TAILLE_GROUPES):
                del values[:]
                for _ in range(TAILLE_GROUPES):
                    values.append(randint(5, 10))
            return values
        endowments = zip(get_values(), get_values())
    return endowments

ENDOWMENTS = get_endowments()