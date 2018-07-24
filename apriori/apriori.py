#!/usr/bin/env python

"""
a simple implementation of Apriori algorithm by Python.
"""

import sys
import argparse
from collections import namedtuple
from itertools import combinations
from itertools import chain
sys.path.insert(0, '../util')
import constants


################################################################################
# Data structures.
################################################################################
class TransactionManager(object):
    """
    Transaction managers.
    """

    def __init__(self, transactions):
        """
        Initialize.

        Arguments:
            transactions -- A transaction iterable object
                            (eg. [['A', 'B'], ['B', 'C']]).
        """
        self.__num_transaction = 0
        self.__items = []
        self.__transaction_index_map = {}

        for transaction in transactions:
            self.add_transaction(transaction)

    def add_transaction(self, transaction):
        """
        Add a transaction.

        Arguments:
            transaction -- A transaction as an iterable object (eg. ['A', 'B']).
        """
        for item in transaction:
            if item not in self.__transaction_index_map:
                self.__items.append(item)
                self.__transaction_index_map[item] = set()
            self.__transaction_index_map[item].add(self.__num_transaction)
        self.__num_transaction += 1

    def calc_support(self, items):
        """
        Returns a support for items.

        Arguments:
            items -- Items as an iterable object (eg. ['A', 'B']).
        """
        # Empty items is supported by all transactions.
        if not items:
            return 1.0

        # Empty transactions supports no items.
        if not self.num_transaction:
            return 0.0

        # Create the transaction index intersection.
        sum_indexes = None
        for item in items:
            indexes = self.__transaction_index_map.get(item)
            if indexes is None:
                # No support for any set that contains a not existing item.
                return 0.0

            if sum_indexes is None:
                # Assign the indexes on the first time.
                sum_indexes = indexes
            else:
                # Calculate the intersection on not the first time.
                sum_indexes = sum_indexes.intersection(indexes)

        # Calculate and return the support.
        return len(sum_indexes)

    def initial_candidates(self):
        """
        Returns the initial candidates.
        """
        return [frozenset([item]) for item in self.items]

    @property
    def num_transaction(self):
        """
        Returns the number of transactions.
        """
        return self.__num_transaction

    @property
    def items(self):
        """
        Returns the item list that the transaction is consisted of.
        """
        return sorted(self.__items)

    @property
    def transaction_index_map(self):
        """
        Returns the item list that the transaction is consisted of.
        """
        return self.__transaction_index_map

    @staticmethod
    def create(transactions):
        """
        Create the TransactionManager with a transaction instance.
        If the given instance is a TransactionManager, this returns itself.
        """
        if isinstance(transactions, TransactionManager):
            return transactions
        return TransactionManager(transactions)


# Ignore name errors because these names are namedtuples.
SupportRecord = namedtuple( # pylint: disable=C0103
    'SupportRecord', ('items', 'support'))
RelationRecord = namedtuple( # pylint: disable=C0103
    'RelationRecord', SupportRecord._fields + ('ordered_statistics',))
OrderedStatistic = namedtuple( # pylint: disable=C0103
    'OrderedStatistic', ('items_base', 'items_add', 'antecedent_support', 'rule_support', 'confidence',))


################################################################################
# Inner functions.
################################################################################
def create_next_candidates(prev_candidates, length):
    """
    Returns the apriori candidates as a list.

    Arguments:
        prev_candidates -- Previous candidates as a list.
        length -- The lengths of the next candidates.
    """
    # Solve the items.
    item_set = set()
    for candidate in prev_candidates:
        for item in candidate:
            item_set.add(item)
    items = sorted(item_set)

    # Create the temporary candidates. These will be filtered below.
    tmp_next_candidates = (frozenset(x) for x in combinations(items, length))
    # Return all the candidates if the length of the next candidates is 2
    # because their subsets are the same as items.
    if length < 3:
        return list(tmp_next_candidates)

    # Filter candidates that all of their subsets are
    # in the previous candidates.
    next_candidates = [
        candidate for candidate in tmp_next_candidates
        if all(
            True if frozenset(x) in prev_candidates else False
            for x in combinations(candidate, length - 1))
    ]
    return next_candidates


