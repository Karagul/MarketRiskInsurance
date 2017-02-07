# -*- coding: utf-8 -*-
"""=============================================================================
This modules contains the variables and the parameters.
Do not change the variables.
Parameters that can be changed without any risk of damages should be changed
by clicking on the configure sub-menu at the server screen.
If you need to change some parameters below please be sure of what you do,
otherwise ask to the developer ;-)
============================================================================="""
from __future__ import division
from datetime import time
from random import random


# variables DO NOT TOUCH -------------------------------------------------------
P_2 = 0
P_2_RANDOM = 1
TREATMENTS_NAMES = {P_2: u"P2", P_2_RANDOM: u"P_2_RANDOM"}
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
# dictionary that will store the endowments of each group
INCOMES = dict()

# parameters -------------------------------------------------------------------
TREATMENT = P_2
MARKET_TIME = time(0, 3, 0)  # hour, minute, second
SUMMARY_TIME = time(0, 1, 30)  # timer on the summary screen
PROB_TRIANGLE = 50  # An integer between 1 and 100
TRIANGLE_PAY = 1  # amount payed by the seller if the event is TRIANGLE
STAR_PAY = 1  # amount payed by the seller if the event is STAR
DECIMALS = 2
OFFER_MAX = 100
BALANCE_THRESHOLD = 0
PERIODE_ESSAI = False

NOMBRE_PERIODES = 11
TAILLE_GROUPES = 8
#NUMBER_OF_PAID_PERIODS = 3
AMOUNT_TO_SUBTRACT = 27
TAUX_CONVERSION = 1
MONNAIE = u"euro"


def format_value(val):
    try:
        return float("{:.2f}".format(val))
    except ValueError:
        return val


# Endowments
def get_incomes():
    incomes = list()
    if TREATMENT == P_2:
        incomes = zip((10.14, 3.38) * (TAILLE_GROUPES // 2),
                         (3.38, 10.14) * (TAILLE_GROUPES // 2))

    elif TREATMENT == P_2_RANDOM:
        def get_random_values():
            radius = 4.3
            my_list = [0]
            my_list.extend(
                sorted([random() for _ in range(TAILLE_GROUPES // 2 - 1)]))
            my_list.append(1)
            my_list_diff = [my_list[i] - my_list[i - 1] for i in
                            range(1, TAILLE_GROUPES // 2 + 1)]
            my_list_norm = [e - 1 / (TAILLE_GROUPES // 2) for e in my_list_diff]
            my_list_incomes = list()
            for i in range(TAILLE_GROUPES // 2):
                my_list_incomes.append(
                    (format_value(10.14 + radius * my_list_norm[i]),
                     format_value(3.38 - radius * my_list_norm[i])))
                my_list_incomes.append((format_value(
                    3.38 - radius * my_list_norm[i]), format_value(
                    10.14 + radius * my_list_norm[i])))
            return my_list_incomes
        incomes = get_random_values()
    return incomes
