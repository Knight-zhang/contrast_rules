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
sys.path.insert(0, '../util')
import constants


################################################################################
# Data structures.
################################################################################
class TransactionManager(object):
    """
    Transaction managers.
    """

    def __init__(self, transactions, inv, var, classifier):
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
        self.__inv = inv
        self.__var = var

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
        return len(sum_indexes_1), len(sum_indexes_2)

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
    def invariable_attributes(self):
        """
        Returns the set of the classifier
        """
        return self.__inv

    @property
    def variable_attributes(self):
        """
        Returns the set of the classifier
        """
        return self.__var

    @staticmethod
    def create(transactions, inv, var, classifier):
        """
        Create the TransactionManager with a transaction instance.
        If the given instance is a TransactionManager, this returns itself.
        """
        if isinstance(transactions, TransactionManager):
            return transactions
        return TransactionManager(transactions, inv, var, classifier)


# Ignore name errors because these names are namedtuples.
SupportRecord = namedtuple( # pylint: disable=C0103
    'SupportRecord', ('items', 'support'))
RelationRecord = namedtuple( # pylint: disable=C0103
    'SCR_pattern', ('rule_pairs',))
AttributeRecord = namedtuple( # pylint: disable=C0103
    'Rule', ('attributes', 'invariable_items', 'variable_items', 'support',))
OrderedStatistic = namedtuple( # pylint: disable=C0103
    'Rule', ('attributes', 'invariable_items', 'variable_items', 'antecedent_count', 'class_name',
             'rule_count', 'confidence'))


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
            # Exclude candidates with support less than min_support in both classes
            if support[0] < min_support and support[1] < min_support:
                continue
            candidate_set = frozenset(relation_candidate)
            relations.add(candidate_set)
            """# If both supports are greater than min_support
            # We don't return them, but we store them and keep looking
            if support[0] > min_support and support[1] > min_support:
                continue"""
            # Exclude candidates whith no variable attributes
            if not attributes(relation_candidate).intersection(transaction_manager.variable_attributes):
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
        if item[:2] in transaction_manager.invariable_attributes:
            invariable_items.append(item)
        else:
            variable_items.append(item)
    variable_items = frozenset(variable_items)
    invariable_items = frozenset(invariable_items)
    if variable_items != frozenset([]):
        yield AttributeRecord(
            attributes, invariable_items, variable_items, record.support)


def filter_ordered_statistics(transaction_manager, attribute_records, pairs_count, **kwargs):
    """
    Filter AttributeRecord objects that have no contrasting rules.

    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        ordered_statistics -- An AttributeRecord iterable object.
        pair_count -- A dictionary of attributes and their counts

    """
    min_confidence = kwargs.get('min_confidence', 0.5)
    g = {k: v for k, v in pairs_count.items() if v > 1}
    for attribute_record in attribute_records:
        if attribute_record.attributes in g.keys():
            cond_set = attribute_record.support
            class_index = cond_set.index(max(cond_set))
            class_name = transaction_manager.classifier[class_index]
            rule_support = cond_set[class_index]
            global_antecedent_count = cond_set[0] + cond_set[1]
            confidence = float(rule_support) / global_antecedent_count
            if confidence >= min_confidence:
                yield OrderedStatistic(
                    attribute_record.attributes,
                    attribute_record.invariable_items,
                    attribute_record.variable_items,
                    global_antecedent_count,
                    class_name,
                    rule_support,
                    confidence)


################################################################################
# API function.
################################################################################
def generate_contrasting_rules(transactions, classifier, inv, var, min_support, **kwargs):
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

    min_confidence = kwargs.get('min_confidence', 0.5)

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
    transaction_manager = TransactionManager.create(transactions, inv, var, classifier)
    support_records = _gen_support_records(
        transaction_manager, min_support)

    # Calculate ordered stats.
    support_records, support_records_clone = tee(support_records)
    res = {}
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

    #count = 0
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
        if filtered_statistics[0].attributes not in res:
            res[filtered_statistics[0].attributes] = []
        res[filtered_statistics[0].attributes].append(filtered_statistics)
        """if count == 0:
            res.append(filtered_statistics)
            count += 1
            continue
        if res[count-1][0].attributes == filtered_statistics[0].attributes:
            res[count-1] += filtered_statistics
            continue"""
        #res.append(filtered_statistics)
        #count += 1
    res = filter_pairs(res, transaction_manager)
    return res


def filter_pairs(res, transaction_manager):
    list_of_pairs = []
    for val in list(res.values()):
        list_of_pairs.append(list(combinations(val, 2)))
    rules = []
    for group in list_of_pairs:
        temp = set()
        if not group:
            continue
        for pair in group:
            if pair[0][0].class_name == pair[1][0].class_name:
                continue
            if pair[0][0].invariable_items != pair[1][0].invariable_items:
                continue
            if pair[0][0].invariable_items == frozenset():
                if pair[0][0].variable_items.intersection(pair[1][0].variable_items) == frozenset():
                    continue
            temp.add(pair[0][0])
            temp.add(pair[1][0])
        if temp != set():
            rules.append(temp)
    links = {}
    for group in rules:
        for rule1 in group:
            links[rule1] = ''
            for rule2 in group:
                if rule1 != rule2 and rule1.class_name != rule2.class_name \
                        and (rule1.invariable_items == rule2.invariable_items) \
                        and (rule1.invariable_items != frozenset() or rule1.variable_items.intersection(rule2.variable_items) != frozenset()):
                    # tests:
                    # 1. rules are different
                    # 2. classes are different
                    # 3. invariant attributes should have the same values
                    # 4. if no invariant attributes, at least 1 varying attribute should have the same values
                    links[rule1] += str(list(group).index(rule2) + 1) + ','
            links[rule1] = links[rule1][:-1]
    rules = []
    att = list(links.keys())[0].attributes
    for rule in links.keys():
        items = rule.variable_items.union(rule.invariable_items)
        antecedent = tuple(sorted(items))
        # transform antecedent and consequent into sets
        antecedent_set = set(antecedent)
        consequent_str = rule.class_name
        consequent_set = set([consequent_str])
        antecedent_str = ''
        for el in antecedent:
            antecedent_str += el + ','
        antecedent_str = antecedent_str[:-1]
        a_rule = {constants.LHS: antecedent_str, constants.RHS: consequent_str,
                  constants.LHS_SET: antecedent_set, constants.RHS_SET: consequent_set,
                  constants.LHS_SUPP_COUNT: rule.antecedent_count,
                  constants.RULE_SUPP_COUNT: rule.rule_count,
                  constants.LHS_SUPP: float(rule.antecedent_count)
                                      / transaction_manager.num_transaction,
                  constants.RULE_SUPP: float(
                      rule.rule_count) / transaction_manager.num_transaction,
                  constants.RULE_CONF: rule.confidence,
                  constants.LINKS: links[rule]}
        if rule.attributes != att:
            att = rule.attributes
            rules.append(set())
        rules.append(a_rule)
    return rules


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