def gen_support_records(transaction_manager, min_support, **kwargs):
    """
    Returns a generator of support records with given transactions.

    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        min_support -- A minimum support (float).

    Keyword arguments:
        max_length -- The maximum length of relations (integer).
    """
    # Parse arguments.
    max_length = kwargs.get('max_length')

    # For testing.
    _create_next_candidates = kwargs.get(
        '_create_next_candidates', create_next_candidates)

    # Process.
    candidates = transaction_manager.initial_candidates()
    length = 1
    while candidates:
        relations = set()
        for relation_candidate in candidates:
            support = transaction_manager.calc_support(relation_candidate)
            if support < min_support:
                continue
            candidate_set = frozenset(relation_candidate)
            relations.add(candidate_set)
            yield SupportRecord(candidate_set, support)
        length += 1
        if max_length and length > max_length:
            break
        candidates = _create_next_candidates(relations, length)


def gen_ordered_statistics(transaction_manager, record):
    """
    Returns a generator of ordered statistics as OrderedStatistic instances.

    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        record -- A support record as a SupportRecord instance.
    """
    items = record.items
    for combination_set in combinations(sorted(items), len(items) - 1):
        items_base = frozenset(combination_set)
        items_add = frozenset(items.difference(items_base))
        antecedent_support = transaction_manager.calc_support(items_base)
        confidence = float(record.support) / antecedent_support
        yield OrderedStatistic(
            frozenset(items_base), frozenset(items_add), antecedent_support, record.support, confidence)


def filter_ordered_statistics(ordered_statistics, **kwargs):
    """
    Filter OrderedStatistic objects.

    Arguments:
        ordered_statistics -- A OrderedStatistic iterable object.

    Keyword arguments:
        min_confidence -- The minimum confidence of relations (float).
    """
    min_confidence = kwargs.get('min_confidence', 0.5)

    for ordered_statistic in ordered_statistics:
        if ordered_statistic.items_base == frozenset():
            continue
        if ordered_statistic.confidence < min_confidence:
            continue
        yield ordered_statistic


def get_classifications(filtered_ordered_statistics, classifier):

    for filtered_ordered_statistic in filtered_ordered_statistics:
        if filtered_ordered_statistic.items_add not in classifier:
            continue
        yield filtered_ordered_statistic


