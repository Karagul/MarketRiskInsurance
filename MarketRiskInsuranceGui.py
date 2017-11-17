# -*- coding: utf-8 -*-
"""
This module contains the GUI
"""

import sys
import logging
from PyQt4 import QtGui, QtCore, QtWebKit
from twisted.internet import defer
from random import random, randint, choice
from util.utili18n import le2mtrans
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceTexts import trans_MRI
import MarketRiskInsuranceTexts as texts_MRI
from client.cltgui.cltguidialogs import GuiHistorique
from client.cltgui.cltguiwidgets import WPeriod, WExplication, WCompterebours, \
    WTableview
from client.cltgui.cltguitablemodels import TableModelHistorique
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


SIZE_HISTO = (1300, 500)
logger = logging.getLogger("le2m")


class MyStandardItem(QtGui.QStandardItem):
    """
    Surcharge du standard item pour la fonction sort de la liste qui
    accueillera ces items
    """
    def __init__(self, value):
        QtGui.QStandardItem.__init__(self)
        self.__value = value
        self.setText(str(value))

    def __lt__(self, other):
        return other < self.__value

    def value(self):
        return self.__value


class MyDoubleSpinBox(QtGui.QDoubleSpinBox):
    def __init__(self):
        QtGui.QDoubleSpinBox.__init__(self)
        self.setDecimals(pms.DECIMALS)
        self.setMinimum(0)
        self.setMaximum(pms.OFFER_MAX)
        self.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self.setMaximumWidth(50)


class InformationZone(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)

        self.layout.addSpacerItem(QtGui.QSpacerItem(
            20, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))

        self.form = QtGui.QFormLayout()
        self.layout.addLayout(self.form)
        self.label_balance_if_triangle = QtGui.QLabel(u"...")
        self.label_balance_if_triangle.setAlignment(QtCore.Qt.AlignRight)
        self.form.addRow(QtGui.QLabel(trans_MRI(u"Income if triangle:")),
                         self.label_balance_if_triangle)
        self.label_balance_if_star = QtGui.QLabel(u"...")
        self.label_balance_if_star.setAlignment(QtCore.Qt.AlignRight)
        self.form.addRow(QtGui.QLabel(trans_MRI(u"Income if star:")),
                         self.label_balance_if_star)

        self.layout.addSpacerItem(QtGui.QSpacerItem(
            20, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))


