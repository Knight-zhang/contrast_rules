import itertools
import sys

sys.path.insert(0, '../util')
import constants


class FPNode(object):
    """
    A node in the FP tree.
    """

    def __init__(self, value, count, parent):
        """
        Create the node.
        """
        self.value = value
        self.count = count
        self.parent = parent
        self.link = None
        self.children = []

    def has_child(self, value):
        """
        Check if node has a particular child node.
        """
        for node in self.children:
            if node.value == value:
                return True

        return False

    def get_child(self, value):
        """
        Return a child node with a particular value.
        """
        for node in self.children:
            if node.value == value:
                return node

        return None

    def add_child(self, value):
        """
        Add a node as a child node.
        """
        child = FPNode(value, 1, self)
        self.children.append(child)
        return child


class FPTree(object):
    """
    A frequent pattern tree.
    """

    def __init__(self, transactions, threshold, root_value, root_count):
        """
        Initialize the tree.
        """
        self.frequent = self.find_frequent_items(transactions, threshold)
        self.headers = self.build_header_table(self.frequent)
        self.root = self.build_fptree(
            transactions, root_value,
            root_count, self.frequent, self.headers)

    @staticmethod
    def find_frequent_items(transactions, threshold):
        """
        Create a dictionary of items with occurrences above the threshold.
        """
        items = {}

        for transaction in transactions:
            for item in transaction:
                if item in items:
                    items[item] += 1
                else:
                    items[item] = 1

        for key in list(items.keys()):
            if items[key] < threshold:
                del items[key]

        return items

    @staticmethod
    def build_header_table(frequent):
        """
        Build the header table.
        """
        headers = {}
        for key in frequent.keys():
            headers[key] = None

        return headers

    def build_fptree(self, transactions, root_value,
                     root_count, frequent, headers):
        """
        Build the FP tree and return the root node.
        """
        root = FPNode(root_value, root_count, None)

        for transaction in transactions:
            sorted_items = [x for x in transaction if x in frequent]
            sorted_items.sort(key=lambda x: frequent[x], reverse=True)
            if len(sorted_items) > 0:
                self.insert_tree(sorted_items, root, headers)

        return root

    def insert_tree(self, items, node, headers):
        """
        Recursively grow FP tree.
        """
        first = items[0]
        child = node.get_child(first)
        if child is not None:
            child.count += 1
        else:
            # Add new child.
            child = node.add_child(first)

            # Link it to header structure.
            if headers[first] is None:
                headers[first] = child
            else:
                current = headers[first]
                while current.link is not None:
                    current = current.link
                current.link = child

        # Call function recursively.
        remaining_items = items[1:]
        if len(remaining_items) > 0:
            self.insert_tree(remaining_items, child, headers)

    def tree_has_single_path(self, node):
        """
        If there is a single path in the tree,
        return True, else return False.
        """
        num_children = len(node.children)
        if num_children > 1:
            return False
        elif num_children == 0:
            return True
        else:
            return True and self.tree_has_single_path(node.children[0])

    def mine_patterns(self, threshold):
        """
        Mine the constructed FP tree for frequent patterns.
        """
        if self.tree_has_single_path(self.root):
            return self.generate_pattern_list()
        else:
            return self.zip_patterns(self.mine_sub_trees(threshold))

    def zip_patterns(self, patterns):
        """
        Append suffix to patterns in dictionary if
        we are in a conditional FP tree.
        """
        suffix = self.root.value

        if suffix is not None:
            # We are in a conditional tree.
            new_patterns = {}
            # add the root first
            new_patterns[tuple([suffix])] = self.root.count
            for key in patterns.keys():
                new_patterns[tuple(sorted(list(key) + [suffix]))] = patterns[key]

            return new_patterns

        return patterns

    def generate_pattern_list(self):
        """
        Generate a list of patterns with support counts.
        """
        patterns = {}
        items = self.frequent.keys()

        # If we are in a conditional tree,
        # the suffix is a pattern on its own.
        if self.root.value is None:
            suffix_value = []
        else:
            suffix_value = [self.root.value]
            patterns[tuple(suffix_value)] = self.root.count

        for i in range(1, len(items) + 1):
            for subset in itertools.combinations(items, i):
                pattern = tuple(sorted(list(subset) + suffix_value))
                patterns[pattern] = \
                    min([self.frequent[x] for x in subset])

        return patterns

    def mine_sub_trees(self, threshold):
        """
        Generate subtrees and mine them for patterns.
        """
        patterns = {}
        mining_order = sorted(self.frequent.keys(),
                              key=lambda x: self.frequent[x])

        # Get items in tree in reverse order of occurrences.
        for item in mining_order:
            suffixes = []
            conditional_tree_input = []
            node = self.headers[item]

            # Follow node links to get a list of
            # all occurrences of a certain item.
            while node is not None:
                suffixes.append(node)
                node = node.link

            # For each occurrence of the item, 
            # trace the path back to the root node.
            for suffix in suffixes:
                frequency = suffix.count
                path = []
                parent = suffix.parent

                while parent.parent is not None:
                    path.append(parent.value)
                    parent = parent.parent

                for i in range(frequency):
                    conditional_tree_input.append(path)

            # Now we have the input for a subtree,
            # so construct it and grab the patterns.
            subtree = FPTree(conditional_tree_input, threshold,
                             item, self.frequent[item])
            subtree_patterns = subtree.mine_patterns(threshold)

            # Insert subtree patterns into main patterns dictionary.
            for pattern in subtree_patterns.keys():
                if pattern in patterns:
                    patterns[pattern] += subtree_patterns[pattern]
                else:
                    patterns[pattern] = subtree_patterns[pattern]

        return patterns

    def to_string(self):
        """
        Get string representation of the tree
        :return:
        """
        tree_structure_str = self.node_to_string(self.root, 0, is_add_children=True).rstrip()
        return tree_structure_str

    def node_to_string(self, node, tab_count=0, is_add_children=False):
        """
        Get String representation of the node
        :param node:
        :param tab_count:
        :param is_add_children:
        :return:
        """
        tabs_str = ''
        for i in range(0, tab_count):
            tabs_str += '\t'

        node_str = tabs_str + str(node.value) + ': ' + str(node.count)

        children_str = ''
        if is_add_children:
            for child_node in node.children:
                children_str += '\n\t' + tabs_str + self.node_to_string(child_node, tab_count+1, True)

        return node_str + children_str


