# -*- coding: utf-8 -*-

import logging
import random
from time import strftime, localtime
from twisted.internet import defer
from twisted.spread import pb
from client.cltremote import IRemote
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceGui import GuiDecision, GuiRecapitulatif
import MarketRiskInsuranceTexts as texts_MRI


logger = logging.getLogger("le2m")


class RemoteMRI(IRemote):
    """
    Class remote, remote_ methods can be called by the server
    """
    def __init__(self, le2mclt):
        IRemote.__init__(self, le2mclt)
        self.balance = 0
        self.balance_if_triangle = 0
        self.balance_if_star = 0
        self.histo.append(texts_MRI.get_histo_head())
        self.histo_vars = texts_MRI.get_histo_vars()

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

    def remote_newperiod(self, period):
        """
        Set the current period and delete the history
        :param period: the current period
        :return:
        """
        logger.info(u"{} Period {}".format(self._le2mclt.uid, period))
        self.currentperiod = period
        if self.currentperiod == 1:
            self.balance = self.balance_if_triangle = \
                self.balance_if_star = pms.ENDOWMENT
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
        self._decision_screen.show()
        self._decision_screen.update_balance(self.balance,
                                             self.balance_if_triangle,
                                             self.balance_if_star)
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
        offer["MRI_offer_time"] = strftime("%X", localtime())
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
        new_offer["MRI_offer_time"] = strftime("%X", localtime())
        yield(self._server_part.callRemote("add_transaction",
                                           existing_offer, new_offer))

    def remote_add_transaction(self, transaction):
        logger.debug(u"Received a transaction to display: {}".format(transaction))
        self._decision_screen.add_transaction(transaction)

    @defer.inlineCallbacks
    def remote_update_balance(self, balance, balance_if_triangle,
                              balance_if_star):
        """
        Update the information zone and also remove the offers in the player's
        lists that are no more possible
        :param balance:
        :param balance_if_triangle:
        :param balance_if_star:
        :return:
        """
        logger.debug(u"Update of balance: {} - {} - {}".format(
            balance, balance_if_triangle, balance_if_star))
        self.balance = balance
        self.balance_if_triangle = balance_if_triangle
        self.balance_if_star = balance_if_star
        yield (self._decision_screen.update_balance(
            balance, balance_if_triangle, balance_if_star))

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
            if self.balance - offer["MRI_offer_price"] < pms.BALANCE_THRESHOLD:
                return False
        else:
            if offer["MRI_offer_contract"] == pms.TRIANGLE:
                if self.balance_if_triangle - pms.TRIANGLE_PAY < \
                        pms.BALANCE_THRESHOLD:
                    return False
            else:
                if self.balance_if_star - pms.STAR_PAY < pms.BALANCE_THRESHOLD:
                    return False
        return True

    def remote_display_summary(self, period_content, transactions_group):
        """
        Display the summary screen
        :param period_content: dictionary with the content of the current period
        :return: deferred
        """
        logger.info(u"{} Summary".format(self._le2mclt.uid))
        self.histo.append([period_content.get(k) for k in self.histo_vars])
        # replace event code by text
        self.histo[-1][10] = texts_MRI.get_event_str(self.histo[-1][10])
        logger.debug(u"Ligne histo: {}".format(self.histo[-1]))
        if self._le2mclt.simulation:
            return 1
        else:
            defered = defer.Deferred()
            ecran_recap = GuiRecapitulatif(
                defered, self._le2mclt.automatique, self._le2mclt.screen,
                self.currentperiod, self.histo,
                texts_MRI.get_text_summary(period_content),
                size_histo=(1200, 100))
            ecran_recap.show()
            return defered