class OfferZone(QtGui.QWidget):

    font_normale = QtGui.QFont()
    font_bold = QtGui.QFont()
    font_bold.setWeight(QtGui.QFont.Bold)
    font_bold.setPointSize(font_normale.pointSize() + 1)
    offer_selected = QtCore.pyqtSignal(dict)

    def __init__(self, purchase_or_sell, zone_size=(400, 300)):
        QtGui.QWidget.__init__(self)

        self.current_offer = None
        self._purchase_or_sell = purchase_or_sell
        self._offers = {}

        self.layout_main = QtGui.QVBoxLayout()
        self.setLayout(self.layout_main)

        self.label = QtGui.QLabel()
        if self._purchase_or_sell == pms.BUY:
            self.label.setText(trans_MRI(u"Purchase offers"))
        else:
            self.label.setText(trans_MRI(u"Sell offers"))
        self.layout_main.addWidget(self.label)

        self.list_view = QtGui.QListView()
        self.model = QtGui.QStandardItemModel()
        self.list_view.setModel(self.model)
        self.layout_main.addWidget(self.list_view)

        self.layout_offer = QtGui.QHBoxLayout()
        self.layout_main.addLayout(self.layout_offer)
        if self._purchase_or_sell == pms.BUY:
            self.layout_offer.addWidget(
                QtGui.QLabel(trans_MRI(u"Make a purchase offer")))
        else:
            self.layout_offer.addWidget(
                QtGui.QLabel(trans_MRI(u"Make a sell offer")))
        self.spin_offer = MyDoubleSpinBox()
        self.layout_offer.addWidget(self.spin_offer)
        self.pushbutton_send = QtGui.QPushButton(trans_MRI(u"Send"))
        self.pushbutton_send.setFixedWidth(100)
        self.pushbutton_send.setToolTip(
            trans_MRI(u"Make an offer or replace the current one"))
        self.layout_offer.addWidget(self.pushbutton_send)
        self.layout_offer.addSpacerItem(
            QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Minimum))

        self.layout_accept_remove = QtGui.QHBoxLayout()
        self.layout_main.addLayout(self.layout_accept_remove)
        self.pushbutton_accept = QtGui.QPushButton(
            trans_MRI(u"Accept the offer"))
        self.pushbutton_accept.setFixedWidth(160)
        self.pushbutton_accept.setToolTip(
            trans_MRI(u"Select an offer and click on this button to "
                      u"accept it"))
        self.layout_accept_remove.addWidget(self.pushbutton_accept)

        self.pushbutton_remove = QtGui.QPushButton(trans_MRI(u"Remove my bid"))
        self.pushbutton_remove.setFixedWidth(160)
        self.pushbutton_remove.setToolTip(
            trans_MRI(u"If you have an offer click here to remove it"))
        self.layout_accept_remove.addWidget(
            self.pushbutton_remove)
        self.layout_accept_remove.addSpacerItem(
            QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Minimum))

        # connections
        self.list_view.clicked.connect(self._set_current_offer)

        self.setFixedSize(*zone_size)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def _set_current_offer(self, index):
        current_item = self.model.item(index.row(), 0)
        for k, v in self._offers.viewitems():
            if v[0] == current_item:
                self.current_offer = v[1]
                break
        self.offer_selected.emit(self.current_offer.copy())

    def add_offer(self, sender, offer, color):
        # remove the current offer
        self.remove_offer(sender)
        # add the new offer
        item = MyStandardItem(offer["MRI_offer_price"])
        item.setForeground(QtGui.QColor(color))
        self.model.appendRow(item)
        self._sort()
        self._offers[sender] = (item, offer)

    def remove_offer(self, sender):
        """
        Remove the offer from the list
        :param sender:
        :return:
        """
        offer_item = self._offers.pop(sender, None)
        if offer_item is not None:
            for row in range(self.model.rowCount()):
                if self.model.item(row, 0) == offer_item[0]:
                    self.model.removeRow(row)
                    break
            self._sort()

    def _sort(self):
        if self._purchase_or_sell == pms.BUY:
            self.model.sort(0, QtCore.Qt.DescendingOrder)
        else:
            self.model.sort(0, QtCore.Qt.AscendingOrder)

        for i in range(self.model.rowCount()):
            self.model.item(i).setFont(
                self.font_bold if i == 0 else self.font_normale)
        self.current_offer = None

    def clear(self):
        """
        we clear both the model and the dict that stores the offers
        :return:
        """
        self.model.clear()
        self._offers.clear()

    def exists_offer(self, price, sender):
        """
        We check whether there exists an offer with that price.
        If it does return the offer. If it doesn't return False
        :param sender:
        :param price:
        :return:
        """
        existing_offers = list()
        for k, v in self._offers.viewitems():
            if v[1]["MRI_offer_price"] == price and \
                            v[1]["MRI_offer_sender"] != sender:
                existing_offer = v[1]
                logger.debug(u"exists_offer: {}".format(existing_offer))
                existing_offers.append(existing_offer)
        if existing_offers:
            existing_offers.sort(key=lambda x: x["MRI_offer_time"])
            return existing_offers[0]
        return False

    def get_sender_offer(self, sender):
        try:
            return self._offers[sender][1]
        except KeyError:
            return None

    def select_an_item(self):
        if self._offers:
            random_item = choice([v[0] for v in self._offers.viewvalues()])
            index = self.model.indexFromItem(random_item)
            self.list_view.setCurrentIndex(index)
            self._set_current_offer(index)


class TransactionZone(QtGui.QWidget):
    def __init__(self, zone_size=(400, 200)):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QtGui.QLabel(trans_MRI(u"Transactions"))
        self.layout.addWidget(self.label)
        self.list = QtGui.QListView()
        self.layout.addWidget(self.list)
        self.model = QtGui.QStandardItemModel()
        self.list.setModel(self.model)

        self.setFixedSize(*zone_size)

    def add_transaction(self, price, buyer_seller, color):
        if buyer_seller == pms.BUYER:
            item = MyStandardItem(str(price) + u" (" +
                                  trans_MRI(u"purchase") + u")")
        elif buyer_seller == pms.SELLER:
            item = MyStandardItem(str(price) + u" (" +
                                  trans_MRI(u"sell") + u")")
        else:
            item = MyStandardItem(price)
        item.setForeground(QtGui.QColor(color))
        self.model.insertRow(0, item)

    def clear(self):
        self.model.clear()


class GraphicalZone(QtGui.QWidget):
    def __init__(self, transactions, max_price, triangle_or_star,
                 zone_size=(500, 200)):
        QtGui.QWidget.__init__(self)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        the_marker = "^" if triangle_or_star == pms.TRIANGLE else "*"

        figure = plt.Figure(figsize=(7, 4), facecolor="white")
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)

        try:
            graph = figure.add_subplot(111)
            graph.plot(transactions.MRI_time_diff,
                       transactions.MRI_trans_price, color="k",
                       marker=the_marker)
            graph.set_xlim(0, pms.MARKET_TIME.minute * 60 + pms.MARKET_TIME.second)
            graph.set_xlabel("Temps (secondes)")
            graph.set_xticks(
                range(0,
                      pms.MARKET_TIME.minute * 60 + pms.MARKET_TIME.second + 1, 10))
            graph.set_xticklabels(
                range(0, pms.MARKET_TIME.minute * 60 + pms.MARKET_TIME.second + 1, 30))

            graph.set_ylabel(trans_MRI(u"Price"))
            graph.set_xlim(0, pms.MARKET_TIME.minute * 60 + pms.MARKET_TIME.second + 5)
            graph.set_ylim(-0.5, max_price + 0.5)
            graph.grid()
        except ValueError:  # no transactions
            pass
        figure.tight_layout()
        self.setFixedSize(*zone_size)


