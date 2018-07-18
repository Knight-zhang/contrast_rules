#!/usr/bin/env python

"""
this is an implementation of CAR-apriori algorithm based on an existing apriori implementation
"""

import sys
import argparse
import pandas as pd
from collections import namedtuple
from itertools import combinations
from itertools import chain
from itertools import product


################################################################################
# Data structures.
################################################################################
class TransactionManager(object):
    """
    Transaction managers.
    """

    def __init__(self, transactions, classifier):
        """
        Initialize.

        Arguments:
            transactions -- A transaction iterable object
                            (eg. [['A', 'B'], ['B', 'C']]).
            classifier -- A set containing the classifier classes
                            (ef . {'Class1', 'Class2'})
        """
        self.__num_transaction = 0
        self.__items = []
        self.__classifier = classifier
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
        return float(len(sum_indexes)) / self.__num_transaction

    def initial_candidates(self):
        """
        Returns the initial candidates.
        """
        return [frozenset([item]) for item in set(self.items) - self.classifier]

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
        Returns the transaction index map of the items
        """
        return self.__transaction_index_map

    @property
    def classifier(self):
        """
        Returns the set of the classifier
        """
        return self.__classifier

    @staticmethod
    def create(transactions, classifier):
        """
        Create the TransactionManager with a transaction instance.
        If the given instance is a TransactionManager, this returns itself.
        """
        if isinstance(transactions, TransactionManager):
            return transactions
        return TransactionManager(transactions, classifier)


# Ignore name errors because these names are namedtuples.
SupportRecord = namedtuple( # pylint: disable=C0103
    'SupportRecord', ('items', 'support'))
RelationRecord = namedtuple( # pylint: disable=C0103
    'RelationRecord', SupportRecord._fields + ('ordered_statistics',))
OrderedStatistic = namedtuple( # pylint: disable=C0103
    'OrderedStatistic', ('items_base', 'items_add', 'confidence', 'lift',))


################################################################################
# Inner functions.
################################################################################
def create_next_candidates(prev_candidates, classifier, length):
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

    # If the length is 2 we want to make sure that the next candidates contain our classifier
    # so we proceed by a product between the previous 1-itemset and our classifier
    if length < 3:
        tmp_next_candidates = (frozenset(x) for x in product(items, classifier))
        return list(tmp_next_candidates)

    # Make sure our items do not contain the classifier
    items = sorted(set(items) - classifier)
    # Create a temporary generator for next candidates with len = length - 1
    # to be completed with our classifier
    tmp_next_candidates = (x for x in combinations(items, length - 1))
    # Complete the last item with our classifier
    tmp_next_candidates = [x for x in product(list(tmp_next_candidates), classifier)]
    # Using a map function to get the right format
    tmp_next_candidates = map(lambda x: format(x), tmp_next_candidates)
    return list(tmp_next_candidates)


def gen_support_records(transaction_manager, classifier, min_support, **kwargs):
    """
    Returns a generator of support records with given transactions.

    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        classifier -- A set of our classes
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
            if length == 1:
                # We don't need to generate the 1 - frequent items
                continue
            yield SupportRecord(candidate_set, support)
        length += 1
        if max_length and length > max_length:
            break
        candidates = _create_next_candidates(relations, classifier, length)


def gen_ordered_statistics(transaction_manager, record):
    """
    Returns a generator of ordered statistics as OrderedStatistic instances.

    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        record -- A support record as a SupportRecord instance.
    """
    items = record.items
    combination_set = sorted(set(items) - transaction_manager.classifier.intersection(set(items)))
    items_base = frozenset(combination_set)
    items_add = frozenset(transaction_manager.classifier.intersection(set(items)))
    confidence = (
        record.support / transaction_manager.calc_support(items_base))
    lift = confidence / transaction_manager.calc_support(items_add)
    yield OrderedStatistic(
        frozenset(items_base), frozenset(items_add), confidence, lift)


def filter_ordered_statistics(ordered_statistics, **kwargs):
    """
    Filter OrderedStatistic objects.

    Arguments:
        ordered_statistics -- A OrderedStatistic iterable object.

    Keyword arguments:
        min_confidence -- The minimum confidence of relations (float).
        min_lift -- The minimum lift of relations (float).
    """
    min_confidence = kwargs.get('min_confidence', 0.0)
    min_lift = kwargs.get('min_lift', 0.0)

    for ordered_statistic in ordered_statistics:
        if ordered_statistic.confidence < min_confidence:
            continue
        if ordered_statistic.lift < min_lift:
            continue
        yield ordered_statistic


################################################################################
# API function.
################################################################################
def CAR_apriori(transactions, classifier, **kwargs):
    """
    Executes Apriori algorithm and returns a RelationRecord generator.

    Arguments:
        transactions -- A transaction iterable object
                        (eg. [['A', 'B'], ['B', 'C']]).
        index_classifier -- The index of the classifier in the data set

    Keyword arguments:
        min_support -- The minimum support of relations (float).
        min_confidence -- The minimum confidence of relations (float).
        min_lift -- The minimum lift of relations (float).
        max_length -- The maximum length of the relation (integer).
    """
    # Parse the arguments.

    min_support = kwargs.get('min_support', 0.1)
    min_confidence = kwargs.get('min_confidence', 0.0)
    min_lift = kwargs.get('min_lift', 0.0)
    max_length = kwargs.get('max_length', None)

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
    transaction_manager = TransactionManager.create(transactions, classifier)
    support_records = _gen_support_records(
        transaction_manager, classifier, min_support, max_length=max_length)

    # Calculate ordered stats.
    for support_record in support_records:
        ordered_statistics = list(
            _filter_ordered_statistics(
                _gen_ordered_statistics(transaction_manager, support_record),
                min_confidence=min_confidence,
                min_lift=min_lift,
            )
        )
        if not ordered_statistics:
            continue
        yield RelationRecord(
            support_record.items, support_record.support, ordered_statistics)


def load_base(location, delimiter):
    data = pd.read_csv(location, delimiter=delimiter, header=None)
    return data


def initialize(data, class_index):
    split_data = data[0].str.split(',', expand=True)
    classifier = set(split_data[split_data.columns[class_index]])
    transactions = []
    for index in range(len(data)):
        transactions.append(data[0][index].split(','))
    return classifier, transactions


def format(x):
    l=[]
    for t in x:
        if type(t) == tuple:
            for e in t:
                l.append(e)
        else:
            l.append(t)
    return frozenset(l)


def run(url, **kwargs):
    delimiter = kwargs.get('delimiter', ';')
    class_index = kwargs.get('class_index', -1)
    min_support = kwargs.get('min_support', 0.1)
    min_confidence = kwargs.get('min_confidence', 0.1)
    data = load_base(url, delimiter)
    classifier, transactions = initialize(data, class_index)
    results = list(CAR_apriori(transactions, classifier, min_support=min_support, min_confidence=min_confidence))
    return results
