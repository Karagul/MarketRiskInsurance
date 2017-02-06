# -*- coding: utf-8 -*-

from __future__ import division
import logging
from twisted.internet import defer
from twisted.spread import pb
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey
from server.servbase import Base
from server.servparties import Partie
from util.utiltools import get_module_attributes
import MarketRiskInsuranceParams as pms


logger = logging.getLogger("le2m")


class PartieMRI(Partie, pb.Referenceable):
    __tablename__ = "partie_MarketRiskInsurance"
    __mapper_args__ = {'polymorphic_identity': 'MarketRiskInsurance'}
    partie_id = Column(Integer, ForeignKey('parties.id'), primary_key=True)
    repetitions = relationship('RepetitionsMRI')

    def __init__(self, le2mserv, joueur):
        super(PartieMRI, self).__init__(
            nom="MarketRiskInsurance", nom_court="MRI",
            joueur=joueur, le2mserv=le2mserv)
        self.MRI_gain_ecus = 0
        self.MRI_gain_euros = 0

    @defer.inlineCallbacks
    def configure(self):
        logger.debug(u"{} Configure".format(self.joueur))
        yield (self.remote.callRemote("configure", get_module_attributes(pms),
                                      self))
        self.joueur.info(u"Ok")

    @defer.inlineCallbacks
    def newperiod(self, period, random_value):
        """
        Create a new period and inform the remote
        :param period: the current period number
        :param the random value drawn by the server
        :return:
        """
        logger.debug(u"{} New Period".format(self.joueur))
        self.currentperiod = RepetitionsMRI(period)
        self.le2mserv.gestionnaire_base.ajouter(self.currentperiod)
        self.repetitions.append(self.currentperiod)
        self.currentperiod.MRI_random_value = random_value
        self.currentperiod.MRI_event = pms.TRIANGLE if \
            random_value < (pms.PROB_TRIANGLE + 1) else \
            pms.STAR
        self.currentperiod.MRI_group = self.joueur.group
        player_endowments = pms.ENDOWMENTS[self.joueur.group_composition.index(self.joueur)]
        self.currentperiod.MRI_endowment_triangle = player_endowments[0]
        self.currentperiod.MRI_endowment_star = player_endowments[1]
        yield (self.remote.callRemote(
            "newperiod", period, (self.currentperiod.MRI_endowment_triangle,
                                  self.currentperiod.MRI_endowment_star)))
        logger.info(u"{} Ready for period {}".format(self.joueur, period))

    @defer.inlineCallbacks
    def display_decision(self):
        """
        Display the decision screen on the remote
        Get back noting because it is a market
        :return:
        """
        logger.debug(u"{} Decision".format(self.joueur))
        yield(self.remote.callRemote("display_decision"))
        self.joueur.info(u"Market closed")
        self.joueur.remove_waitmode()

    @defer.inlineCallbacks
    def remote_add_offer(self, offer):
        """
        check the offer
        if ok, create the offer in the database and send it to the group
        members
        :param offer: a dict
        :return:
        """
        logger.info(u"{} add_offer {}".format(self.joueur, offer))
        # create offer
        new_offer = OffersMRI(offer)
        new_offer_dict = new_offer.todict()
        logger.debug(u"Offer created: {}".format(new_offer.todict()))
        self.joueur.info(u"Offer {MRI_offer_contract}, "
                         u"{MRI_offer_type}, {MRI_offer_price}".format(
                            **new_offer_dict))
        self.currentperiod.MRI_offers.append(new_offer)
        # add the offer to the screen of group members
        for j in self.joueur.group_composition:
            yield (j.get_part(self.nom).remote.callRemote(
                "add_offer", new_offer_dict))

    @defer.inlineCallbacks
    def remote_remove_offer(self, offer):
        """
        Called by remote, when the player removes his offer
        :param offer:
        :return:
        """
        logger.debug(u"{} remove_offer {}".format(self.joueur, offer))
        for j in self.joueur.group_composition:
            yield (j.get_part(self.nom).remote.callRemote(
                "remove_offer", offer))

    def add_transaction(self, transaction):
        """
        Create the transaction and update the balances
        Called by remote_add_transaction
        :param transaction:
        :return:
        """
        new_transaction = TransactionsMRI(transaction)
        self.currentperiod.MRI_transactions.append(new_transaction)
        if transaction["MRI_trans_contract"] == pms.TRIANGLE:
            if transaction["MRI_trans_buyer"] == self.joueur.uid:
                self.currentperiod.MRI_triangle_number_of_purchase += 1
                self.currentperiod.MRI_triangle_sum_of_purchase += \
                    transaction["MRI_trans_price"]
            else:
                self.currentperiod.MRI_triangle_number_of_sell += 1
                self.currentperiod.MRI_triangle_sum_of_sell += \
                    transaction["MRI_trans_price"]
        else:  # star
            if transaction["MRI_trans_buyer"] == self.joueur.uid:
                self.currentperiod.MRI_star_number_of_purchase += 1
                self.currentperiod.MRI_star_sum_of_purchase += \
                    transaction["MRI_trans_price"]
            else:
                self.currentperiod.MRI_star_number_of_sell += 1
                self.currentperiod.MRI_star_sum_of_sell += \
                    transaction["MRI_trans_price"]
        self.joueur.info(u"Transaction {MRI_trans_contract}, "
                         u"{MRI_trans_price}".format(**transaction))

    @defer.inlineCallbacks
    def remote_add_transaction(self, existing_offer, new_offer):
        """
        Called by remote, when either:
        (i) the player accept an existing offer
        (ii) the player makes an offer at the same price than an existing offer
        (a purchase or a sell, it depends)
        :param existing_offer:
        :param new_offer:
        :return:
        """
        # remove the existing offer from the list on the screen
        yield(self.remote_remove_offer(existing_offer))

        # create a new offer (just for the player)
        new_offer_temp = OffersMRI(new_offer)
        self.currentperiod.MRI_offers.append(new_offer_temp)
        self.joueur.info(u"Offer {MRI_offer_contract}, "
                         u"{MRI_offer_type}, {MRI_offer_price}".format(**new_offer))

        # create the transaction
        transaction = dict()
        transaction["MRI_trans_time"] = new_offer["MRI_offer_time"]
        transaction["MRI_trans_contract"] = new_offer["MRI_offer_contract"]
        if new_offer["MRI_offer_type"] == pms.BUY:
            transaction["MRI_trans_buyer"] = new_offer["MRI_offer_sender"]
            transaction["MRI_trans_seller"] = existing_offer["MRI_offer_sender"]
        else:
            transaction["MRI_trans_buyer"] = existing_offer["MRI_offer_sender"]
            transaction["MRI_trans_seller"] = new_offer["MRI_offer_sender"]
        transaction["MRI_trans_price"] = new_offer["MRI_offer_price"]

        # send the transaction to everyone in the group
        for j in self.joueur.group_composition:
            # if this is a player implied in the transaction
            if j.uid == existing_offer["MRI_offer_sender"] or j == self.joueur:
                j.get_part(self.nom).add_transaction(transaction)
                yield (j.get_part(self.nom).update_balance())
            # display the transaction on the screen
            yield (j.get_part(self.nom).remote.callRemote(
                "add_transaction", transaction))

    @defer.inlineCallbacks
    def update_balance(self):
        balance_transactions = \
            (self.currentperiod.MRI_triangle_sum_of_sell +
             self.currentperiod.MRI_star_sum_of_sell) - \
            (self.currentperiod.MRI_triangle_sum_of_purchase +
            self.currentperiod.MRI_star_sum_of_purchase)

        balance_triangle = self.currentperiod.MRI_endowment_triangle + \
            balance_transactions

        balance_star = self.currentperiod.MRI_endowment_star + \
            balance_transactions

        balance_if_triangle = balance_triangle + \
                              (self.currentperiod.MRI_triangle_number_of_purchase *
                              pms.TRIANGLE_PAY) - \
                              (self.currentperiod.MRI_triangle_number_of_sell *
                              pms.TRIANGLE_PAY)

        balance_if_star = balance_star + \
                          (self.currentperiod.MRI_star_number_of_purchase *
                           pms.STAR_PAY) - \
                          (self.currentperiod.MRI_star_number_of_sell *
                          pms.STAR_PAY)
        yield (self.remote.callRemote("update_balance", balance_if_triangle,
                                      balance_if_star))

    def compute_periodpayoff(self):
        """
        Compute the payoff for the period
        :return:
        """
        logger.debug(u"{} Period Payoff".format(self.joueur))

        # endowment
        self.currentperiod.MRI_periodpayoff = \
            self.currentperiod.MRI_endowment_triangle if \
                self.currentperiod.MRI_event == pms.TRIANGLE else \
                self.currentperiod.MRI_endowment_star

        # transactions
        self.currentperiod.MRI_periodpayoff += \
            self.currentperiod.MRI_triangle_sum_of_sell + \
            self.currentperiod.MRI_star_sum_of_sell - \
            self.currentperiod.MRI_triangle_sum_of_purchase - \
            self.currentperiod.MRI_star_sum_of_purchase

        # balance of event
        if self.currentperiod.MRI_event == pms.TRIANGLE:
            self.currentperiod.MRI_event_balance = \
                (self.currentperiod.MRI_triangle_number_of_purchase -
                self.currentperiod.MRI_triangle_number_of_sell) * pms.TRIANGLE_PAY

        else:
            self.currentperiod.MRI_event_balance = \
                (self.currentperiod.MRI_star_number_of_purchase -
                self.currentperiod.MRI_star_number_of_sell) * pms.STAR_PAY

        self.currentperiod.MRI_periodpayoff += \
            self.currentperiod.MRI_event_balance

        # price activity indicator
        nb_offers = len(self.currentperiod.MRI_offers)
        nb_price_maker = len([o for o in self.currentperiod.MRI_offers if
                              o.MRI_offer_sender_type == pms.PRICE_MAKER])
        try:
            self.currentperiod.MRI_price_active = float("{:.4f}".format(
                nb_price_maker / nb_offers))
        except ZeroDivisionError:
            self.currentperiod.MRI_price_active = None
        logger.debug(u"{}: price activity {}".format(
            self.joueur, self.currentperiod.MRI_price_active))

        # cumulative payoff since the second period (the first one is a trial)
        if self.currentperiod.MRI_period < 3:
            self.currentperiod.MRI_cumulativepayoff = \
                self.currentperiod.MRI_periodpayoff
        else: 
            previousperiod = self.periods[self.currentperiod.MRI_period - 1]
            self.currentperiod.MRI_cumulativepayoff = \
                previousperiod.MRI_cumulativepayoff + \
                self.currentperiod.MRI_periodpayoff

        # we store the period in the self.periods dictionary
        self.periods[self.currentperiod.MRI_period] = self.currentperiod

        logger.debug(u"{} Period Payoff {}".format(
            self.joueur,
            self.currentperiod.MRI_periodpayoff))

    @defer.inlineCallbacks
    def display_summary(self):
        """
        Send a dictionary with the period content values to the remote.
        The remote creates the text and the history
        :param args:
        :return:
        """
        logger.debug(u"{} Summary".format(self.joueur))
        yield(self.remote.callRemote(
            "display_summary", self.currentperiod.todict(),
            self._transactions_group))
        self.joueur.info("Ok")
        self.joueur.remove_waitmode()

    @defer.inlineCallbacks
    def compute_partpayoff(self):
        """
        Compute the payoff for the part and set it on the remote.
        The remote stores it and creates the corresponding text for display
        (if asked)
        :return:
        """
        logger.debug(u"{} Part Payoff".format(self.joueur))
        # payoffs_selected_periods = dict([(r.MRI_period, r.MRI_periodpayoff) for r in
        #                             self.repetitions if r.MRI_period in
        #                             self._paid_periods])
        # logger.debug(u"{} payoffs {}".format(
        #     self.joueur, sorted(payoffs_selected_periods)))
        # self.MRI_gain_ecus = sum(payoffs_selected_periods.viewvalues())
        # self.MRI_gain_euros = float(self.MRI_gain_ecus) * float(pms.TAUX_CONVERSION)
        # yield (self.remote.callRemote(
        #     "set_payoffs", self.MRI_gain_euros, self.MRI_gain_ecus,
        #     payoffs_selected_periods))

        self.MRI_gain_ecus = self.currentperiod.MRI_cumulativepayoff
        self.MRI_gain_euros = float(self.MRI_gain_ecus) * float(pms.TAUX_CONVERSION)
        self.MRI_gain_euros -= pms.AMOUNT_TO_SUBTRACT
        yield (self.remote.callRemote(
            "set_payoffs", self.MRI_gain_euros))

        logger.info(u'{} Payoff ecus {} Payoff euros {:.2f}'.format(
            self.joueur, self.MRI_gain_ecus, self.MRI_gain_euros))

    def get_transactions(self):
        return [t.todict() for t in self.currentperiod.MRI_transactions]


class RepetitionsMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    partie_partie_id = Column(
        Integer,
        ForeignKey("partie_MarketRiskInsurance.partie_id"))
    MRI_offers = relationship('OffersMRI')
    MRI_transactions = relationship('TransactionsMRI')

    MRI_period = Column(Integer)
    MRI_treatment = Column(Integer)
    MRI_group = Column(Integer)
    MRI_random_value = Column(Integer)
    MRI_event = Column(Integer)
    MRI_endowment_triangle = Column(Float)
    MRI_endowment_star = Column(Float)
    MRI_triangle_number_of_purchase = Column(Integer)
    MRI_triangle_number_of_sell = Column(Integer)
    MRI_triangle_sum_of_purchase = Column(Float)
    MRI_triangle_sum_of_sell = Column(Float)
    MRI_star_number_of_purchase = Column(Integer)
    MRI_star_number_of_sell = Column(Integer)
    MRI_star_sum_of_purchase = Column(Float)
    MRI_star_sum_of_sell = Column(Float)
    MRI_event_balance = Column(Float)
    MRI_price_active = Column(Float)
    MRI_periodpayoff = Column(Float)
    MRI_cumulativepayoff = Column(Float)

    def __init__(self, period):
        self.MRI_period = period
        self.MRI_treatment = pms.TREATMENT
        self.MRI_triangle_number_of_purchase = 0
        self.MRI_triangle_number_of_sell = 0
        self.MRI_triangle_sum_of_purchase = 0
        self.MRI_triangle_sum_of_sell = 0
        self.MRI_star_number_of_purchase = 0
        self.MRI_star_number_of_sell = 0
        self.MRI_star_sum_of_purchase = 0
        self.MRI_star_sum_of_sell = 0
        self.MRI_periodpayoff = 0
        self.MRI_cumulativepayoff = 0

    def todict(self, joueur=None):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns
                if "MRI" in c.name}
        if joueur:
            temp["joueur"] = joueur
        return temp


class OffersMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions_offers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repetitions_id = Column(
        Integer, ForeignKey("partie_MarketRiskInsurance_repetitions.id"))

    counter = 0

    MRI_offer_time = Column(String)
    MRI_offer_sender = Column(String)
    MRI_offer_contract = Column(Integer)
    MRI_offer_type = Column(Integer)
    MRI_offer_price = Column(Float)
    MRI_offer_sender_type = Column(Integer)

    def __init__(self, offer):
        self.MRI_offer_time = offer["MRI_offer_time"]
        self.MRI_offer_contract = offer["MRI_offer_contract"]
        self.MRI_offer_sender = offer["MRI_offer_sender"]
        self.MRI_offer_type = offer["MRI_offer_type"]
        self.MRI_offer_price = offer["MRI_offer_price"]
        self.MRI_offer_sender_type = offer["MRI_offer_sender_type"]

    def todict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns
                if "MRI" in c.name}


class TransactionsMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions_transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repetitions_id = Column(
        Integer, ForeignKey("partie_MarketRiskInsurance_repetitions.id"))

    MRI_trans_time = Column(String)
    MRI_trans_contract = Column(Integer)
    MRI_trans_buyer = Column(String)
    MRI_trans_seller = Column(String)
    MRI_trans_price = Column(Float)

    def __init__(self, transaction):
        self.MRI_trans_time = transaction["MRI_trans_time"]
        self.MRI_trans_contract = transaction["MRI_trans_contract"]
        self.MRI_trans_buyer = transaction["MRI_trans_buyer"]
        self.MRI_trans_seller = transaction["MRI_trans_seller"]
        self.MRI_trans_price = transaction["MRI_trans_price"]

    def todict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns
                if "MRI" in c.name}