class GuiDecision(QtGui.QDialog):
    def __init__(self, defered, automatique, parent, period, historique, remote):
        super(GuiDecision, self).__init__(parent)

        # variables
        self._defered = defered
        self._automatique = automatique
        self._remote = remote

        layout = QtGui.QVBoxLayout(self)

        self._historique = GuiHistorique(self, historique, size=SIZE_HISTO)
        wperiod = WPeriod(
            period=period, ecran_historique=self._historique)
        layout.addWidget(wperiod)

        wexplanation = WExplication(
            text=texts_MRI.get_text_explanation(
                self._remote.balance_if_triangle, self._remote.balance_if_star),
            size=(SIZE_HISTO[0], 70), parent=self)
        layout.addWidget(wexplanation)

        # Compte à rebours =====================================================
        self._compte_rebours = WCompterebours(
            parent=self, temps=pms.MARKET_TIME, actionfin=self._accept)
        self._compte_rebours.setStyleSheet("color: blue;")
        layout.addWidget(self._compte_rebours)

        # zone information actualisée ==========================================
        self._information = InformationZone()
        layout.addWidget(self._information)

        # market ===============================================================
        market_layout = QtGui.QGridLayout()
        layout.addLayout(market_layout)

        # triangle
        triangle_label = QtGui.QLabel(trans_MRI(u"Triangle"))
        triangle_label.setStyleSheet("color: red;")
        market_layout.addWidget(triangle_label, 0, 0, 1, 2)
        self._triangle_purchase_zone = OfferZone(pms.BUY, zone_size=(350, 250))
        market_layout.addWidget(self._triangle_purchase_zone, 1, 0)
        self._triangle_sell_zone = OfferZone(pms.SELL, zone_size=(350, 250))
        market_layout.addWidget(self._triangle_sell_zone, 1, 1)
        self._triangle_transactions = TransactionZone(zone_size=(350, 250))
        market_layout.addWidget(self._triangle_transactions, 2, 0, 1, 2)

        # star
        star_label = QtGui.QLabel(trans_MRI(u"Star"))
        star_label.setStyleSheet("color: red;")
        market_layout.addWidget(star_label, 0, 3, 1, 2)
        self._star_purchase_zone = OfferZone(pms.BUY, zone_size=(350, 250))
        market_layout.addWidget(self._star_purchase_zone, 1, 3)
        self._star_sell_zone = OfferZone(pms.SELL, zone_size=(350, 250))
        market_layout.addWidget(self._star_sell_zone, 1, 4)
        self._star_transactions = TransactionZone(zone_size=(350, 250))
        market_layout.addWidget(self._star_transactions, 2, 3, 1, 2)

        separator = QtGui.QFrame()
        separator.setFrameShape(QtGui.QFrame.VLine)
        market_layout.addWidget(separator, 0, 2, market_layout.rowCount(), 1)

        # finalisation =========================================================
        layout.addSpacing(50)
        self._make_connections()
        self.setWindowTitle(trans_MRI(u"Market"))
        # self.adjustSize()
        # self.setFixedSize(self.size())

        if self._automatique:
            self._timer_automatique = QtCore.QTimer()
            self._timer_automatique.timeout.connect(self._play_auto)
            self._timer_automatique.start(randint(2000, 7000))
                
    def _make_connections(self):
        """
        Connect the pushbutton of the different offer zones to the method
        of GUIDecision (_add_offer)
        :return:
        """
        # send offer ===========================================================
        # TRIANGLE
        self._triangle_purchase_zone.pushbutton_send.clicked.connect(
            lambda _: self._add_offer(
                pms.TRIANGLE, pms.BUY,
                self._triangle_purchase_zone.spin_offer.value(),
        self._triangle_purchase_zone.spin_offer))
        self._triangle_purchase_zone.spin_offer.valueChanged.connect(
            lambda _: self._triangle_purchase_zone.pushbutton_send.setToolTip(
                self._remote.get_hypothetical_balance(
                    {"MRI_offer_contract": pms.TRIANGLE,
                     "MRI_offer_type": pms.BUY,
                     "MRI_offer_price": self._triangle_purchase_zone.spin_offer.value()})
            ))
        self._triangle_sell_zone.pushbutton_send.clicked.connect(
            lambda _: self._add_offer(
                pms.TRIANGLE, pms.SELL,
                self._triangle_sell_zone.spin_offer.value(),
                self._triangle_sell_zone.spin_offer))
        self._triangle_sell_zone.spin_offer.valueChanged.connect(
            lambda _: self._triangle_sell_zone.pushbutton_send.setToolTip(
                self._remote.get_hypothetical_balance(
                    {"MRI_offer_contract": pms.TRIANGLE,
                     "MRI_offer_type": pms.SELL,
                     "MRI_offer_price": self._triangle_sell_zone.spin_offer.value()}
                )))
        # STAR
        self._star_purchase_zone.pushbutton_send.clicked.connect(
            lambda _: self._add_offer(
                pms.STAR, pms.BUY,
                self._star_purchase_zone.spin_offer.value(),
                self._star_purchase_zone.spin_offer))
        self._star_purchase_zone.spin_offer.valueChanged.connect(
            lambda _: self._star_purchase_zone.pushbutton_send.setToolTip(
                self._remote.get_hypothetical_balance(
                    {"MRI_offer_contract": pms.STAR,
                     "MRI_offer_type": pms.BUY,
                     "MRI_offer_price": self._star_purchase_zone.spin_offer.value()}
                )))
        self._star_sell_zone.pushbutton_send.clicked.connect(
            lambda _: self._add_offer(
                pms.STAR, pms.SELL, self._star_sell_zone.spin_offer.value(),
                self._star_sell_zone.spin_offer))
        self._star_sell_zone.spin_offer.valueChanged.connect(
            lambda _: self._star_sell_zone.pushbutton_send.setToolTip(
                self._remote.get_hypothetical_balance(
                    {"MRI_offer_contract": pms.STAR,
                     "MRI_offer_type": pms.SELL,
                     "MRI_offer_price": self._star_sell_zone.spin_offer.value()}
                )))
        
        # remove offer =========================================================
        self._triangle_purchase_zone.pushbutton_remove.clicked.connect(
            lambda _: self._remove_offer(pms.TRIANGLE, pms.BUY))
        self._triangle_sell_zone.pushbutton_remove.clicked.connect(
            lambda _: self._remove_offer(pms.TRIANGLE, pms.SELL))
        self._star_purchase_zone.pushbutton_remove.clicked.connect(
            lambda _: self._remove_offer(pms.STAR, pms.BUY))
        self._star_sell_zone.pushbutton_remove.clicked.connect(
            lambda _: self._remove_offer(pms.STAR, pms.SELL))

        # offer selected =======================================================
        self._triangle_purchase_zone.offer_selected.connect(
            lambda offer: self._triangle_purchase_zone.pushbutton_accept.setToolTip(
                self._remote.get_hypothetical_balance(offer, accept=True)))
        self._triangle_sell_zone.offer_selected.connect(
            lambda offer: self._triangle_sell_zone.pushbutton_accept.setToolTip(
                self._remote.get_hypothetical_balance(offer, accept=True)))
        self._star_purchase_zone.offer_selected.connect(
            lambda offer: self._star_purchase_zone.pushbutton_accept.setToolTip(
                self._remote.get_hypothetical_balance(offer, accept=True)))
        self._star_sell_zone.offer_selected.connect(
            lambda offer: self._star_sell_zone.pushbutton_accept.setToolTip(
                self._remote.get_hypothetical_balance(offer, accept=True)))

        # accept selected offer ================================================
        self._triangle_purchase_zone.pushbutton_accept.clicked.connect(
            lambda _: self._accept_selected_offer(
                pms.TRIANGLE, self._triangle_purchase_zone.current_offer))
        self._triangle_sell_zone.pushbutton_accept.clicked.connect(
            lambda _: self._accept_selected_offer(
                pms.TRIANGLE, self._triangle_sell_zone.current_offer))
        self._star_purchase_zone.pushbutton_accept.clicked.connect(
            lambda _: self._accept_selected_offer(
                pms.STAR, self._star_purchase_zone.current_offer))
        self._star_sell_zone.pushbutton_accept.clicked.connect(
            lambda _: self._accept_selected_offer(
                pms.STAR, self._star_sell_zone.current_offer))

    def reject(self):
        pass
    
    def _accept(self):
        try:
            self._timer_automatique.stop()
        except AttributeError:
            pass
        logger.info(u"Ok")
        self.accept()
        self._defered.callback(True)

    @defer.inlineCallbacks
    def _add_offer(self, triangle_or_star, buy_or_sell, price,
                   spin_offer_sender=None):
        """
        send the offer to the server
        called by pushbutton_send of the offer zone
        """
        logger.info("add_offer: contract {} - type {} - price {}".format(
            triangle_or_star, buy_or_sell, price))
        # we test whether there exists an offer with the same price
        if triangle_or_star == pms.TRIANGLE:
            if buy_or_sell == pms.BUY:
                existing_offer = self._triangle_sell_zone.exists_offer(
                    price, self._remote.le2mclt.uid)
            else:
                existing_offer = self._triangle_purchase_zone.exists_offer(
                    price, self._remote.le2mclt.uid)
        else:
            if buy_or_sell == pms.BUY:
                existing_offer = self._star_sell_zone.exists_offer(
                    price, self._remote.le2mclt.uid)
            else:
                existing_offer = self._star_purchase_zone.exists_offer(
                    price, self._remote.le2mclt.uid)

        # if the existing is player's own offer we cancel this existing offer
        if existing_offer:
            if existing_offer["MRI_offer_sender"] == self._remote.le2mclt.uid:
                existing_offer = False

        if existing_offer:
            existing_offer["MRI_offer_contract"] = triangle_or_star
            existing_offer["MRI_offer_type"] = \
                pms.SELL if buy_or_sell == pms.BUY else pms.BUY
            yield (self._accept_selected_offer(triangle_or_star,
                                               existing_offer))
        else:
            offer = {"MRI_offer_contract": triangle_or_star,
                     "MRI_offer_type": buy_or_sell,
                     "MRI_offer_price": price,
                     "MRI_offer_sender_type": pms.PRICE_MAKER}
            if self._remote.is_offer_ok(offer):
                yield (self._remote.add_offer(offer))
            else:
                if not self._automatique:
                    self._display_offer_failure(
                        trans_MRI(u"You can't make this offer"))
        try:
            spin_offer_sender.setValue(0)
        except AttributeError:
            pass

    def add_offer(self, offer):
        """
        add the offer to the list
        called by remote
        :param offer:
        :return:
        """
        sender = offer["MRI_offer_sender"]
        color = "blue" if sender == self._remote.le2mclt.uid else "black"
        if offer["MRI_offer_contract"] == pms.TRIANGLE:
            if offer["MRI_offer_type"] == pms.BUY:
                self._triangle_purchase_zone.add_offer(sender, offer, color)
            else:  # purchase
                self._triangle_sell_zone.add_offer(sender, offer, color)
        else:  # star
            if offer["MRI_offer_type"] == pms.BUY:
                self._star_purchase_zone.add_offer(sender, offer, color)
            else:  # purchase
                self._star_sell_zone.add_offer(sender, offer, color)
        
    @defer.inlineCallbacks
    def _remove_offer(self, triangle_or_star, buy_or_sell):
        """
        Called by pushbutton_remove_offer from the offer zone
        :param triangle_or_star: 
        :param buy_or_sell: 
        :return:
        """
        offer = {"MRI_offer_contract": triangle_or_star,
                 "MRI_offer_type": buy_or_sell}
        yield (self._remote.remove_offer(offer))

    def remove_offer(self, offer):
        """
        remove the offer from the list
        called by remote
        :param offer:
        :return:
        """
        sender = offer["MRI_offer_sender"]
        if offer["MRI_offer_contract"] == pms.TRIANGLE:
            if offer["MRI_offer_type"] == pms.BUY:
                self._triangle_purchase_zone.remove_offer(sender)
            else:  # purchase
                self._triangle_sell_zone.remove_offer(sender)
        else:  # star
            if offer["MRI_offer_type"] == pms.BUY:
                self._star_purchase_zone.remove_offer(sender)
            else:  # purchase
                self._star_sell_zone.remove_offer(sender)

    @defer.inlineCallbacks
    def _accept_selected_offer(self, triangle_or_star, existing_offer):
        """
        Called by pushbutton accept_selected_offer from the offer zone
        Complete the offer and if all is fine add a new transaction
        :param triangle_or_star:
        :param existing_offer:
        :return:
        """
        if existing_offer is None:
            return
        try:
            if existing_offer["MRI_offer_sender"] != self._remote.le2mclt.uid:
                existing_offer["MRI_offer_contract"] = triangle_or_star
                new_offer = dict()
                new_offer["MRI_offer_contract"] = \
                    existing_offer["MRI_offer_contract"]
                new_offer["MRI_offer_price"] = existing_offer["MRI_offer_price"]
                new_offer["MRI_offer_sender_type"] = pms.PRICE_TAKER
                if existing_offer["MRI_offer_type"] == pms.BUY:
                    new_offer["MRI_offer_type"] = pms.SELL
                else:
                    new_offer["MRI_offer_type"] = pms.BUY
                if self._remote.is_offer_ok(new_offer):
                    yield (self._remote.add_transaction(existing_offer,
                                                        new_offer))
                else:
                    if not self._automatique:
                        self._display_offer_failure(
                            trans_MRI(u"You can't accept this offer"))
        except (TypeError, KeyError):  # if no item selected
            pass

    def add_transaction(self, transaction):
        """
        Add the transaction in the transaction zone
        :param transaction:
        :return:
        """
        price = transaction["MRI_trans_price"]
        buyer = transaction["MRI_trans_buyer"]
        seller = transaction["MRI_trans_seller"]
        implied, buyer_or_seller = False, None
        if buyer == self._remote.le2mclt.uid or \
                    seller == self._remote.le2mclt.uid:
            implied = True
            buyer_or_seller = pms.BUYER if buyer == self._remote.le2mclt.uid \
                else pms.SELLER
        color = "blue" if implied else "black"
        if transaction["MRI_trans_contract"] == pms.TRIANGLE:
            self._triangle_transactions.add_transaction(price, buyer_or_seller,
                                                        color)
        else:
            self._star_transactions.add_transaction(price, buyer_or_seller,
                                                    color)

    @defer.inlineCallbacks
    def update_balance(self, balance_if_triangle, balance_if_star):
        """
        Display the new balances and test each player's offers in the list.
        If an offer is no more possible then removes it
        :param balance:
        :param balance_if_triangle:
        :param balance_if_star:
        :return:
        """
        self._information.label_balance_if_triangle.setText(
            str(balance_if_triangle))
        self._information.label_balance_if_star.setText(str(balance_if_star))

        triangle_purchase_sender_offer = \
            self._triangle_purchase_zone.get_sender_offer(self._remote.le2mclt.uid)
        if triangle_purchase_sender_offer:
            if not self._remote.is_offer_ok(triangle_purchase_sender_offer):
                yield (self._remove_offer(pms.TRIANGLE, pms.BUY))
        triangle_sell_sender_offer = \
            self._triangle_sell_zone.get_sender_offer(self._remote.le2mclt.uid)
        if triangle_sell_sender_offer:
            if not self._remote.is_offer_ok(triangle_sell_sender_offer):
                yield (self._remove_offer(pms.TRIANGLE, pms.SELL))
        star_purchase_sender_offer = \
            self._star_purchase_zone.get_sender_offer(self._remote.le2mclt.uid)
        if star_purchase_sender_offer:
            if not self._remote.is_offer_ok(star_purchase_sender_offer):
                yield (self._remove_offer(pms.STAR, pms.BUY))
        star_sell_sender_offer = \
            self._star_sell_zone.get_sender_offer(self._remote.le2mclt.uid)
        if star_sell_sender_offer:
            if not self._remote.is_offer_ok(star_sell_sender_offer):
                yield (self._remove_offer(pms.STAR, pms.SELL))

    def _display_offer_failure(self, message):
        QtGui.QMessageBox.warning(self, trans_MRI(u"Be careful"), message)
        return

    def _play_auto(self):
        """
        called by the timer when the program play automatically
        :return:
        """
        # make an offer
        def make_offer(the_list):
            random_offer = float("{:.2f}".format(random() + randint(0, 1)))
            the_list.spin_offer.setValue(random_offer)
            the_list.pushbutton_send.click()

        def accept_offer(the_list):
            the_list.select_an_item()
            the_list.pushbutton_accept.click()

        triangle_or_star = choice([pms.TRIANGLE, pms.STAR])
        buy_or_sell = choice([pms.BUY, pms.SELL])
        selected_function = choice([make_offer, accept_offer])

        if triangle_or_star == pms.TRIANGLE:
            if buy_or_sell == pms.BUY:
                selected_function(self._triangle_purchase_zone)
            else:
                selected_function(self._triangle_sell_zone)
        else:
            if buy_or_sell == pms.BUY:
                selected_function(self._star_purchase_zone)
            else:
                selected_function(self._star_sell_zone)


