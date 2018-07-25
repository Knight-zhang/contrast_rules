import itertools
import sys

sys.path.insert(0, '../util')
import constants


class UtilClass(object):

    @staticmethod
    def min_for_dic_value(dic_values_array, possible_keys_array):
        """
        For a given array of dictionaries of the same structure return a dictionary that has
        minimum values of all keys
        :param dic_values_array:
        :param possible_keys_array: keys of dictionaries
        :return:
        """
        # initialize with empty array
        all_dic = {}
        for key in possible_keys_array:
            all_dic[key] = []

        # loop thorough dictionaries to gather all values for one key into array
        for dic in dic_values_array:
            for key in possible_keys_array:
                all_dic[key].append(dic[key])

        # now min_dic for every key has its minimum value
        min_dic = {}
        for key in possible_keys_array:
            min_dic[key] = min(all_dic[key])

        return min_dic


class FPNode(object):
    """
    A node in the FP tree.
    """

    def __init__(self, value, count, current_class, possible_class_values, parent):
        """
        Create the node.
        """
        self.value = value
        self.count = {}
        # TODO
        # count can be a value or a dictionary ==> replace it to be a dictionary and then we don't need current class
        if type(count) is dict:
            # this is a dictionary, copy values
            for key in count:
                self.count[key] = count[key]
        else:
            for class_val in possible_class_values:
                self.count[class_val] = 0
            if current_class is not None:
                self.count[current_class] = count
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

    def add_child(self, value, current_class, possible_class_values):
        """
        Add a node as a child node.
        """
        child = FPNode(value, 1, current_class, possible_class_values, self)
        self.children.append(child)
        return child


class FPTree(object):
    """
    A frequent pattern tree.
    """

    def __init__(self, transactions, threshold, possible_class_values, root_value, root_count):
        """
        Initialize the tree.
        """
        self.frequent = self.find_frequent_items(transactions, possible_class_values, threshold)
        self.headers = self.build_header_table(self.frequent)
        self.possible_class_values = possible_class_values
        self.root = self.build_fptree(
            transactions, root_value, root_count,
            self.frequent, self.headers, possible_class_values)

    @staticmethod
    def find_frequent_items(transactions, possible_class_values, threshold):
        """
        Create a dictionary of items with occurrences above the threshold.
        """
        items = {}

        for transaction in transactions:
            # first find the class value
            current_class = None
            for class_val in possible_class_values:
                if class_val in transaction:
                    current_class = class_val
                    break
            if current_class is None:
                raise Exception("Transaction has no class value: {}".format(transaction))

            for item in transaction:
                if item == current_class:
                    continue
                if item in items:
                    items[item][current_class] += 1
                else:
                    item_info = {}
                    for class_val in possible_class_values:
                        if class_val == current_class:
                            item_info[class_val] = 1
                        else:
                            item_info[class_val] = 0
                    items[item] = item_info

        for key in list(items.keys()):
            # now delete those, that are frequent on none of the classes
            item_info = items[key]
            not_frequent = True
            for class_val in possible_class_values:
                if item_info[class_val] >= threshold:
                    not_frequent = False
                    break
            if not_frequent:
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

    def build_fptree(self, transactions, root_value, root_count,
                     frequent, headers, possible_class_values):
        """
        Build the FP tree and return the root node.
        """
        root = FPNode(root_value, root_count, None, possible_class_values, None)

        for transaction in transactions:
            # initialize class object
            current_class = None
            for class_val in possible_class_values:
                if class_val in transaction:
                    # current_class is found
                    current_class = class_val
                    # remove class element from items
                    # transaction.remove(current_class)
                    break
            if current_class is None:
                raise Exception("Transaction has no class value: {}".format(transaction))

            sorted_items = [x for x in transaction if x in frequent.keys()]
            if len(sorted_items) > 0:
                sorted_items.sort(key=lambda x: max(frequent[x].values()), reverse=True)
                self.insert_tree(sorted_items, root, headers, possible_class_values, current_class)

        if root_count is None:
            # now update root class values if it is an original tree
            for a_child in root.children:
                for class_val in possible_class_values:
                    root.count[class_val] += a_child.count[class_val]

        return root

    def insert_tree(self, items, node, headers, possible_class_values, current_class):
        """
        Recursively grow FP tree.
        """
        first = items[0]
        child = node.get_child(first)
        if child is not None:
            child.count[current_class] += 1
        else:
            # Add new child.
            child = node.add_child(first, current_class, possible_class_values)

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
            self.insert_tree(remaining_items, child, headers, possible_class_values, current_class)

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
            # add the root first, which is itself a pattern
            new_patterns = {tuple([suffix]): self.root.count}
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
                    UtilClass.min_for_dic_value([self.frequent[x] for x in subset], self.possible_class_values)

        return patterns

    def mine_sub_trees(self, threshold):
        """
        Generate subtrees and mine them for patterns.
        """
        patterns = {}
        mining_order = sorted(self.frequent.keys(),
                              key=lambda x: max(self.frequent[x].values()))

        # Get items in tree in reverse order of occurrences.
        for item in mining_order:
            item_frequency = self.frequent[item]
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

                for class_val in self.possible_class_values:
                    path_with_class = path[:]
                    path_with_class.append(class_val)
                    for i in range(frequency[class_val]):
                        conditional_tree_input.append(path_with_class)

            # Now we have the input for a subtree,
            # so construct it and grab the patterns.
            subtree = FPTree(conditional_tree_input, threshold, self.possible_class_values,
                             item, item_frequency)
            # print(subtree.to_string())
            subtree_patterns = subtree.mine_patterns(threshold)

            # Insert subtree patterns into main patterns dictionary.
            for pattern in subtree_patterns.keys():
                if pattern in patterns:
                    # add the values for corresponding classes
                    for class_val in self.possible_class_values:
                        patterns[pattern][class_val] += subtree_patterns[pattern][class_val]
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


