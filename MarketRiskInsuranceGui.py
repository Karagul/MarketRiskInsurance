# -*- coding: utf-8 -*-
"""
This module contains the GUI
"""

import sys
import logging
from PyQt4 import QtGui, QtCore
from twisted.internet import defer
from random import randint, choice
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceTexts import trans_MRI
import MarketRiskInsuranceTexts as texts_MRI
from client.cltgui.cltguidialogs import GuiHistorique
from client.cltgui.cltguiwidgets import WPeriod, WExplication, WCompterebours


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
        self.label_balance = QtGui.QLabel(u"...")
        self.label_balance.setAlignment(QtCore.Qt.AlignRight)
        self.form.addRow(QtGui.QLabel(trans_MRI(u"Your account:")),
                         self.label_balance)
        self.label_balance_if_triangle = QtGui.QLabel(u"...")
        self.label_balance_if_triangle.setAlignment(QtCore.Qt.AlignRight)
        self.form.addRow(QtGui.QLabel(trans_MRI(u"Payoff if triangle:")),
                         self.label_balance_if_triangle)
        self.label_balance_if_star = QtGui.QLabel(u"...")
        self.label_balance_if_star.setAlignment(QtCore.Qt.AlignRight)
        self.form.addRow(QtGui.QLabel(trans_MRI(u"Payoff if star:")),
                         self.label_balance_if_star)

        self.layout.addSpacerItem(QtGui.QSpacerItem(
            20, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))


class OfferZone(QtGui.QWidget):
    def __init__(self, purchase_or_sell):
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

        self.list = QtGui.QListView()
        self.model = QtGui.QStandardItemModel()
        self.list.setModel(self.model)
        self.list.setFixedSize(350, 250)
        self.layout_main.addWidget(self.list)

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
        self.pushbutton_send.setMaximumWidth(100)
        self.pushbutton_send.setToolTip(
            trans_MRI(u"Make an offer or replace the current one"))
        self.layout_offer.addWidget(self.pushbutton_send)
        self.layout_offer.addSpacerItem(
            QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Minimum))

        self.layout_accept_remove = QtGui.QHBoxLayout()
        self.layout_main.addLayout(self.layout_accept_remove)
        self.pushbutton_accept = QtGui.QPushButton(
            trans_MRI(u"Accept the selected offer"))
        self.pushbutton_accept.setMinimumWidth(180)
        self.pushbutton_accept.setToolTip(
            trans_MRI(u"Select an offer and click on this button to "
                      u"accept it"))
        self.layout_accept_remove.addWidget(self.pushbutton_accept)

        self.pushbutton_remove = QtGui.QPushButton(trans_MRI(u"Remove my offer"))
        self.pushbutton_remove.setMinimumWidth(150)
        self.pushbutton_remove.setToolTip(
            trans_MRI(u"If you have an offer click here to remove it"))
        self.layout_accept_remove.addWidget(
            self.pushbutton_remove)
        self.layout_accept_remove.addSpacerItem(
            QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Minimum))

        # connections
        self.list.clicked.connect(self._set_current_offer)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def _set_current_offer(self, index):
        current_item = self.model.item(index.row(), 0)
        for k, v in self._offers.viewitems():
            if v == current_item:
                self.current_offer = {
                    "MRI_offer_sender": k,
                    "MRI_offer_type": self._purchase_or_sell,
                    "MRI_offer_price": v.value()}

    def add_offer(self, sender, price, color):
        # remove the current offer
        self.remove_offer(sender)
        # add the new offer
        item = MyStandardItem(price)
        item.setForeground(QtGui.QColor(color))
        self.model.appendRow(item)
        self._sort()
        self._offers[sender] = item

    def remove_offer(self, sender):
        """
        Remove the offer from the list
        :param sender:
        :return:
        """
        offer_item = self._offers.pop(sender, None)
        if offer_item is not None:
            for row in range(self.model.rowCount()):
                if self.model.item(row, 0) == offer_item:
                    self.model.removeRow(row)
                    break
            self._sort()

    def _sort(self):
        if self._purchase_or_sell == pms.BUY:
            self.model.sort(0, QtCore.Qt.DescendingOrder)
        else:
            self.model.sort(0, QtCore.Qt.AscendingOrder)

    def clear(self):
        """
        we clear both the model and the dict that stores the offers
        :return:
        """
        self.model.clear()
        self._offers.clear()

    def exists_offer(self, price):
        """
        We check whether there exists an offer with that price.
        If it does return the offer. If it doesn't return False
        :param price:
        :return:
        """
        for k, v in self._offers.viewitems():
            if v.value() == price:
                existing_offer = dict()
                existing_offer["MRI_offer_sender"] = k
                existing_offer["MRI_offer_price"] = v.value()
                logger.debug(u"exists_offer: {}".format(existing_offer))
                return existing_offer
        return False