def find_frequent_patterns(transactions, support_threshold):
    """
    Given a set of transactions, find the patterns in it
    over the specified support threshold.
    """
    tree = FPTree(transactions, support_threshold, None, None)
    return tree.mine_patterns(support_threshold)


def generate_association_rules(patterns, confidence_threshold, num_of_transactions):
    """
    Given a set of frequent itemsets, return a dict
    of association rules in the form
    {(left): ((right), confidence)}
    """
    rules = []
    for itemset in patterns.keys():
        upper_support = patterns[itemset]

        for i in range(1, len(itemset)):
            for antecedent in itertools.combinations(itemset, i):
                antecedent = tuple(sorted(antecedent))
                # transform antecedent and consequent into sets
                antecedent_set = set(antecedent)
                consequent = tuple(sorted(set(itemset) - antecedent_set))
                consequent_set = set(consequent)

                lower_support = patterns[antecedent]
                confidence = float(upper_support) / lower_support

                if confidence >= confidence_threshold:
                    # form antecedent and censequent in string format (the tuples are already sorted)
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
                              constants.LHS_SUPP_COUNT: lower_support, constants.RULE_SUPP_COUNT: upper_support,
                              constants.LHS_SUPP: (float(lower_support) / num_of_transactions),
                              constants.RULE_SUPP: (float(upper_support) / num_of_transactions),
                              constants.RULE_CONF: confidence, constants.LINKS: ''}
                    rules.append(a_rule)

    return rules


def generate_association_rules_with_one_item_consequent(patterns, confidence_threshold, num_of_transactions):
    """
    Given a set of frequent itemsets, return a dict
    of association rules in the form
    {(left): ((right), confidence)}
    right contains only one item (is and itemset of size 1)
    """
    rules = []
    for itemset in patterns.keys():
        if len(itemset) > 1:
            # we can't generate a rule from an itemset containing only 1 item, at least 2 are required
            upper_support = patterns[itemset]

            for consequent_el in itemset:
                # consequent_el has only one elements, so it is already sorted
                consequent = tuple([consequent_el])
                consequent_set = set(consequent)
                antecedent = tuple(sorted(set(itemset) - consequent_set))
                antecedent_set = set(antecedent)

                lower_support = patterns[antecedent]
                confidence = float(upper_support) / lower_support

                if confidence >= confidence_threshold:
                    # form antecedent and censequent in string format (the tuples are already sorted)
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
                              constants.LHS_SUPP_COUNT: lower_support, constants.RULE_SUPP_COUNT: upper_support,
                              constants.LHS_SUPP: (float(lower_support) / num_of_transactions),
                              constants.RULE_SUPP: (float(upper_support) / num_of_transactions),
                              constants.RULE_CONF: confidence, constants.LINKS: ''}
                    rules.append(a_rule)
    return rules


def generate_classification_rules(patterns, confidence_threshold, num_of_transactions, class_values):
    """
    Given a set of frequent itemsets, return a dict
    of association rules in the form
    {(left): ((right), confidence)}
    right contains only one item (is and itemset of size 1)
    """
    rules = []
    for itemset in patterns.keys():
        if len(itemset) > 1:
            # we can't generate a rule from an itemset containing only 1 item, at least 2 are required
            upper_support = patterns[itemset]

            # only classification rules are required; that is only those itemsets should be considered,
            # that have one of class values inside
            for consequent_el in class_values:
                if consequent_el in itemset:
                    # consequent_el has only one elements, so it is already sorted
                    consequent = tuple([consequent_el])
                    consequent_set = set(consequent)
                    antecedent = tuple(sorted(set(itemset) - consequent_set))
                    antecedent_set = set(antecedent)

                    lower_support = patterns[antecedent]
                    confidence = float(upper_support) / lower_support

                    if confidence >= confidence_threshold:
                        # form antecedent and censequent in string format (the tuples are already sorted)
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
                                  constants.LHS_SUPP_COUNT: lower_support, constants.RULE_SUPP_COUNT: upper_support,
                                  constants.LHS_SUPP: (float(lower_support) / num_of_transactions),
                                  constants.RULE_SUPP: (float(upper_support) / num_of_transactions),
                                  constants.RULE_CONF: confidence, constants.LINKS: ''}
                        rules.append(a_rule)
                    # class value was found, no other class values can be in the itemset ==> bread the loop
                    break
    return rules
