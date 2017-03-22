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
P_6 = 2
P_6_RANDOM = 3
TREATMENTS_NAMES = {
    P_2: u"P2", P_2_RANDOM: u"P_2_RANDOM",
    P_6: u"P_6", P_6_RANDOM: u"P_6_RANDOM"
}
TREATMENTS_PROFILES = {
    P_2: [(10.14, 3.38), (3.38, 10.14)],
    P_6: [(8.07, 5.19), (10.06, 3.62)]
}
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


def __format_value(val):
    try:
        return float("{:.2f}".format(val))
    except ValueError:
        return val


def __get_fixed_incomes(profil_A, profil_B):
    half_groups = TAILLE_GROUPES // 2
    return [profil_A for _ in range(half_groups)] + \
           [profil_B for _ in range(half_groups)]


def __get_random_incomes(profil_A, profil_B, radius):
    try:
        radius_A, radius_B = radius
    except ValueError:
        radius_A = radius_B = radius[0]
    except TypeError:
        radius_A = radius_B = radius
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
            (__format_value(profil_A[0] + radius_A * my_list_norm[i]),
             __format_value(profil_A[1] - radius_A * my_list_norm[i])))
        my_list_incomes.append((__format_value(
            profil_B[0] - radius_B * my_list_norm[i]), __format_value(
            profil_B[1] + radius_B * my_list_norm[i])))
    return my_list_incomes


# Endowments
def get_incomes():
    incomes = list()
    if TREATMENT == P_2:
        incomes = __get_fixed_incomes(*TREATMENTS_PROFILES[P_2])
    elif TREATMENT == P_6:
        incomes = __get_fixed_incomes(*TREATMENTS_PROFILES[P_6])

    elif TREATMENT == P_2_RANDOM:
        incomes = __get_random_incomes(
            profil_A=TREATMENTS_PROFILES[P_2][0],
            profil_B=TREATMENTS_PROFILES[P_2][1], radius=4.3)
    elif TREATMENT == P_6_RANDOM:
        incomes = __get_random_incomes(
            profil_A=TREATMENTS_PROFILES[P_6][0],
            profil_B=TREATMENTS_PROFILES[P_6][1],
            radius=(2, 4))
    return incomes
