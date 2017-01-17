# -*- coding: utf-8 -*-

import logging
from datetime import datetime
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
        self.currentperiod.MRI_random_value = random_value
        self.currentperiod.MRI_group = self.joueur.group

        self.le2mserv.gestionnaire_base.ajouter(self.currentperiod)
        self.repetitions.append(self.currentperiod)

        yield (self.remote.callRemote("newperiod", period))
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
        self.joueur.info(u"Ok")
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
        # todo: check whether the offer is ok
        # create proposition
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

    @defer.inlineCallbacks
    def remote_add_transaction(self, existing_offer, new_offer):
        # first remove the existing offer
        yield(self.remote_remove_offer(existing_offer))
        # create a new offer (just for the player)
        new_offer_temp = OffersMRI(new_offer)
        self.currentperiod.MRI_offers.append(new_offer_temp)
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
        new_transaction = TransactionsMRI(transaction)
        self.currentperiod.MRI_transactions.append(new_transaction)
        self.joueur.info(u"Transaction {MRI_trans_contract}, "
                         u"{MRI_trans_price}".format(**transaction))
        # send the transaction to everyone in the group
        for j in self.joueur.group_composition:
            yield (j.get_part(self.nom).remote.callRemote(
                "add_transaction", transaction))

    def _is_offer_ok(self, offer):
        """"
        We check that the offer is compatible with the player's budget
        in any event.
        1) check the player doesn't already have made a better offer
        2) check the player can buy the offer
        3) check the player's payoff at the end of the period taking into
        account the two possible events
        Return a tuple either of size 2 if the result is false
        (False and the explanation) or of size 1 if the result is true.
        """
        logger.debug(u"{}: test of prop: {}".format(self.joueur, offer))

        # proposition's informations
        contract = offer['MRI_offer_contract']  # triangle or star
        kind = offer["MRI_offer_type"]  # purchase or sell
        price = offer["MRI_offer_price"]

        # Checks that the proposition is not less interesting than another one
        # proposed by the player himself
        # prop_in_progress = [p for p in self.currentperiod.MRI_propositions if
        #                     p.MRI_prop_status == pms.IN_PROGRESS and
        #                     p.MRI_prop_contract == contract and
        #                     p.MRI_prop_type == kind]
        #
        # if kind == pms.BUY:
        #     best_props = [p for p in prop_in_progress if
        #                   p.MRI_prop_price > price]
        # else:
        #     best_props = [p for p in prop_in_progress if
        #                   p.MRI_prop_price < price]
        #
        # if best_props:
        #     return (False, u"Vous avez une meilleure proposition en cours.")



        transactions_balance = self._get_transactions_balance()

        solde_achats_ventes = self._get_solde_achats_ventes()
        solde_recu_verse_triangle = self._get_solde_recu_verse(pms.TRIANGLE)
        solde_recu_verse_star = self._get_solde_recu_verse(pms.STAR)

        # check the player has a budget that corresponds to at least CAPITAL_REQUIREMENT of the price, without taking into account the events
        # if type == pms.ACHAT:
        #     if self.periodeCourante.revenu + solde_achats_ventes < Decimal(
        #             str(prix)) * pms.CAPITAL_REQUIREMENT:
        #         return (
        #         False, u"Vous n'avez pas le budget nécessaire pour cet achat.")
        #
        # # check the player has a budget that corresponds to at leat CAPITAL_REQUIREMENT of the price, if the event if TRIANGLE
        # elif type == pms.VENTE:
        #     if contrat == pms.TRIANGLE:
        #         solde_recu_verse_triangle -= pms.TRIANGLE_VERSEMENT
        #         if solde_recu_verse_triangle < 0:
        #             if self.periodeCourante.revenu + solde_achats_ventes < Decimal(
        #                     str(abs(
        #                             solde_recu_verse_triangle))) * pms.CAPITAL_REQUIREMENT:
        #                 return (False,
        #                         u"Vous n'avez pas le budget nécessaire pour cette vente si l'évènement \"triangle\" se réalise.")
        #     elif contrat == pms.STAR:
        #         solde_recu_verse_star -= pms.STAR_VERSEMENT
        #         if solde_recu_verse_star < 0:
        #             if self.periodeCourante.revenu + solde_achats_ventes < Decimal(
        #                     str(abs(
        #                             solde_recu_verse_star))) * pms.CAPITAL_REQUIREMENT:
        #                 return (False,
        #                         u"Vous n'avez pas le budget nécessaire pour cette vente si l'évènement \"étoile\" se réalise.")
        #
        # # si tous les tests sont passés
        # logger.debug(u"Résultat du test: True")
        # return (True,)

    def _get_event_balance(self, event):
        # compute the receipts and the expenses for the event
        # if depends whether the player made transactions or not
        rec = sum(
            [t.MRI_trans_price for t in self.currentperiod.MRI_transactions
             if t.MRI_trans_contract == event and
             t.MRI_trans_seller == self.joueur.uid])
        dep = sum(
            [t.MRI_trans_price for t in self.currentperiod.MRI_transactions
             if t.MRI_trans_contract == event and
             t.MRI_trans_buyer == self.joueur.uid])
        return rec - dep

    def _get_transaction_balance(self):
        """
        Return the sum of the player's sells minus the sum of the player's
        purchases.
        """
        purchases = sum([t.MRI_trans_price for t in
                         self.currentperiod.MRI_transactions if
                         t.MRI_trans_buyer == self.joueur.uid])
        sells = sum([t.MRI_trans_price for t in
                         self.currentperiod.MRI_transactions if
                         t.MRI_trans_seller == self.joueur.uid])
        return sells - purchases

    def compute_periodpayoff(self):
        """
        Compute the payoff for the period
        :return:
        """
        logger.debug(u"{} Period Payoff".format(self.joueur))
        self.currentperiod.MRI_periodpayoff = 0

        # cumulative payoff since the first period
        if self.currentperiod.MRI_period < 2:
            self.currentperiod.MRI_cumulativepayoff = \
                self.currentperiod.MRI_periodpayoff
        else: 
            previousperiod = self.periods[self.currentperiod.MRI_period - 1]
            self.currentperiod.MRI_cumulativepayoff = \
                previousperiod.MRI_cumulativepayoff + \
                self.currentperiod.MRI_periodpayoff

        # we store the period in the self.periodes dictionnary
        self.periods[self.currentperiod.MRI_period] = self.currentperiod

        logger.debug(u"{} Period Payoff {}".format(
            self.joueur,
            self.currentperiod.MRI_periodpayoff))

    @defer.inlineCallbacks
    def display_summary(self, *args):
        """
        Send a dictionary with the period content values to the remote.
        The remote creates the text and the history
        :param args:
        :return:
        """
        logger.debug(u"{} Summary".format(self.joueur))
        yield(self.remote.callRemote(
            "display_summary", self.currentperiod.todict()))
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

        self.MRI_gain_ecus = self.currentperiod.MRI_cumulativepayoff
        self.MRI_gain_euros = float(self.MRI_gain_ecus) * float(pms.TAUX_CONVERSION)
        yield (self.remote.callRemote(
            "set_payoffs", self.MRI_gain_euros, self.MRI_gain_ecus))

        logger.info(u'{} Payoff ecus {} Payoff euros {:.2f}'.format(
            self.joueur, self.MRI_gain_ecus, self.MRI_gain_euros))


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
    MRI_dotation = Column(Integer)
    MRI_triangle_number_of_purchase = Column(Integer)
    MRI_triangle_number_of_sell = Column(Integer)
    MRI_triangle_sum_of_purchase = Column(Float)
    MRI_triangle_sum__of_sell = Column(Float)
    MRI_star_number_of_purchase = Column(Integer)
    MRI_star_number_of_sell = Column(Integer)
    MRI_star_sum_of_purchase = Column(Float)
    MRI_star_sum_of_sell = Column(Float)
    MRI_periodpayoff = Column(Float)
    MRI_cumulativepayoff = Column(Float)

    def __init__(self, period):
        self.MRI_treatment = pms.TREATMENT
        self.MRI_period = period
        self.MRI_triangle_number_of_purchase = 0

        self.MRI_periodpayoff = 0
        self.MRI_cumulativepayoff = 0

    def todict(self, joueur=None):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if joueur:
            temp["joueur"] = joueur
        return temp


class OffersMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions_propositions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repetitions_id = Column(
        Integer, ForeignKey("partie_MarketRiskInsurance_repetitions.id"))

    counter = 0

    MRI_offer_time = Column(String)
    MRI_offer_sender = Column(String)
    MRI_offer_contract = Column(Integer)
    MRI_offer_type = Column(Integer)
    MRI_offer_price = Column(Float)

    def __init__(self, offer):
        self.MRI_offer_time = offer["MRI_offer_time"]
        self.MRI_offer_contract = offer["MRI_offer_contract"]
        self.MRI_offer_sender = offer["MRI_offer_sender"]
        self.MRI_offer_type = offer["MRI_offer_type"]
        self.MRI_offer_price = offer["MRI_offer_price"]

    def todict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


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
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}