#!/usr/bin/env python

"""
this is an implementation of SCR-apriori algorithm based on an existing apriori implementation
"""

import sys
import argparse
import pandas as pd
from collections import namedtuple
from itertools import combinations
from itertools import chain
from itertools import product
from itertools import tee
from memory_profiler import profile


################################################################################
# Data structures.
################################################################################
class TransactionManager(object):
    """
    Transaction managers.
    """

    def __init__(self, transactions, non_varying, varying, classifier):
        """
        Initialize.

        Arguments:
            transactions -- A transaction iterable object
                            (eg. [['A', 'B'], ['B', 'C']]).
            non_varying -- A set containing the non varying attributes
                            (eg. { '01', '03, '12' })
            varying -- A set containing the varying attributes
                            (eg. { '01', '03, '12' })
            classifier -- A set containing the classifier classes
                            (ef . {'Class1', 'Class2'})
        """
        self.__num_transaction = 0
        self.__items = []
        self.__classifier = classifier
        self.__transaction_index_map = {}
        self.__non_varying = non_varying
        self.__varying = varying

        for transaction in transactions:
            self.add_transaction(transaction)

        self.__num_class_1 = len(self.__transaction_index_map.get(self.classifier[0]))
        self.__num_class_2 = self.__num_transaction - self.__num_class_1

    def add_transaction(self, transaction):
        """
        Add a transaction.

        Arguments:
            transaction -- A transaction as an iterable object (eg. ['A', 'B']).
        """
        for item in transaction:
            if item not in self.__transaction_index_map:
                if item not in self.__classifier:
                    self.__items.append(item)
                self.__transaction_index_map[item] = set()
            self.__transaction_index_map[item].add(self.__num_transaction)
        self.__num_transaction += 1

    def create_attribute_value_map(self):
        for item in set(self.__items):
            if item in self.__classifier:
                continue
            if item[:2] not in self.__attribute_value_map.keys():
                self.__attribute_value_map[item[:2]] = [frozenset([item])]
                continue
            self.__attribute_value_map[item[:2]].append(frozenset([item]))

    def calc_support(self, items):
        """
        Returns a support for items with reference to the classifier.

        Arguments:
            items -- Items as an iterable object (eg. ['A', 'B']).
        """
        # Empty items is supported by all transactions.
        if not items:
            return 1.0, 1.0

        # Empty transactions supports no items.
        if not self.num_transaction:
            return 0.0, 0.0

        # Create the transaction index intersection.
        sum_indexes_1 = None
        sum_indexes_2 = None
        for item in items:
            indexes_class_1 = self.__transaction_index_map.get(item).intersection(self.__transaction_index_map.get(
                self.__classifier[0]
            ))
            indexes_class_2 = self.__transaction_index_map.get(item).intersection(self.__transaction_index_map.get(
                self.__classifier[1]
            ))
            if indexes_class_1 is None and indexes_class_2 is None:
                # No support for any set that contains a not existing item.
                return 0.0, 0.0

            if sum_indexes_1 is None:
                # Assign the indexes on the first time.
                sum_indexes_1 = indexes_class_1

            if sum_indexes_2 is None:
                # Assign the indexes on the first time.
                sum_indexes_2 = indexes_class_2

            else:
                # Calculate the intersection on not the first time.
                sum_indexes_1 = sum_indexes_1.intersection(indexes_class_1)
                sum_indexes_2 = sum_indexes_2.intersection(indexes_class_2)

        # Calculate and return the support.
        return float(len(sum_indexes_1)) / self.__num_class_1, float(len(sum_indexes_2)) / self.__num_class_2

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
    def num_class_1(self):
        """
        Returns the number of transactions.
        """
        return self.__num_class_1

    @property
    def num_class_2(self):
        """
        Returns the number of transactions.
        """
        return self.__num_class_2

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

    @property
    def non_varying(self):
        """
        Returns the set of the classifier
        """
        return self.__non_varying

    @property
    def varying(self):
        """
        Returns the set of the classifier
        """
        return self.__varying

    @staticmethod
    def create(transactions, non_varying, varying, classifier):
        """
        Create the TransactionManager with a transaction instance.
        If the given instance is a TransactionManager, this returns itself.
        """
        if isinstance(transactions, TransactionManager):
            return transactions
        return TransactionManager(transactions, non_varying, varying, classifier)