class DConfigure(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        form = QtGui.QFormLayout()
        layout.addLayout(form)

        # treatment
        self._combo_treatment = QtGui.QComboBox()
        self._combo_treatment.addItems(
            [pms.TREATMENTS_NAMES[k] for k in
             sorted(pms.TREATMENTS_NAMES.viewkeys())])
        self._combo_treatment.setCurrentIndex(pms.TREATMENT)
        form.addRow(QtGui.QLabel(trans_MRI(u"Treatment")), self._combo_treatment)

        # periods
        self._spin_periods = QtGui.QSpinBox()
        self._spin_periods.setMinimum(0)
        self._spin_periods.setMaximum(100)
        self._spin_periods.setSingleStep(1)
        self._spin_periods.setValue(pms.NOMBRE_PERIODES)
        self._spin_periods.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_periods.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(trans_MRI(u"Number of periods")), self._spin_periods)

        # # trial
        # self._checkbox_essai = QtGui.QCheckBox()
        # self._checkbox_essai.setChecked(pms.PERIODE_ESSAI)
        # form.addRow(QtGui.QLabel(trans_MRI(u"Trail period")), self._checkbox_essai)

        # paid periods
        # self._spin_paid_periods = QtGui.QSpinBox()
        # self._spin_paid_periods.setMinimum(1)
        # self._spin_paid_periods.setMaximum(50)
        # self._spin_paid_periods.setSingleStep(1)
        # self._spin_paid_periods.setValue(pms.NUMBER_OF_PAID_PERIODS)
        # self._spin_paid_periods.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        # self._spin_paid_periods.setMaximumWidth(50)
        # form.addRow(QtGui.QLabel(trans_MRI(u"Number of paid periods")),
        #             self._spin_paid_periods)

        # Amount to substract from the cumulative payoff
        self._spin_amount_to_substract = QtGui.QSpinBox()
        self._spin_amount_to_substract.setMinimumWidth(0)
        self._spin_amount_to_substract.setMaximumWidth(200)
        self._spin_amount_to_substract.setSingleStep(1)
        self._spin_amount_to_substract.setValue(pms.AMOUNT_TO_SUBTRACT)
        self._spin_amount_to_substract.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_amount_to_substract.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(
            trans_MRI(u"Amount to subtract to the cumulative payoff")),
            self._spin_amount_to_substract)

        # group size
        self._spin_groups = QtGui.QSpinBox()
        self._spin_groups.setMinimum(2)
        self._spin_groups.setMaximum(100)
        self._spin_groups.setSingleStep(1)
        self._spin_groups.setValue(pms.TAILLE_GROUPES)
        self._spin_groups.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_groups.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(trans_MRI(u"Group size")), self._spin_groups)

        # market duration
        self._timeEdit_market = QtGui.QTimeEdit()
        self._timeEdit_market.setDisplayFormat("hh:mm:ss")
        self._timeEdit_market.setTime(QtCore.QTime(pms.MARKET_TIME.hour,
                                                   pms.MARKET_TIME.minute,
                                                   pms.MARKET_TIME.second))
        self._timeEdit_market.setMaximumWidth(100)
        form.addRow(QtGui.QLabel(trans_MRI(u"Market duration")),
                    self._timeEdit_market)

        # summary duration
        self._timeEdit_summary = QtGui.QTimeEdit()
        self._timeEdit_summary.setDisplayFormat("hh:mm:ss")
        self._timeEdit_summary.setTime(QtCore.QTime(pms.SUMMARY_TIME.hour,
                                                    pms.SUMMARY_TIME.minute,
                                                    pms.SUMMARY_TIME.second))
        self._timeEdit_summary.setMaximumWidth(100)
        form.addRow(QtGui.QLabel(trans_MRI(u"Summary duration")),
                    self._timeEdit_summary)

        button = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        button.accepted.connect(self._accept)
        button.rejected.connect(self.reject)
        layout.addWidget(button)

        self.setWindowTitle(trans_MRI(u"Configure"))
        self.adjustSize()
        self.setFixedSize(self.size())

    def _accept(self):
        pms.TREATMENT = self._combo_treatment.currentIndex()
        pms.AMOUNT_TO_SUBTRACT = self._spin_amount_to_substract.value()
        pms.MARKET_TIME = self._timeEdit_market.time().toPyTime()
        pms.SUMMARY_TIME = self._timeEdit_summary.time().toPyTime()
        pms.NOMBRE_PERIODES = self._spin_periods.value()
        pms.TAILLE_GROUPES = self._spin_groups.value()
        self.accept()


