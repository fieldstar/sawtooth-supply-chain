# Copyright 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

import logging
import re

from journal import transaction, global_store_manager
from journal.messages import transaction_message

from sawtooth_battleship.battleship_exceptions import BattleshipException

LOGGER = logging.getLogger(__name__)


def _register_transaction_types(ledger):
    """Registers the Battleship transaction types on the ledger.

    Args:
        ledger (journal.journal_core.Journal): The ledger to register
            the transaction type against.
    """
    ledger.register_message_handler(
        BattleshipTransactionMessage,
        transaction_message.transaction_message_handler)
    ledger.add_transaction_store(BattleshipTransaction)


class BattleshipTransactionMessage(transaction_message.TransactionMessage):
    """Battleship transaction message represent Battleship transactions.

    Attributes:
        MessageType (str): The class name of the message.
        Transaction (BattleshipTransaction): The transaction the
            message is associated with.
    """
    MessageType = "/Battleship/Transaction"

    def __init__(self, minfo=None):
        if minfo is None:
            minfo = {}

        super(BattleshipTransactionMessage, self).__init__(minfo)

        tinfo = minfo.get('Transaction', {})
        self.Transaction = BattleshipTransaction(tinfo)


class BattleshipTransaction(transaction.Transaction):
    """A Transaction is a set of updates to be applied atomically
    to a ledger.

    It has a unique identifier and a signature to validate the source.

    Attributes:
        TransactionTypeName (str): The name of the Battleship
            transaction type.
        TransactionTypeStore (type): The type of transaction store.
        MessageType (type): The object type of the message associated
            with this transaction.
    """
    TransactionTypeName = '/BattleshipTransaction'
    TransactionStoreType = global_store_manager.KeyValueStore
    MessageType = BattleshipTransactionMessage

    def __init__(self, minfo=None):
        """Constructor for the BattleshipTransaction class.

        Args:
            minfo: Dictionary of values for transaction fields.
        """

        if minfo is None:
            minfo = {}

        super(BattleshipTransaction, self).__init__(minfo)

        LOGGER.debug("minfo: %s", repr(minfo))
        self._name = minfo['Name'] if 'Name' in minfo else None
        self._action = minfo['Action'] if 'Action' in minfo else None
        # TODO: handle 'Board', 'Column', 'Row' 

    def __str__(self):
        try:
            oid = self.OriginatorID
        except AssertionError:
            oid = "unknown"

        if self._action == "CREATE":
            return "{} {} {}".format(oid, self._action, self._name)
        else:
            return "{} {}".format(oid, self._action)

    def is_valid(self, store):
        """Determines if the transaction is valid.

        Args:
            store (dict): Transaction store mapping.
        """

        try:
            self.check_valid(store)
        except BattleshipException as e:
            LOGGER.debug('invalid transaction (%s): %s', str(e), str(self))
            return False

        return True

    def check_valid(self, store):
        """Determines if the transaction is valid.

        Args:
            store (dict): Transaction store mapping.
        """

        if not super(BattleshipTransaction, self).is_valid(store):
            raise BattleshipException("invalid transaction")
        
        LOGGER.debug('checking %s', str(self))

        # Name (of the game) is always required
        if self._name is None or self._name == '':
            raise BattleshipException('name not set')

        # Action is always required
        if self._action is None or self._action == '':
            raise BattleshipException('action not set')

        # The remaining validity rules depend upon which action has
        # been specified.

        if self._action == 'CREATE':    
            if self._name in store:
                raise BattleshipException('game already exists')

            # Restrict game name letters and numbers.
            if not re.match("^[a-zA-Z0-9]*$", self._name):
                raise BattleshipException("Only letters a-z A-Z and numbers 0-9 are allowed in the game name!")

            LOGGER.error("in check_valid, CREATE is not fully implemented")
        elif self._action == 'JOIN':
            # TODO: Check that the game can be joined (the state is 'NEW')

            # Check that self._name is in the store (to verify 
            # that the game exists (see FIRE below).
            if self._name not in store:
                raise BattleshipException('Trying to join a game that does not exist')

            # TODO: Validate that self._board is a valid board (right size,
            # right content.

            # TODO: Remove this logging statement when all other TODOs
            # have been resolved for JOIN
            LOGGER.error("in check_valid, JOIN is not fully implemented")
        elif self._action == 'FIRE':
            if self._name not in store:
                raise BattleshipException('no such game')
            
            # TODO: Check that self._column is valid (letter from A-J)

            # TODO: Check that self._row is valid (number from 1-10)

            state = store[self._name]['State']

            if state in ['P1-WIN', 'P2-WIN']:
                raise BattleshipException('game complete')

            # TODO: Check that the state is not 'NEW', which would imply
            # that the players have not yet joined.

            player = None
            if state == 'P1-NEXT':
                player = store[self._name]['Player1']
                if player != self.OriginatorID:
                    raise BattleshipException('invalid player 1')
            elif state == 'P2-NEXT':
                player = store[self._name]['Player2']
                if player != self.OriginatorID:
                    raise BattleshipException('invalid player 2')
            else:
                raise BattleshipException("invalid state: {}".format(state))

            # TODO: Check whether the board's column and row have already been
            # fired upon.  Note there are two boards, so the board used
            # depends upon which player's turn it is.

            # TODO: Remove this logging statement when all other TODOs
            # have been resolved for FIRE
            LOGGER.error("in check_valid, FIRE is not fully implemented")
        else:
            raise BattleshipException('invalid action: {}'.format(self._action))


    def apply(self, store):
        """Applies all the updates in the transaction to the transaction
        store.

        Args:
            store (dict): Transaction store mapping.
        """
        LOGGER.debug('apply %s', str(self))

        if self._action == 'CREATE':
            store[self._name] = { 'State': 'NEW' }
        elif self._action == 'JOIN':
            game = store[self._name].copy()

            # TODO: if this is the first JOIN, set Board1 and Player1 in
            # the store.  if this is the second JOIN, set Board2 and Player2
            # in the store.  Also, initialie TargetBoard1 and TargetBoard2
            # as empty.

            # TODO: this should only move to 'P1-NEXT' if both boards have
            # been entered.
            game["State"] = 'P1-NEXT'

            # TODO: Remove this logging statement when all other TODOs
            # have been resolved for JOIN
            LOGGER.error("in apply, JOIN is not fully implemented")

            store[self._name] = game
        elif self._action == 'FIRE':
            game = store[self._name].copy()

            # TODO: Reveal.  Update TargetBoard1 or TargetBoard2 as
            # appropriate, depending on the current player (determined by
            # State).  Use the LastFireColumn and LastFireRow.

            # TODO: Update LastFireColumn and LastFireRow in the store so
            # they can be used for last time.  (Set them to self._column and
            # self._row.)

            # TODO: detect if the game has been won, changing the State
            # to P1-WIN or P2-WIN as appropriate

            if game['State'] == 'P1-NEXT':
                game['State'] = 'P2-NEXT'
            elif game['State'] == 'P2-NEXT':
                game['State'] = 'P1-NEXT'

            # TODO: Remove this logging statement when all other TODOs
            # have been resolved for FIRE
            LOGGER.error("in apply, FIRE is not fully implemented")

            store[self._name] = game
        else:
            raise BattleshipException("invalid state: {}".format(state))

         
    def dump(self):
        """Returns a dict with attributes from the transaction object.

        Returns:
            dict: The updates from the transaction object.
        """
        result = super(BattleshipTransaction, self).dump()

        result['Name'] = self._name
        result['Action'] = self._action
        # TODO: handle 'Board', 'Column', 'Row'; only add them to the result
        # if they are valid arguments for the Action

        return result