class TransactionZone(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QtGui.QLabel(trans_MRI(u"Transactions"))
        self.layout.addWidget(self.label)
        self.list = QtGui.QListView()
        self.list.setFixedSize(400, 200)
        self.layout.addWidget(self.list)
        self.model = QtGui.QStandardItemModel()
        self.list.setModel(self.model)

    def add_transaction(self, price, buyer, seller, color):
        item = MyStandardItem(price)
        item.setForeground(QtGui.QColor(color))
        self.model.insertRow(0, item)

    def clear(self):
        self.model.clear()


class GuiDecision(QtGui.QDialog):
    def __init__(self, defered, automatique, parent, period, historique, remote):
        super(GuiDecision, self).__init__(parent)

        # variables
        self._defered = defered
        self._automatique = automatique
        self._historique = GuiHistorique(self, historique)
        self._remote = remote

        layout = QtGui.QVBoxLayout(self)

        wperiod = WPeriod(
            period=period, ecran_historique=self._historique)
        layout.addWidget(wperiod)

        wexplanation = WExplication(
            text=texts_MRI.get_text_explanation(),
            size=(800, 100), parent=self)
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
        self._triangle_purchase_zone = OfferZone(pms.BUY)
        market_layout.addWidget(self._triangle_purchase_zone, 1, 0)
        self._triangle_sell_zone = OfferZone(pms.SELL)
        market_layout.addWidget(self._triangle_sell_zone, 1, 1)
        self._triangle_transactions = TransactionZone()
        market_layout.addWidget(self._triangle_transactions, 2, 0, 1, 2)

        # star
        star_label = QtGui.QLabel(trans_MRI(u"Star"))
        star_label.setStyleSheet("color: red;")
        market_layout.addWidget(star_label, 0, 3, 1, 2)
        self._star_purchase_zone = OfferZone(pms.BUY)
        market_layout.addWidget(self._star_purchase_zone, 1, 3)
        self._star_sell_zone = OfferZone(pms.SELL)
        market_layout.addWidget(self._star_sell_zone, 1, 4)
        self._star_transactions = TransactionZone()
        market_layout.addWidget(self._star_transactions, 2, 3, 1, 2)

        separator = QtGui.QFrame()
        separator.setFrameShape(QtGui.QFrame.VLine)
        market_layout.addWidget(separator, 0, 2, market_layout.rowCount(), 1)

        # finalisation =========================================================
        layout.addSpacing(50)
        self._make_connections()
        self.setWindowTitle(trans_MRI(u"Market"))
        self.adjustSize()
        self.setFixedSize(self.size())

        if self._automatique:
            self._timer_automatique = QtCore.QTimer()
            self._timer_automatique.timeout.connect(self._play_auto)
            self._timer_automatique.start(7000)
                
    def _make_connections(self):
        """
        Connect the pushbutton of the different offer zones to the method
        of GUIDecision (add
        :return:
        """
        # send offer ===========================================================
        self._triangle_purchase_zone.pushbutton_send.clicked.connect(
            lambda _: self._add_offer(
                pms.TRIANGLE, pms.BUY,
                self._triangle_purchase_zone.spin_offer.value()))
        self._triangle_sell_zone.pushbutton_send.clicked.connect(
            lambda _: self._add_offer(
                pms.TRIANGLE, pms.SELL,
                self._triangle_sell_zone.spin_offer.value()))

        self._star_purchase_zone.pushbutton_send.clicked.connect(
            lambda _: self._add_offer(
                pms.STAR, pms.BUY,
                self._star_purchase_zone.spin_offer.value()))

        self._star_sell_zone.pushbutton_send.clicked.connect(
            lambda _: self._add_offer(
                pms.STAR, pms.SELL, self._star_sell_zone.spin_offer.value()))
        
        # remove offer =========================================================
        self._triangle_purchase_zone.pushbutton_remove.clicked.connect(
            lambda _: self._remove_offer(pms.TRIANGLE, pms.BUY))
        self._triangle_sell_zone.pushbutton_remove.clicked.connect(
            lambda _: self._remove_offer(pms.TRIANGLE, pms.SELL))
        self._star_purchase_zone.pushbutton_remove.clicked.connect(
            lambda _: self._remove_offer(pms.STAR, pms.BUY))
        self._star_sell_zone.pushbutton_remove.clicked.connect(
            lambda _: self._remove_offer(pms.STAR, pms.SELL))

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
    def _add_offer(self, triangle_or_star, buy_or_sell, price):
        """
        send the offer to the server
        called by pushbutton_send of the offer zone
        """
        logger.info("add_offer: contract {} - type {} - price {}".format(
            triangle_or_star, buy_or_sell, price))
        # we test whether there exists an offer with the same price
        if triangle_or_star == pms.TRIANGLE:
            if buy_or_sell == pms.BUY:
                existing_offer = self._triangle_sell_zone.exists_offer(price)
            else:
                existing_offer = self._triangle_purchase_zone.exists_offer(price)
        else:
            if buy_or_sell == pms.BUY:
                existing_offer = self._star_sell_zone.exists_offer(price)
            else:
                existing_offer = self._star_purchase_zone.exists_offer(price)

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
                     "MRI_offer_price": price}
            yield (self._remote.add_offer(offer))

    def add_offer(self, offer):
        """
        add the offer to the list
        called by remote
        :param offer:
        :return:
        """
        sender = offer["MRI_offer_sender"]
        price = offer["MRI_offer_price"]
        color = "blue" if sender == self._remote.le2mclt.uid else "black"
        if offer["MRI_offer_contract"] == pms.TRIANGLE:
            if offer["MRI_offer_type"] == pms.BUY:
                self._triangle_purchase_zone.add_offer(sender, price, color)
            else:  # purchase
                self._triangle_sell_zone.add_offer(sender, price, color)
        else:  # star
            if offer["MRI_offer_type"] == pms.BUY:
                self._star_purchase_zone.add_offer(sender, price, color)
            else:  # purchase
                self._star_sell_zone.add_offer(sender, price, color)
        
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
        try:
            if existing_offer["MRI_offer_sender"] != self._remote.le2mclt.uid:
                existing_offer["MRI_offer_contract"] = triangle_or_star
                new_offer = dict()
                new_offer["MRI_offer_contract"] = \
                    existing_offer["MRI_offer_contract"]
                new_offer["MRI_offer_price"] = existing_offer["MRI_offer_price"]
                if existing_offer["MRI_offer_type"] == pms.BUY:
                    new_offer["MRI_offer_type"] = pms.SELL
                else:
                    new_offer["MRI_offer_type"] = pms.BUY
                yield (self._remote.add_transaction(existing_offer, new_offer))
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
        if buyer == self._remote.le2mclt.uid or \
                        seller == self._remote.le2mclt.uid:
            color = "blue"
        else:
            color = "black"
        if transaction["MRI_trans_contract"] == pms.TRIANGLE:
            self._triangle_transactions.add_transaction(
                price, buyer, seller, color)
        else:
            self._star_transactions.add_transaction(price, buyer, seller, color)

    def update_balance(self, balance, balance_if_triangle, balance_if_star):
        self._information.label_balance.setText(str(balance))
        self._information.label_balance_if_triangle.setText(str(balance_if_triangle))
        self._information.label_balance_if_star.setText(str(balance_if_star))

    def display_offer_failure(self):
        QtGui.QMessageBox.warning(
            self, trans_MRI(u"Be careful"),
            trans_MRI(u"You can't do this offer"))
        return

    def _play_auto(self):
        """
        called by the timer when the program play automatically
        :return:
        """
        # make an offer
        triangle_or_star = choice([pms.TRIANGLE, pms.STAR])
        buy_or_sell = choice([pms.BUY, pms.SELL])
        value = randint(0, pms.OFFER_MAX)


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
            list(sorted(pms.TREATMENTS_NAMES.viewvalues())))
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

        # trial
        self._checkbox_essai = QtGui.QCheckBox()
        self._checkbox_essai.setChecked(pms.PERIODE_ESSAI)
        form.addRow(QtGui.QLabel(trans_MRI(u"Trail period")), self._checkbox_essai)

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
        self._timeEdit = QtGui.QTimeEdit()
        self._timeEdit.setDisplayFormat("hh:mm:ss")
        self._timeEdit.setTime(QtCore.QTime(pms.MARKET_TIME.hour,
                                            pms.MARKET_TIME.minute,
                                            pms.MARKET_TIME.second))
        self._timeEdit.setMaximumWidth(100)
        form.addRow(QtGui.QLabel(trans_MRI(u"Market duration")), self._timeEdit)

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
        pms.PERIODE_ESSAI = self._checkbox_essai.isChecked()
        pms.MARKET_TIME = self._timeEdit.time().toPyTime()
        pms.NOMBRE_PERIODES = self._spin_periods.value()
        pms.TAILLE_GROUPES = self._spin_groups.value()
        self.accept()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    my_screen = GuiDecision(
        defered=None,
        automatique=False,
        parent=None,
        period=1,
        historique=None,
        remote=None
    )
    my_screen.show()
    my_item = MyStandardItem(25.5)
    my_screen.triangle_purchase_zone.model.appendRow(my_item)
    sys.exit(app.exec_())