class GuiRecapitulatif(QtGui.QDialog):
    """
    Dialog for the summary, for repeated game or one-shot.
    If ecran_historique is set it replaces the default GuiHistorique
    """

    def __init__(self, remote, defered, automatique, parent, period, historique,
                 summary_text, triangle_transactions, star_transactions):
        """

        :param defered:
        :param automatique:
        :param parent:
        :param period:
        :param historique:
        :param summary_text:
        :param history_screen:
        :param size_histo: the size of the history table. The width of the
        explanation area will be the same than the width of the history table
        :return:
        """
        super(GuiRecapitulatif, self).__init__(parent)

        self._remote = remote
        self._defered = defered
        self._automatique = automatique

        layout = QtGui.QVBoxLayout(self)

        # period label and history button --------------------------------------
        self.ecran_historique = GuiHistorique(
            self, historique, size=SIZE_HISTO)
        layout_period = QtGui.QHBoxLayout()
        label_period = QtGui.QLabel(le2mtrans("Period") + " {}".format(period))
        layout_period.addWidget(label_period)
        layout_period.addSpacerItem(
            QtGui.QSpacerItem(20, 5, QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Fixed))
        button_history = QtGui.QPushButton(le2mtrans("History"))
        button_history.clicked.connect(self.ecran_historique.show)
        layout_period.addWidget(button_history)
        layout.addLayout(layout_period)

        # timer
        self._compte_rebours = WCompterebours(
            parent=self, temps=pms.SUMMARY_TIME, actionfin=self._display_warning)
        layout.addWidget(self._compte_rebours)

        # explanation zone -----------------------------------------------------
        self.widexplication = WExplication(text=summary_text, parent=self,
                                           size=(SIZE_HISTO[0], 80))
        layout.addWidget(self.widexplication)

        # transactions ---------------------------------------------------------
        try:
            max_triangle_price = max(triangle_transactions.MRI_trans_price)
        except ValueError:  # no transaction
            max_triangle_price = 0
        try:
            max_star_price = max(star_transactions.MRI_trans_price)
        except ValueError:
            max_star_price = 0
        max_price = max(max_triangle_price, max_star_price)

        transactions_layout = QtGui.QGridLayout()
        layout.addLayout(transactions_layout)

        # triangle ---
        triangle_label = QtGui.QLabel(trans_MRI(u"Triangle"))
        triangle_label.setStyleSheet("font-weight: bold;")
        transactions_layout.addWidget(triangle_label, 0, 0)
        self._triangle_transaction_zone = TransactionZone(zone_size=(450, 250))
        try:
            for i, item in triangle_transactions.iterrows():
                price = item.MRI_trans_price
                buyer = item.MRI_trans_buyer
                seller = item.MRI_trans_seller
                implied, buyer_or_seller = False, None
                if buyer == self._remote.le2mclt.uid or \
                                seller == self._remote.le2mclt.uid:
                    implied = True
                    buyer_or_seller = pms.BUYER if \
                        buyer == self._remote.le2mclt.uid else pms.SELLER
                color = "blue" if implied else "black"
                self._triangle_transaction_zone.add_transaction(
                    price, buyer_or_seller, color)
        except ValueError:  # no transactions
            pass
        transactions_layout.addWidget(self._triangle_transaction_zone, 1, 0)
        self._triangle_transactions_graph = GraphicalZone(
            triangle_transactions, max_price, pms.TRIANGLE, zone_size=(450, 250))
        transactions_layout.addWidget(self._triangle_transactions_graph, 2, 0)

        # star ---
        star_label = QtGui.QLabel(trans_MRI(u"Star"))
        star_label.setStyleSheet("font-weight: bold;")
        transactions_layout.addWidget(star_label, 0, 2)
        self._star_transaction_zone = TransactionZone(zone_size=(450, 250))
        try:
            for i, item in star_transactions.iterrows():
                price = item.MRI_trans_price
                buyer = item.MRI_trans_buyer
                seller = item.MRI_trans_seller
                implied, buyer_or_seller = False, None
                if buyer == self._remote.le2mclt.uid or \
                                seller == self._remote.le2mclt.uid:
                    implied = True
                    buyer_or_seller = pms.BUYER if \
                        buyer == self._remote.le2mclt.uid else pms.SELLER
                color = "blue" if implied else "black"
                self._star_transaction_zone.add_transaction(
                    price, buyer_or_seller, color)
        except ValueError:  # no transactions
            pass
        transactions_layout.addWidget(self._star_transaction_zone, 1, 2)
        self._star_transactions_graph = GraphicalZone(
            star_transactions, max_price, pms.STAR, zone_size=(450, 250))
        transactions_layout.addWidget(self._star_transactions_graph, 2, 2)

        separator = QtGui.QFrame()
        separator.setFrameShape(QtGui.QFrame.VLine)
        transactions_layout.addWidget(
            separator, 0, 1, transactions_layout.rowCount(), 1)

        # history table --------------------------------------------------------
        # in this screen we only keep the header and the last line of the
        # history
        histo_recap = [historique[0], historique[-1]]
        self.tablemodel = TableModelHistorique(histo_recap)
        self.widtableview = WTableview(parent=self, tablemodel=self.tablemodel,
                                       size=(SIZE_HISTO[0], 100))
        self.widtableview.ui.tableView.verticalHeader().setResizeMode(
            QtGui.QHeaderView.Stretch)
        layout.addWidget(self.widtableview)

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)

        # automatique
        if self._automatique:
            self._timer_automatique = QtCore.QTimer()
            self._timer_automatique.timeout.connect(
                buttons.button(QtGui.QDialogButtonBox.Ok).click)
            self._timer_automatique.start(7000)

        # taille et titre
        self.setWindowTitle(le2mtrans(u"Summary"))
        # self.adjustSize()
        # self.setFixedSize(self.size())

    def _accept(self):
        """
        :return:
        """
        try:
            self._timer_automatique.stop()
        except AttributeError:
            pass
        try:
            self._compte_rebours.stop()
        except AttributeError:
            pass
        logger.info(u"callback: Ok summary")
        self._defered.callback(1)
        self.accept()

    def reject(self):
        pass

    def _display_warning(self):
        self._compte_rebours.setStyleSheet("color: red;")