################################################################################
# API function.
################################################################################
def generate_association_rules(transactions, min_support, **kwargs):
    """
    Executes Apriori algorithm and returns a RelationRecord generator.

    Arguments:
        transactions -- A transaction iterable object
                        (eg. [['A', 'B'], ['B', 'C']]).

    Keyword arguments:
        min_support -- The minimum support of relations (float).
        min_confidence -- The minimum confidence of relations (float).
        min_lift -- The minimum lift of relations (float).
        max_length -- The maximum length of the relation (integer).
    """
    # Parse the arguments.

    min_confidence = kwargs.get('min_confidence', 0.5)

    # Check arguments.
    if min_support <= 0:
        raise ValueError('minimum support must be > 0')

    # For testing.
    _gen_support_records = kwargs.get(
        '_gen_support_records', gen_support_records)
    _gen_ordered_statistics = kwargs.get(
        '_gen_ordered_statistics', gen_ordered_statistics)
    _filter_ordered_statistics = kwargs.get(
        '_filter_ordered_statistics', filter_ordered_statistics)

    # Calculate supports.
    transaction_manager = TransactionManager.create(transactions)
    support_records = _gen_support_records(
        transaction_manager, min_support)

    # Calculate ordered stats.
    rules = []
    for support_record in support_records:
        ordered_statistics = list(
            _filter_ordered_statistics(
                _gen_ordered_statistics(transaction_manager, support_record),
                min_confidence=min_confidence,
            )
        )
        if not ordered_statistics:
            continue
        for ordered_statistic in ordered_statistics:
            antecedent = tuple(sorted(ordered_statistic.items_base))
            # transform antecedent and consequent into sets
            antecedent_set = set(antecedent)
            consequent = tuple(ordered_statistic.items_add)
            consequent_set = set(consequent)
            consequent_str = ''
            for el in consequent:
                consequent_str += el + ','
            consequent_str = consequent_str[:-1]
            antecedent_str = ''
            for el in antecedent:
                antecedent_str += el + ','
            antecedent_str = antecedent_str[:-1]
            a_rule = {constants.LHS: antecedent_str, constants.RHS: consequent_str,
                      constants.LHS_SET: antecedent_set, constants.RHS_SET: consequent_set,
                      constants.LHS_SUPP_COUNT: ordered_statistic.antecedent_support,
                      constants.RULE_SUPP_COUNT: ordered_statistic.rule_support,
                      constants.LHS_SUPP: float(ordered_statistic.antecedent_support)
                                          / transaction_manager.num_transaction,
                      constants.RULE_SUPP: float(ordered_statistic.rule_support) / transaction_manager.num_transaction,
                      constants.RULE_CONF: ordered_statistic.confidence, constants.LINKS: ''}
            rules.append(a_rule)
    return rules


def generate_classification_rules(transactions, classifier, min_support, **kwargs):
    min_confidence = kwargs.get('min_confidence', 0.5)

    # Check arguments.
    if min_support <= 0:
        raise ValueError('minimum support must be > 0')

    # For testing.
    _gen_support_records = kwargs.get(
        '_gen_support_records', gen_support_records)
    _gen_ordered_statistics = kwargs.get(
        '_gen_ordered_statistics', gen_ordered_statistics)
    _filter_ordered_statistics = kwargs.get(
        '_filter_ordered_statistics', filter_ordered_statistics)
    _get_classifications = kwargs.get(
        '_get_classifications', get_classifications)

    # Calculate supports.
    transaction_manager = TransactionManager.create(transactions)
    support_records = _gen_support_records(
        transaction_manager, min_support)

    # Calculate ordered stats.
    rules = []
    for support_record in support_records:
        ordered_statistics = list(
            _get_classifications(
                _filter_ordered_statistics(
                    _gen_ordered_statistics(transaction_manager, support_record),
                    min_confidence=min_confidence,
                ),
                classifier
            )
        )
        if not ordered_statistics:
            continue
        for ordered_statistic in ordered_statistics:
            antecedent = tuple(sorted(ordered_statistic.items_base))
            # transform antecedent and consequent into sets
            antecedent_set = set(antecedent)
            consequent = tuple(ordered_statistic.items_add)
            consequent_set = set(consequent)
            consequent_str = ''
            for el in consequent:
                consequent_str += el + ','
            consequent_str = consequent_str[:-1]
            antecedent_str = ''
            for el in antecedent:
                antecedent_str += el + ','
            antecedent_str = antecedent_str[:-1]
            a_rule = {constants.LHS: antecedent_str, constants.RHS: consequent_str,
                      constants.LHS_SET: antecedent_set, constants.RHS_SET: consequent_set,
                      constants.LHS_SUPP_COUNT: ordered_statistic.antecedent_support,
                      constants.RULE_SUPP_COUNT: ordered_statistic.rule_support,
                      constants.LHS_SUPP: float(ordered_statistic.antecedent_support)
                                          / transaction_manager.num_transaction,
                      constants.RULE_SUPP: float(ordered_statistic.rule_support) / transaction_manager.num_transaction,
                      constants.RULE_CONF: ordered_statistic.confidence, constants.LINKS: ''}
            rules.append(a_rule)
    return rules
