# -*- coding: utf-8 -*-

import logging
import random
import datetime
#from time import strftime, localtime
from twisted.internet import defer
from twisted.spread import pb
from client.cltremote import IRemote
import pandas as pd
import numpy as np
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceGui import GuiDecision, GuiRecapitulatif
import MarketRiskInsuranceTexts as texts_MRI


logger = logging.getLogger("le2m")


def get_formated_value(value):
    if value > 0:
        return "+{:.2f}".format(value)
    else:
        return value


class RemoteMRI(IRemote):
    """
    Class remote, remote_ methods can be called by the server
    """
    def __init__(self, le2mclt):
        IRemote.__init__(self, le2mclt)
        self.balance_if_triangle = 0
        self.balance_if_star = 0
        self.histo.append(texts_MRI.get_histo_head())
        self.histo_vars = texts_MRI.get_histo_vars()
        self.currentperiod_start_time = 0

    def remote_configure(self, params, server_part):
        """
        Set the same parameters as in the server side
        :param params:
        :return:
        """
        logger.info(u"{} configure".format(self._le2mclt.uid))
        for k, v in params.viewitems():
            setattr(pms, k, v)
        self._server_part = server_part

    def remote_newperiod(self, period, endowments):
        """
        Set the current period and delete the history
        :param period: the current period
        :return:
        """
        logger.info(u"{} Period {}".format(self._le2mclt.uid, period))
        self.currentperiod = period
        self.currentperiod_start_time = datetime.datetime.now()
        self.balance_if_triangle = endowments[0]
        self.balance_if_star = endowments[1]
        if self.currentperiod == 1:
            del self.histo[1:]

    def remote_display_decision(self):
        """
        Display the decision screen.
        No simulation mode
        :return: deferred
        """
        logger.info(u"{} Decision".format(self._le2mclt.uid))
        defered = defer.Deferred()
        self._decision_screen = GuiDecision(
            defered, self._le2mclt.automatique,
            self._le2mclt.screen, self.currentperiod, self.histo, self)
        self._decision_screen.showFullScreen()
        self._decision_screen.update_balance(
            self.balance_if_triangle, self.balance_if_star)
        return defered

    @defer.inlineCallbacks
    def add_offer(self, offer):
        """
        send the offer to the server part
        called by the decision screen (method _send_offer)
        :param offer:
        :return:
        """
        offer["MRI_offer_sender"] = self.le2mclt.uid
        offer["MRI_offer_time"] = datetime.datetime.now().strftime("%H:%M:%S")
        yield (self._server_part.callRemote("add_offer", offer))

    def remote_add_offer(self, offer):
        """
        Add the offer to the corresponding list on the decision decision
        Called by the server part
        :param offer:
        :return:
        """
        logger.debug(u"Received an offer to display: {}".format(offer))
        self._decision_screen.add_offer(offer)

    @defer.inlineCallbacks
    def remove_offer(self, offer):
        """
        send the order to the server part to remove the offer on the group
        members screen
        Called by the screen with the remove my offer button
        :param offer:
        :return:
        """
        offer["MRI_offer_sender"] = self.le2mclt.uid
        yield (self._server_part.callRemote("remove_offer", offer))

    def remote_remove_offer(self, offer):
        """
        Remove the offer from the corresponding list
        Called by the server part
        :param offer:
        :return:
        """
        logger.debug(u"Remove the offer: {}".format(offer))
        self._decision_screen.remove_offer(offer)

    @defer.inlineCallbacks
    def add_transaction(self, existing_offer, new_offer):
        """
        send the elements for a new transaction to the server
        Called by the decision screen when the subject click on accept
        the selected offer
        :param existing_offer:
        :param new_offer:
        :return:
        """
        new_offer["MRI_offer_sender"] = self.le2mclt.uid
        new_offer["MRI_offer_time"] = datetime.datetime.now().strftime("%H:%M:%S")
        yield(self._server_part.callRemote("add_transaction",
                                           existing_offer, new_offer))

    def remote_add_transaction(self, transaction):
        logger.debug(u"Received a transaction to display: {}".format(transaction))
        self._decision_screen.add_transaction(transaction)

    @defer.inlineCallbacks
    def remote_update_balance(self, balance_if_triangle, balance_if_star):
        """
        Update the information zone and also remove the offers in the player's
        lists that are no more possible
        :param balance:
        :param balance_if_triangle:
        :param balance_if_star:
        :return:
        """
        logger.debug(u"Update of balance: {} - {}".format(
            balance_if_triangle, balance_if_star))
        self.balance_if_triangle = balance_if_triangle
        self.balance_if_star = balance_if_star
        yield (self._decision_screen.update_balance(
            balance_if_triangle, balance_if_star))

    def is_offer_ok(self, offer):
        """
        Check whether the subject can make this offer.
        If this is a purchase we just check he can pay the price.
        If this is a sell then we check that he can pay in case the event is
        the one of the contract in this offer (because in that case he has to
        pay).
        Called by the decision screen, just after the creation of a new offer,
        i.e. by add_offer and accept_selected_offer
        :param offer:
        :return:
        """
        if offer["MRI_offer_type"] == pms.BUY:
            if self.balance_if_triangle - offer["MRI_offer_price"] < \
                    pms.BALANCE_THRESHOLD or \
                self.balance_if_star - offer["MRI_offer_price"] < \
                    pms.BALANCE_THRESHOLD:
                return False

        else:
            if offer["MRI_offer_contract"] == pms.TRIANGLE:
                if self.balance_if_triangle + offer["MRI_offer_price"] - \
                        pms.TRIANGLE_PAY < pms.BALANCE_THRESHOLD:
                    return False
            else:
                if self.balance_if_star + offer["MRI_offer_price"] - \
                        pms.STAR_PAY < pms.BALANCE_THRESHOLD:
                    return False
        return True

    def get_hypothetical_balance(self, offer, accept=False):
        """
        Give the hypothetical income in the two states depending on the
        contract the offer is about and whether it is a BUY or a SELL
        :param offer:
        :param accept
        :return:
        """
        if accept: # if accept an offer then that offer is not the same type
            offer["MRI_offer_type"] = pms.BUY if \
                offer["MRI_offer_type"] == pms.SELL else pms.SELL

        if offer["MRI_offer_type"] == pms.BUY:
            if offer["MRI_offer_contract"] == pms.TRIANGLE:
                return "Variation de revenu:\nSi Triangle: {} | si Etoile: {}".format(
                    get_formated_value(- offer["MRI_offer_price"] + pms.TRIANGLE_PAY),
                    get_formated_value(- offer["MRI_offer_price"]))
            else:
                return "Variation de revenu:\nSi Triangle: {} | si Etoile: {}".format(
                    get_formated_value(- offer["MRI_offer_price"]),
                    get_formated_value(- offer["MRI_offer_price"] +
                    pms.STAR_PAY))

        else:  # SELL
            if offer["MRI_offer_contract"] == pms.TRIANGLE:
                return "Variation de revenu:\nSi Triangle: {} | si Etoile: {}".format(
                    get_formated_value(offer["MRI_offer_price"] - pms.TRIANGLE_PAY),
                    get_formated_value(offer["MRI_offer_price"]))
            else:
                return "Variation de revenu:\nSi Triangle: {} | si Etoile: {}".format(
                    get_formated_value(offer["MRI_offer_price"]),
                    get_formated_value(offer["MRI_offer_price"] - pms.STAR_PAY))

    def remote_display_summary(self, period_content, transactions_group):
        """
        Display the summary screen
        :param period_content: dictionary with the content of the current period
        :param transactions_group
        :return: deferred
        """
        logger.info("{} Summary".format(self.le2mclt.uid))
        logger.debug(u"{} Summary - transactions_group: {}".format(
            self._le2mclt.uid, transactions_group))

        if not transactions_group:
            group_transactions = pd.DataFrame(
                columns = ["MRI_trans_time", "MRI_trans_contract",
                           "MRI_trans_buyer", "MRI_trans_seller",
                           "MRI_trans_price"])
        else:
            group_transactions = pd.DataFrame(transactions_group)

        start_period = datetime.datetime.strptime(
            period_content["MRI_time_start"], "%H:%M:%S")

        try:  # if no transaction
            group_transactions.loc[:, "MRI_time_diff"] = np.NAN
            group_transactions.MRI_time_diff = group_transactions.apply(
                lambda line: (datetime.datetime.strptime(
                line.MRI_trans_time, "%H:%M:%S") - start_period).seconds, axis=1)
        except ValueError:
            group_transactions.loc[:, "MRI_time_diff"] = []

        # transactions
        triangle_transactions = group_transactions.loc[
                group_transactions.MRI_trans_contract == pms.TRIANGLE, ]
        # logger.debug(u"triangle_transactions: {}".format(triangle_transactions))
        star_transactions = group_transactions.loc[
            group_transactions.MRI_trans_contract == pms.STAR, ]
        # logger.debug(u"star_transactions: {}".format(star_transactions))

        # history
        self.histo.append([period_content.get(k) for k in self.histo_vars])
        # replace event code by text
        self.histo[-1][11] = texts_MRI.get_event_str(self.histo[-1][11])
        logger.debug(u"Ligne histo: {}".format(self.histo[-1]))

        # screen
        if self._le2mclt.simulation:
            return 1
        else:
            defered = defer.Deferred()
            ecran_recap = GuiRecapitulatif(
                self, defered, self._le2mclt.automatique, self._le2mclt.screen,
                self.currentperiod, self.histo,
                texts_MRI.get_text_summary(period_content),
                triangle_transactions, star_transactions)
            ecran_recap.showFullScreen()
            return defered

    # def remote_set_payoffs(self, in_euros, in_ecus=None,
    #                        payoffs_selected_periods=None):
    #     self.payoff_euros = in_euros
    #     self.payoff_ecus = in_ecus
    #     self.payoff_text = texts_MRI.get_payoff_text(
    #         self.payoff_euros, payoffs_selected_periods)