def find_frequent_patterns(transactions, support_threshold, possible_class_values):
    """
    Given a set of transactions, find the patterns in it
    over the specified support threshold.
    """
    tree = FPTree(transactions, support_threshold, possible_class_values, None, None)
    # print(tree.to_string())
    return tree.mine_patterns(support_threshold)


def generate_classification_rules(patterns, confidence_threshold, num_of_transactions, class_values):
    """
    Given a set of frequent itemsets, return a dict
    of association rules in the form
    {(left): ((right), confidence)}
    right contains only one item (is and itemset of size 1)
    """
    rules = []
    for itemset in patterns.keys():
        # get most frequent class value and generate a rule for it
        frequency = patterns[itemset]
        chosen_class = max(frequency, key=frequency.get)
        rule_support_count = frequency[chosen_class]
        # calculate confidence of the rule
        tot_support_count = 0
        for class_key in frequency:
            tot_support_count += frequency[class_key]
        confidence = float(rule_support_count) / tot_support_count
        if confidence >= confidence_threshold:
            # form antecedent and consequent as sets and strings
            antecedent = tuple(sorted(itemset))
            antecedent_set = set(antecedent)
            antecedent_str = ''
            for el in antecedent:
                antecedent_str += el + ','
            antecedent_str = antecedent_str[:-1]
            consequent_str = chosen_class
            consequent_set = set([consequent_str])

            a_rule = {constants.LHS: antecedent_str, constants.RHS: consequent_str,
                      constants.LHS_SET: antecedent_set, constants.RHS_SET: consequent_set,
                      constants.LHS_SUPP_COUNT: tot_support_count, constants.RULE_SUPP_COUNT: rule_support_count,
                      constants.LHS_SUPP: (float(tot_support_count) / num_of_transactions),
                      constants.RULE_SUPP: (float(rule_support_count) / num_of_transactions),
                      constants.RULE_CONF: confidence, constants.LINKS: ''}
            rules.append(a_rule)

    return rules