class DWebView(QtGui.QDialog):
    def __init__(self, html_file):
        QtGui.QDialog.__init__(self)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        browser = QtWebKit.QWebView()
        layout.addWidget(browser)

        html_url = QtCore.QUrl.fromLocalFile(html_file)
        browser.load(html_url)

        button = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        button.accepted.connect(self.accept)
        layout.addWidget(button)

        self.setWindowTitle(u"WebView")
        self.adjustSize()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    transactions = [
        {'MRI_trans_contract': 0, 'MRI_trans_time': u'13:21:24',
         'MRI_trans_price': 0.3, 'MRI_trans_seller': u'201701241320_j_1',
         'MRI_trans_buyer': u'201701241320_j_0'},
        {'MRI_trans_contract': 0, 'MRI_trans_time': u'13:21:34',
         'MRI_trans_price': 0.3, 'MRI_trans_seller': u'201701241320_j_1',
         'MRI_trans_buyer': u'201701241320_j_0'},
        {'MRI_trans_contract': 0, 'MRI_trans_time': u'13:21:39',
         'MRI_trans_price': 0.3, 'MRI_trans_seller': u'201701241320_j_1',
         'MRI_trans_buyer': u'201701241320_j_0'}
    ]
    graph = GraphicalZone(transactions, 2.5)
    graph.show()
    sys.exit(app.exec_())