# Ignore name errors because these names are namedtuples.
SupportRecord = namedtuple( # pylint: disable=C0103
    'SupportRecord', ('items', 'support'))
RelationRecord = namedtuple( # pylint: disable=C0103
    'SCR_pattern', ('rule_pairs',))
AttributeRecord = namedtuple( # pylint: disable=C0103
    'Rule', ('attributes', 'invariable_items', 'variable_items', 'antecedent_support', 'class_name',
             'rule_support', 'confidence',))


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
    It excludes the itemsets with support less than min_support
    and itemsets that have no contrasting rules

    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        min_support -- A minimum support (float).

    """

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
            # Exclude candidates with support less then min_support in both classes
            if support[0] < min_support and support[1] < min_support:
                continue
            candidate_set = frozenset(relation_candidate)
            relations.add(candidate_set)
            # If both supports are greater than min_support
            # We don't return them, but we store them and keep looking
            if support[0] > min_support and support[1] > min_support:
                continue
            # Exclude candidates whith no varying attributes
            if not attributes(relation_candidate).intersection(transaction_manager.varying):
                continue
            # Exclude candidates with length 1
            if length == 1:
                continue
            yield SupportRecord(candidate_set, support)
        length += 1
        candidates = _create_next_candidates(relations, length)


def gen_attribute_records(transaction_manager, record, min_support):
    """
    Returns a generator of attribute records and class name.

    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        record -- A support record as a SupportRecord instance.
        min_support -- A minimum support (float).
    """
    attributes = ''
    items = sorted(record.items)
    variable_items = []
    invariable_items = []
    for item in items:
        attributes += item[:2]
        if item[:2] in transaction_manager.non_varying:
            invariable_items.append(item)
        else:
            variable_items.append(item)
    variable_items = frozenset(variable_items)
    invariable_items = frozenset(invariable_items)
    if variable_items != frozenset([]):
        class_name = set()
        if record.support[0] > min_support:
            class_name.add(transaction_manager.classifier[0])
        if record.support[1] > min_support:
            class_name.add(transaction_manager.classifier[1])
        yield AttributeRecord(
            attributes, invariable_items, variable_items, 0, class_name, 0, record.support)


def filter_ordered_statistics(transaction_manager, ordered_statistics, pairs_count, **kwargs):
    """
    Filter AttributeRecord objects that have no contrasting rules.

    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        ordered_statistics -- An AttributeRecord iterable object.
        pair_count -- A dictionary of attributes and their counts

    """
    min_confidence = kwargs.get('min_confidence', 0.0)
    g = {k: v for k, v in pairs_count.items() if v > 1}
    for ordered_statistic in ordered_statistics:
        if ordered_statistic.attributes in g.keys():
            cond_set = ordered_statistic.confidence
            if len(ordered_statistic.class_name) == 1:
                class_index = {cond_set.index(max(cond_set))}
            else:
                class_index = {0, 1}

            global_antecedent_count = cond_set[0]*transaction_manager.num_class_1 + cond_set[1]*transaction_manager.num_class_2
            global_antecedent_support = float(global_antecedent_count) / transaction_manager.num_transaction
            confidence = {}
            for i in class_index:
                if i == 0:
                    temp = ((cond_set[i]*transaction_manager.num_class_1)/transaction_manager.num_transaction) \
                             / global_antecedent_support
                    rule_support = float(cond_set[i]*transaction_manager.num_class_1) \
                             / transaction_manager.num_transaction
                    if temp > min_confidence:
                        confidence[i] = temp
                else:
                    temp = ((cond_set[i] * transaction_manager.num_class_2) / transaction_manager.num_transaction) \
                                 / global_antecedent_support
                    rule_support = float(cond_set[i] * transaction_manager.num_class_1) \
                                   / transaction_manager.num_transaction
                    if temp > min_confidence:
                        confidence[i] = temp
            if confidence:
                yield AttributeRecord(
                    ordered_statistic.attributes,
                    ordered_statistic.invariable_items,
                    ordered_statistic.variable_items,
                    global_antecedent_support,
                    ordered_statistic.class_name,
                    rule_support,
                    confidence)


################################################################################
# API function.
################################################################################
def gen_pairs(transactions, classifier, non_varying, varying, **kwargs):
    """
    Executes SCR-Apriori algorithm and returns a AttributeRecord generator.

    Arguments:
        transactions -- A transaction iterable object
                        (eg. [['A', 'B'], ['B', 'C']]).
        classifier -- The index of the classifier in the data set

    Keyword arguments:
        min_support -- The minimum support of relations (float).
        min_confidence -- The minimum confidence of relations (float).
    """
    # Parse the arguments.

    min_support = kwargs.get('min_support', 0.1)
    min_confidence = kwargs.get('min_confidence', 0.0)

    # Check arguments.
    if min_support <= 0:
        raise ValueError('minimum support must be > 0')

    # For testing.
    _gen_support_records = kwargs.get(
        '_gen_support_records', gen_support_records)
    _gen_attribute_records = kwargs.get(
        '_gen_attribute_records', gen_attribute_records)
    _filter_ordered_statistics = kwargs.get(
        '_filter_ordered_statistics', filter_ordered_statistics)

    # Calculate supports.
    transaction_manager = TransactionManager.create(transactions, non_varying, varying, classifier)
    support_records = _gen_support_records(
        transaction_manager, min_support)

    # Calculate ordered stats.
    support_records, support_records_clone = tee(support_records)
    res = []
    """
    Filling a set containing the count of each attribute
    """
    pairs_count = {}
    for support_record in support_records:
        attribute_records = list(_gen_attribute_records(transaction_manager, support_record, min_support))
        for attribute_record in attribute_records:
            if attribute_record.attributes not in pairs_count.keys():
                pairs_count[attribute_record.attributes] = 1
            else:
                pairs_count[attribute_record.attributes] += 1

    count = 0
    for support_record in support_records_clone:
        filtered_statistics = list(
            _filter_ordered_statistics(
                transaction_manager,
                _gen_attribute_records(transaction_manager, support_record, min_support),
                pairs_count,
                min_confidence=min_confidence,
            )
        )
        if not filtered_statistics:
            continue
        if count == 0:
            res.append(filtered_statistics)
            count += 1
            continue
        if res[count-1][0].attributes == filtered_statistics[0].attributes:
            res[count-1] += filtered_statistics
            continue
        res.append(filtered_statistics)
        count += 1

    res = filter_pairs(res)
    return res


def filter_pairs(list_of_pairs):
    to_remove = []
    for pairs in list_of_pairs:
        if len(pairs) == 1:
            to_remove.append(pairs)
            continue
        if pairs[0].invariable_items != pairs[1].invariable_items:
            to_remove.append(pairs)
        if pairs[0].invariable_items == frozenset():
            if pairs[0].variable_items.intersection(pairs[1].variable_items) == frozenset():
                to_remove.append(pairs)
    for x in to_remove:
        list_of_pairs.remove(x)
    return list_of_pairs


def load_base(location, delimiter):
    data = pd.read_csv(location, delimiter=delimiter, header=None)
    return data


def initialize(data, class_index):
    split_data = data[0].str.split(',', expand=True)
    classifier = list(set(split_data[split_data.columns[class_index]]))
    transactions = []
    for index in range(len(data)):
        transactions.append(data[0][index].split(','))
    return classifier, transactions


def format(x):
    l = []
    for t in x:
        if type(t) == tuple or type(t) == list:
            for e in t:
                l.append(e)
        else:
            l.append(t)
    return frozenset(l)


def attributes(itemset):
    res = set()
    for item in itemset:
        res.add(item[:2])
    return res


def run(url, **kwargs):
    delimiter = kwargs.get('delimiter', ';')
    class_index = kwargs.get('class_index', -1)
    min_support = kwargs.get('min_support', 0.01)
    min_confidence = kwargs.get('min_confidence', 0.01)
    data = load_base(url, delimiter)
    classifier, transactions = initialize(data, class_index)
    results = list(CAR_apriori(transactions, classifier, min_support=min_support, min_confidence=min_confidence))
    return results
