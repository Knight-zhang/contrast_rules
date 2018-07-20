import copy
import itertools
import operator
import sys

sys.path.insert(0, '../util')
import constants

CHOSEN_CLASS = 'chosen_class'
RULE_CONF = 'rule_conf'
INV = 'inv'
VAR = 'var'
CLASS_OBJECT = 'class_object'
INV_VALUES = 'inv_values'
VAR_VALUES = 'var_values'
CLASS = 'class'

FREQUENT_ON_ALL_CLASSES = 1
FREQUENT_ON_SOME_CLASSES = 0
FREQUENT_ON_NONE_CLASSES = -1


class FPNode(object):
    """
    A node in the FP tree.
    """

    def __init__(self, value, classes, count_on_class, parent):
        """
        Create the node.
        """
        self.value = value
        # initialize count: set 0 for all values, then initialize with values from count_on_class
        self.count = {}
        for class_val in classes:
            self.count[class_val] = 0
        if count_on_class is not None:
            for class_val in count_on_class:
                self.count[class_val] = count_on_class[class_val]
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

    def add_child(self, value, class_val, classes):
        """
        Add a node as a child node.
        """
        count_on_classes = {class_val: 1}
        child = FPNode(value, classes, count_on_classes, self)
        self.children.append(child)
        return child


class SCRRuleitem(object):

    def __init__(self, inv_values, var_values, class_object):
        # self.list_of_inv = list_of_inv
        # self.list_of_var = list_of_var
        self.inv_values = inv_values
        self.var_values = var_values
        self.class_object = class_object
        self.chosen_class = None
        self.rule_conf = None
        self.tot_supp = None

    def to_string(self):
        return str(self.class_object) + '\tchosen_class=' \
               + str(self.chosen_class) + '\trule_conf=' + str(self.rule_conf)

    def get_frequency_on_classes(self, support_threshold):
        """
        Calculate if SCR-ruleitem is frequent on some/all classes
        :return: -1 - frequent on none of classes
                  0 - frequent on some classes
                  1 - frequent on all classes
        """
        num_of_frequent = 0
        for class_val in self.class_object:
            if self.class_object[class_val] >= support_threshold:
                num_of_frequent += 1
        if num_of_frequent == len(self.class_object):
            # frequent on all classes
            return 1
        elif num_of_frequent > 0:
            # frequent on at least one class
            return 0
        else:
            # not frequent at all
            return -1


class FPTree(object):
    """
    A frequent pattern tree.
    """

    def __init__(self, transactions, transactions_info):
        """
        Initialize the tree.
        """
        # self.frequent = self.find_frequent_items(transactions, threshold)
        self.transactions_info = copy.deepcopy(transactions_info)
        self.headers = {}
        self.sorting_order_per_attribute = []
        self.sorting_order_per_value = []
        self.build_header_table_and_sorting_orders()
        self.scr_ruleitems = None
        self.scr_ruleitems_info = None

        self.root = self.build_fptree(transactions, self.headers)
        # update class count for root node: set it as sum of counts of its children
        for child in self.root.children:
            for class_val in transactions_info["class"]:
                self.root.count[class_val] += child.count[class_val]

    def build_header_table_and_sorting_orders(self):
        headers = {}
        sorting_order_per_attribute = []
        sorting_order_per_value = []

        # collect invariant attributes
        order_of_inv_keys = self.transactions_info["inv"]["order"]
        for key in order_of_inv_keys:
            sorting_order_per_attribute.append(key)
            header = {}
            for attribute_value in self.transactions_info["inv"][key]:
                header[attribute_value] = None
                sorting_order_per_value.append(attribute_value)
            headers[key] = header

        # collect varying attributes
        order_of_var_keys = self.transactions_info["var"]["order"]
        for key in order_of_var_keys:
            sorting_order_per_attribute.append(key)
            header = {}
            for attribute_value in self.transactions_info["var"][key]:
                header[attribute_value] = None
                sorting_order_per_value.append(attribute_value)
            headers[key] = header

        self.headers = headers
        self.sorting_order_per_attribute = sorting_order_per_attribute

        for class_val in self.transactions_info["class"]:
            sorting_order_per_value.append(class_val)
        self.sorting_order_per_value = sorting_order_per_value

    def build_fptree(self, transactions, headers):
        """
        Build the FP tree and return the root node.
        """
        root = FPNode(None, self.transactions_info["class"], None, None)

        for transaction in transactions:
            sorted_items = [x for x in transaction]
            #sorted_items.sort(key=lambda x: frequent[x], reverse=True)
            # sort according to self.sorting_order
            sorted_items = sorted(sorted_items[:], key=lambda x: self.sorting_order_per_value.index(x))
            if len(sorted_items) > 0:
                self.insert_tree(sorted_items, root, headers)

        return root

    def insert_tree(self, items, node, headers):
        """
        Recursively grow FP tree.
        """
        first = items[0]
        # class attribute is always the last one
        class_val = items[-1]
        child = node.get_child(first)
        if child is not None:
            # last attribute is always a class attribute ==> use it to update relative count info
            child.count[class_val] += 1
        else:
            # Add new child.
            child = node.add_child(first, class_val, self.transactions_info["class"])

            # Link it to header structure.
            # Find the position of the required header
            for header_key in headers.keys():
                if first in headers[header_key]:
                    # we are here
                    header = headers[header_key]
                    if header[first] is None:
                        header[first] = child
                    else:
                        current = header[first]
                        while current.link is not None:
                            current = current.link
                        current.link = child
                    break

        # Call function recursively.
        # exclude the last attribute that is the attribute of class
        remaining_items = items[1:]
        if len(remaining_items) > 1:
            self.insert_tree(remaining_items, child, headers)

    def mine_patterns(self, support_threshold, confidence_threshold, original_transactions_info, tot_records_num, is_verbose=False, not_main_tree=False,
                      list_of_patterns=None):
        if list_of_patterns is None:
            list_of_patterns = []

        inverse_order_of_attributes = list(reversed(self.sorting_order_per_attribute))
        # now construct reduced pf-trees
        for i in range(0, len(inverse_order_of_attributes)):
            current_att = inverse_order_of_attributes[i]
            # check if current item is invariant
            # if yes, stop building new trees
            if (current_att in self.transactions_info["var"]) or not_main_tree:
                # build new tree
                if i == len(inverse_order_of_attributes) - 1:
                    next_att = None
                    rest_of_attributes = []
                else:
                    next_att = inverse_order_of_attributes[i + 1]
                    rest_of_attributes = inverse_order_of_attributes[i+2:]
                if i > 0:
                    previous_attributes = inverse_order_of_attributes[0:i]
                else:
                    previous_attributes = []
                if is_verbose:
                    print(str(i) + ": Subtree construction")

                subtree = self.get_subtree(previous_attributes, current_att, next_att, rest_of_attributes)
                                           # ,self.transactions_info)
                subtree.init_scr_ruleitems(original_transactions_info)
                subtree.init_scr_rules()
                # subtree.get_scr_patterns(support_threshold, confidence_threshold)
                if is_verbose:
                    print str(i) + " done"
                    print "-------------------------------"
                    print subtree.to_string(False, is_add_children=False)

                patterns = subtree.get_scr_patterns_v2(support_threshold, confidence_threshold, tot_records_num)
                if len(patterns) > 0:
                    list_of_patterns.append(patterns)
                #for pattern in patterns:
                #    list_of_patterns.append(pattern)
                if is_verbose:
                    print "SCR-patterns"
                    print self.scr_patterns_to_string(patterns)

                pruned_num, left_classes = subtree.prune_tree(support_threshold, original_transactions_info, is_verbose)
                if is_verbose:
                    if pruned_num > 0:
                        print('--Pruned tree--')
                        print subtree.to_string(False)
                # now print the formed patterns
                # patterns is an array of arrays, each sub-array consists of scr_ruleitems forming scr_pattern
                if len(subtree.scr_ruleitems_info[VAR]) == 1 and '01' in subtree.scr_ruleitems_info[VAR]\
                        and len(subtree.scr_ruleitems_info[INV]) == 1 and '07' in subtree.scr_ruleitems_info[INV]:
                    pass
                if left_classes > 0:
                    subtree.mine_patterns(support_threshold, confidence_threshold, original_transactions_info,
                                          tot_records_num, is_verbose, True, list_of_patterns)
            else:
                # only invariant attributes left, no need to build new trees
                if is_verbose:
                    print "====================== Finished iteration ======================="
                break
        return list_of_patterns

    @staticmethod
    def check_frequency(scr_ruleitem, support_threshold):
        num_of_frequent = 0
        tot_num = len(scr_ruleitem.class_object)
        for class_key in scr_ruleitem.class_object:
            if scr_ruleitem.class_object[class_key] >= support_threshold:
                num_of_frequent += 1
        if num_of_frequent == tot_num:
            return FREQUENT_ON_ALL_CLASSES
        if num_of_frequent == 0:
            return FREQUENT_ON_NONE_CLASSES
        return FREQUENT_ON_SOME_CLASSES

    @staticmethod
    def get_frequent_contrast_pair(current_key, scr_ruleitem, scr_ruleitems_object, support_threshold):
        # init the result variable
        result = None

        # get the first frequent class for this scr_ruleitem
        frequent_class = None
        for key in scr_ruleitem.class_object:
            if scr_ruleitem.class_object[key] >= support_threshold:
                frequent_class = key
                break
        # now do pairwise analysis:
        # we need a scr_ruleitem with the same values of varying attributes and frequent on another class
        for key in scr_ruleitems_object:
            # don't compare with itself
            if key == current_key:
                continue
            scr_ruleitem_2 = scr_ruleitems_object[key]
            # check if inv attributes have the same values
            is_inv_same = FPTree.is_all_att_same(scr_ruleitem.inv_values, scr_ruleitem_2.inv_values)
            # check if scr_ruleitem_2 is frequent on another class
            is_frequent_2 = False
            for class_key in scr_ruleitem_2.class_object:
                if class_key == frequent_class:
                    continue
                if scr_ruleitem_2.class_object[class_key] >= support_threshold:
                    is_frequent_2 = True
                    break
            if is_frequent_2 and is_inv_same:
                result = key
                break
        return result

    def prune_tree(self, support_threshold, original_transactions_info, is_verbose=False):
        to_delete_branches = []
        num_of_var = len(self.scr_ruleitems_info[VAR])
        for key in self.scr_ruleitems:
            scr_ruleitem = self.scr_ruleitems[key]
            # check if it is frequent on all classes
            frequency_val = self.check_frequency(scr_ruleitem, support_threshold)
            if frequency_val == FREQUENT_ON_ALL_CLASSES:
                # keep this element
                continue
            elif frequency_val == FREQUENT_ON_NONE_CLASSES:
                # mark for deleting
                to_delete_branches.append(key)
            else:
                # check if has to be deleted according to attributes values
                # idea:
                # if all attributes inv ==> delete
                # no                    ==> check if constrast pair is frequent
                if num_of_var == 0:
                    # all attributes are varying ==> delete this branch
                    to_delete_branches.append(key)
                else:
                    # try to search for a contast pair
                    contrast_pair = self.get_frequent_contrast_pair(key, scr_ruleitem, self.scr_ruleitems, support_threshold)
                    if contrast_pair is None:
                        # nothing was found ==> mark this key for deleting
                        to_delete_branches.append(key)

        # generate to_delete_class_values: combination of original classes with to_delete_branches
        to_delete_class_values = []
        for el in to_delete_branches:
            for class_val in original_transactions_info[CLASS]:
                to_delete_class_values.append('{},{}'.format(el, class_val))
        if is_verbose:
            print('Prunning: marked for prunning: {}'.format(to_delete_branches))
            print('Prunning: classes for prunning: {}'.format(to_delete_class_values))

        if len(to_delete_branches) > 0:
            new_class_info_array = []
            # do the actual pruning
            # delete from self.transactions_info['class']
            for class_info_key in self.transactions_info[CLASS]:
                if class_info_key not in to_delete_class_values:
                    new_class_info_array.append(class_info_key)
            # update value of self.transactions_info['class']
            self.transactions_info['class'] = new_class_info_array
            # now traverse the tree
            FPTree.prune_node(self.root, to_delete_class_values)
        return len(to_delete_class_values), len(self.root.count)

    @staticmethod
    def prune_node(node, to_delete_class_values):
        # do the prunning
        # delete from count
        for el in to_delete_class_values:
            if el in node.count:
                del node.count[el]
        # now process all children
        for a_child in node.children:
            FPTree.prune_node(a_child, to_delete_class_values)


    @staticmethod
    def scr_patterns_to_string(patterns):
        # patterns is a list of scr_patterns
        # each pattern is a list os scr_ruleitems with keys

        result = ''
        for i in range(0, len(patterns)):
            # i - is the number of the pattern
            result += '{}--'.format(i)
            a_pattern = patterns[i]
            for j in range(0, len(a_pattern)):
                a_rule_item = a_pattern[j]
                for key in a_rule_item:
                    scr_ruleitem = a_rule_item[key]
                    result += '\t{}: {}\n'.format(key, scr_ruleitem.to_string())
        if len(result) == 0:
            result = '\tNone'
        return result

    def init_scr_rules(self):
        for key in self.scr_ruleitems:
            scr_ruleitem = self.scr_ruleitems[key]
            # set as chosen class the class with max elements
            chosen_class = max(scr_ruleitem.class_object.iteritems(),
                                            key=operator.itemgetter(1))[0]
            scr_ruleitem.chosen_class = chosen_class
            chosen_supp = scr_ruleitem.class_object[chosen_class]
            tot_supp = 0
            for class_key in scr_ruleitem.class_object:
                tot_supp += scr_ruleitem.class_object[class_key]
            scr_ruleitem.tot_supp = tot_supp
            if chosen_supp == 0:
                scr_ruleitem.rule_conf = 0
            else:
                scr_ruleitem.rule_conf = chosen_supp / float(tot_supp)

    def get_scr_patterns(self, support_threshold, confidence_threshold, tot_records_num):

        result = []
        # num of varying attributes that form scr-ruleitems on this stage
        num_var = len(self.scr_ruleitems_info[VAR])
        # num of invariant
        num_inv = len(self.scr_ruleitems_info[INV])
        # tot num of attributes that form scr-ruleitmes on this stage
        num_tot = num_var + num_inv
        if num_var == 0 or num_tot < 2:
            # no scr ruleitems can be generated on this step, return an empty array
            pass
        else:
            # do processing to get the patterns
            # gather all keys into an array to do pairwise comparison
            keys_arr = []
            for key in self.scr_ruleitems:
                keys_arr.append(key)
            # now do the pairwise comparison
            for i in range(0, len(keys_arr)):
                key_1 = keys_arr[i]
                scr_ruleitem_1 = self.scr_ruleitems[key_1]
                # check confidence and support
                chosen_class_1 = scr_ruleitem_1.chosen_class
                supp_1 = scr_ruleitem_1.class_object[chosen_class_1]
                conf_1 = scr_ruleitem_1.rule_conf
                pairs_arr = [{
                    constants.LHS: key_1, constants.RHS: chosen_class_1,
                    constants.LHS_SUPP_COUNT: scr_ruleitem_1.tot_supp,
                    constants.LHS_SUPP: (float(scr_ruleitem_1.tot_supp) / tot_records_num),
                    constants.RULE_SUPP_COUNT: supp_1,
                    constants.RULE_SUPP: (float(supp_1) / tot_records_num),
                    constants.RULE_CONF: conf_1
                }]
                # pairs_arr.append({key_1: scr_ruleitem_1})
                if supp_1 >= support_threshold and conf_1 >= confidence_threshold:
                    for j in range(0, len(keys_arr)):
                        if i == j:
                            continue
                        key_2 = keys_arr[j]
                        scr_ruleitem_2 = self.scr_ruleitems[key_2]
                        # get chosen_class, supp and conf
                        chosen_class_2 = scr_ruleitem_2.chosen_class
                        supp_2 = scr_ruleitem_2.class_object[chosen_class_2]
                        conf_2 = scr_ruleitem_2.rule_conf
                        # check if classes are different and supp and conf are above thresholds
                        if chosen_class_1 != chosen_class_2 and supp_2 >= support_threshold and conf_2 >= confidence_threshold:
                            # perform different check
                            # 1. invariant attributes have the same values
                            # 2. at least 1 of varying attributes has different values between 2 rules
                            # 3. if num_inv == 0 ==> at least 1 varying should have the same value
                            is_inv_same = self.is_all_att_same(scr_ruleitem_1.inv_values, scr_ruleitem_2.inv_values)
                            is_one_var_diff = self.is_at_least_one_att_diff(scr_ruleitem_1.var_values,
                                                                            scr_ruleitem_2.var_values)
                            is_one_var_same = self.is_at_least_one_att_same(scr_ruleitem_1.var_values,
                                                                            scr_ruleitem_2.var_values)
                            if is_inv_same and is_one_var_diff and ((num_inv > 0) or is_one_var_same):
                                # ok, scr_ruleitem_1 and scr_ruleitem_2 form a pair
                                pairs_arr.append({
                                    constants.LHS: key_2, constants.RHS: chosen_class_2,
                                    constants.LHS_SUPP_COUNT: scr_ruleitem_2.tot_supp,
                                    constants.LHS_SUPP: (float(scr_ruleitem_2.tot_supp) / tot_records_num),
                                    constants.RULE_SUPP_COUNT: supp_2,
                                    constants.RULE_SUPP: (float(supp_2) / tot_records_num),
                                    constants.RULE_CONF: conf_2
                                })
                if len(pairs_arr) > 1:
                    # there was a match, add pairs_arr to the result
                    result.append(pairs_arr)
        return result

    def get_scr_patterns_v2(self, support_threshold, confidence_threshold, tot_records_num):

        result = []
        # num of varying attributes that form scr-ruleitems on this stage
        num_var = len(self.scr_ruleitems_info[VAR])
        # num of invariant
        num_inv = len(self.scr_ruleitems_info[INV])
        # tot num of attributes that form scr-ruleitmes on this stage
        num_tot = num_var + num_inv
        if num_var == 0 or num_tot < 2:
            # no scr ruleitems can be generated on this step, return an empty array
            pass
        else:
            # do processing to get the patterns
            # gather all keys into an array to do pairwise comparison
            keys_arr = []
            ref_object = {}
            rule_object = {}
            for key in self.scr_ruleitems:
                keys_arr.append(key)
                ref_object[key] = []

            # now do the pairwise comparison
            for i in range(0, len(keys_arr)):
                key_1 = keys_arr[i]
                scr_ruleitem_1 = self.scr_ruleitems[key_1]
                # check confidence and support
                chosen_class_1 = scr_ruleitem_1.chosen_class
                supp_1 = scr_ruleitem_1.class_object[chosen_class_1]
                conf_1 = scr_ruleitem_1.rule_conf
                # pairs_arr.append({key_1: scr_ruleitem_1})
                if supp_1 >= support_threshold and conf_1 >= confidence_threshold:
                    for j in range(i + 1, len(keys_arr)):
                        key_2 = keys_arr[j]
                        scr_ruleitem_2 = self.scr_ruleitems[key_2]
                        # get chosen_class, supp and conf
                        chosen_class_2 = scr_ruleitem_2.chosen_class
                        supp_2 = scr_ruleitem_2.class_object[chosen_class_2]
                        conf_2 = scr_ruleitem_2.rule_conf
                        # check if classes are different and supp and conf are above thresholds
                        if chosen_class_1 != chosen_class_2 and supp_2 >= support_threshold and conf_2 >= confidence_threshold:
                            # perform different check
                            # 1. invariant attributes have the same values
                            # 2. at least 1 of varying attributes has different values between 2 rules
                            # 3. if num_inv == 0 ==> at least 1 varying should have the same value
                            is_inv_same = self.is_all_att_same(scr_ruleitem_1.inv_values, scr_ruleitem_2.inv_values)
                            is_one_var_diff = self.is_at_least_one_att_diff(scr_ruleitem_1.var_values,
                                                                            scr_ruleitem_2.var_values)
                            is_one_var_same = self.is_at_least_one_att_same(scr_ruleitem_1.var_values,
                                                                            scr_ruleitem_2.var_values)
                            if is_inv_same and is_one_var_diff and ((num_inv > 0) or is_one_var_same):
                                # ok, scr_ruleitem_1 and scr_ruleitem_2 form a pair
                                if key_1 not in rule_object:
                                    # form rule and put it into rule_object
                                    # sort key_1 according to value; class has only one value, no need to sort
                                    temp = key_1.split(',')
                                    temp.sort()
                                    key_1_sorted = ''
                                    for el in temp:
                                        key_1_sorted += el + ','
                                    key_1_sorted = key_1_sorted[:-1]
                                    # and also create set representations
                                    LHS_set = set(temp)
                                    RHS_set = set([chosen_class_1])
                                    rule_1 = {
                                        constants.LHS: key_1_sorted, constants.RHS: chosen_class_1,
                                        constants.LHS_SET: LHS_set, constants.RHS_SET: RHS_set,
                                        constants.LHS_SUPP_COUNT: scr_ruleitem_1.tot_supp,
                                        constants.LHS_SUPP: (float(scr_ruleitem_1.tot_supp) / tot_records_num),
                                        constants.RULE_SUPP_COUNT: supp_1,
                                        constants.RULE_SUPP: (float(supp_1) / tot_records_num),
                                        constants.RULE_CONF: conf_1
                                    }
                                    rule_object[key_1] = rule_1
                                if key_2 not in rule_object:
                                    # sort key_2 according to value; class has only one value, no need to sort
                                    temp = key_2.split(',')
                                    temp.sort()
                                    key_2_sorted = ''
                                    for el in temp:
                                        key_2_sorted += el + ','
                                    key_2_sorted = key_2_sorted[:-1]
                                    # and also create set representations
                                    LHS_set = set(temp)
                                    RHS_set = set([chosen_class_2])
                                    rule_2 = {
                                        constants.LHS: key_2_sorted, constants.RHS: chosen_class_2,
                                        constants.LHS_SET: LHS_set, constants.RHS_SET: RHS_set,
                                        constants.LHS_SUPP_COUNT: scr_ruleitem_2.tot_supp,
                                        constants.LHS_SUPP: (float(scr_ruleitem_2.tot_supp) / tot_records_num),
                                        constants.RULE_SUPP_COUNT: supp_2,
                                        constants.RULE_SUPP: (float(supp_2) / tot_records_num),
                                        constants.RULE_CONF: conf_2
                                    }
                                    rule_object[key_2] = rule_2
                                # this is a good pair, update references object
                                ref_object[key_1].append(key_2)
                                ref_object[key_2].append(key_1)
            # now form array of rules who have pairs
            # this variable will contain a position of rule in final array
            key_to_pos_object = {}
            pos_to_key_object = {}
            for key in ref_object:
                if len(ref_object[key]) > 0:
                    # there are some links, add it to the final list
                    pos = len(result)
                    result.append(rule_object[key])
                    # save the position
                    key_to_pos_object[key] = pos
                    pos_to_key_object[pos] = key

            # now update references
            for pos in range(0, len(result)):
                key = pos_to_key_object[pos]
                link_keys = ref_object[key]
                ref_str = ''
                for link_key in link_keys:
                    link_pos = key_to_pos_object[link_key]
                    # do the correction to count from 1
                    ref_str += str(link_pos+1) + ','
                # add new field to the rule
                result[pos][constants.LINKS] = ref_str[:-1]

        return result

    @staticmethod
    def is_all_att_same(dic_1, dic_2):
        # dic_1 and dic_2 are 2 dictionaries of the form
        # attribute:attribute_val
        result = True
        for key in dic_1:
            # check if the values of key in dic_1 and dic_2 are the same
            if dic_1[key] != dic_2[key]:
                result = False
                break
        return result

    @staticmethod
    def is_at_least_one_att_same(dic_1, dic_2):
        # dic_1 and dic_2 are 2 dictionaries of the form
        # attribute:attribute_val
        result = False
        for key in dic_1:
            # check if the values of key in dic_1 and dic_2 are the same
            if dic_1[key] == dic_2[key]:
                result = True
                break
        return result

    @staticmethod
    def is_at_least_one_att_diff(dic_1, dic_2):
        # dic_1 and dic_2 are 2 dictionaries of the form
        # attribute:attribute_val
        result = False
        for key in dic_1:
            # check if the values of key in dic_1 and dic_2 are the same
            if dic_1[key] != dic_2[key]:
                result = True
                break
        return result

    def init_scr_ruleitems(self, original_transactions_info):
        scr_ruleitems = {}
        scr_ruleitems_info = {}
        init_meta_info = True
        for el in self.root.count:
            pos = el.rfind(',')
            hash_val = el[0:pos]
            class_val = el[pos+1:]
            if hash_val in scr_ruleitems:
                # ruleitem is already there, just update class info
                scr_ruleitems[hash_val].class_object[class_val] = self.root.count[el]
            else:
                # add this scr_rileitem
                scr_ruleitem, list_of_inv, list_of_var = FPTree.decompose_element(hash_val, class_val, self.root.count[el],
                                                        original_transactions_info, init_meta_info)
                if init_meta_info:
                    init_meta_info = False
                    scr_ruleitems_info['inv'] = list_of_inv
                    scr_ruleitems_info['var'] = list_of_var

                scr_ruleitems[hash_val] = scr_ruleitem
        self.scr_ruleitems = scr_ruleitems
        self.scr_ruleitems_info = scr_ruleitems_info
        self.form_scr_ruleitmes_groups()

    def form_scr_ruleitmes_groups(self):
        analyzed_scr_ruleitems = []
        scr_groups = []

        # essentially devide on groups depending on the value of invariant attribute
        # thereby, if there are no invariant attribute, there is only one group

        if len(self.scr_ruleitems_info['inv']) == 0:
            new_group = []
            for hash_val in self.scr_ruleitems_info:
                new_group.append(hash_val)
            scr_groups.append(new_group)
        else:
            for hash_val in self.scr_ruleitems:
                if hash_val not in analyzed_scr_ruleitems:
                    # add it to analyzed_scr_ruleitems and try to search for pairs
                    analyzed_scr_ruleitems.append(hash_val)
                    a_group = []

                    for hash_val_2 in self.scr_ruleitems:
                        if hash_val_2 not in analyzed_scr_ruleitems:
                            # check if has_val and hash_val_2 can be a pair
                            # they should have the same values of invariant attiributes
                            # the varying attributes are already the same and at least some of them will
                            # have different values
                            pass
            pass

    @staticmethod
    def decompose_element(scr_element, class_val, element_frequency, original_transactions_info, meta_info=False):
        var_values = {}
        list_of_var =[]
        inv_values = {}
        list_of_inv = []
        class_obj = {}
        #hash_val=''
        # class is the las element
        class_obj[class_val] = element_frequency
        for el in scr_element.split(","):
            # check if the value of el is in invariant, varying
            found = False
            # search in var
            for att in original_transactions_info['var']['order']:
                for att_val in original_transactions_info['var'][att]:
                    if el == att_val:
                        #hash_val+=att
                        if meta_info:
                            list_of_var.append(att)
                        var_values[att] = att_val
                        found = True
                        break
            if not found:
                # continue to search in inv
                for att in original_transactions_info['inv']['order']:
                    for att_val in original_transactions_info['inv'][att]:
                        if el == att_val:
                            #hash_val += att
                            if meta_info:
                                list_of_inv.append(att)
                            inv_values[att] = att_val
                            found = True
                            break
        # return (hash_val, SCRRuleitem(list_of_inv, inv_values, list_of_var, var_values, class_obj))
        return SCRRuleitem(inv_values, var_values, class_obj), list_of_inv, list_of_var

    def revert_tree_to_transactions(self):
        all_transactions = []
        # idea: revert from the leaves of the tree
        # identify the attribute that corresponds to the leafs of this tree
        last_att_key = self.sorting_order_per_attribute[-1]
        # get the headers for this attribute
        header_dic = self.headers[last_att_key]
        # now process every possible value of this attribute
        for val_key in header_dic:
            # get the leaf and reconstruct transactions from this leaf
            node = header_dic[val_key]
            while node is not None:
                node_transactions = FPTree.reconstruct_node_transactions(node)
                all_transactions.extend(node_transactions)
                node = node.link
        return all_transactions

    @staticmethod
    def reconstruct_node_transactions(node):
        result_list_of_transactions = []

        # reconstruct the path to the root and gather all items on the way
        # get the value of the current node
        transaction = []
        next_node = node
        # value == None means we have reached the root
        while next_node.value is not None:
            transaction.append(next_node.value)
            next_node = next_node.parent
        # initialize the class value in transactions
        transaction.append('')
        # no add required number of transactions for all classes
        for class_val in node.count:
            num = node.count[class_val]
            transaction[-1] = class_val
            for i in range(0, num):
                to_add = transaction[:]
                result_list_of_transactions.append(to_add)

        return result_list_of_transactions

    def make_copy_of_tree(self, transactions_info):
        transactions = self.revert_tree_to_transactions()
        new_tree = FPTree(transactions, transactions_info)
        return new_tree

    def get_subtree(self, previous_attributes, current_att, next_att, rest_of_attributes):
        # this should be replaces with converting self into a list of transactions and making new tree of it
        #subtree = copy.deepcopy(self)
        subtree = FPTree.make_copy_of_tree(self, self.transactions_info)

        # define new class values
        # get the values of the current attribute that will be added to class label
        current_class_values = self.transactions_info["class"]

        att_type_key = subtree.get_attribute_type(current_att)
        current_attribute_values = self.transactions_info[att_type_key][current_att]
        # combine them with the class values
        new_class_values = []
        for curr_att_val in current_attribute_values:
            for curr_class in current_class_values:
                new_class_values.append(curr_att_val + ',' + curr_class)

        # update tree structure

        # update class values in the leafs of the tree (if it is not root)
        if next_att is not None:
            for next_att_val in subtree.headers[next_att]:
                # next_att_val is a node for which the values should be updated
                next_att_node = subtree.headers[next_att][next_att_val]
                while next_att_node is not None:
                    next_att_node.count = {}
                    for new_class_val in new_class_values:
                        next_att_node.count[new_class_val] = 0

                    for a_child in next_att_node.children:
                        for class_val in current_class_values:
                            next_att_node.count[a_child.value + "," + class_val] = a_child.count[class_val]
                    # delete children
                    next_att_node.children = []
                    next_att_node = next_att_node.link

        # now propagate changes to the root
        # change the class labels and values for the rest of the nodes
        for next_level_att in rest_of_attributes:
            for next_att_val in subtree.headers[next_level_att]:
                next_att_node = subtree.headers[next_level_att][next_att_val]
                while next_att_node is not None:
                    FPTree.update_node_counts_according_to_children(next_att_node, new_class_values)
                    next_att_node = next_att_node.link

        # update values for root node
        if next_att is not None:
            FPTree.update_node_counts_according_to_children(subtree.root, new_class_values)
        else:
            # this is the last root level
            subtree.root.count = {}
            # initialize root.count with 0 for all new class_values
            for new_class_val in new_class_values:
                subtree.root.count[new_class_val] = 0
            for a_child in subtree.root.children:
                for class_val in current_class_values:
                    subtree.root.count[a_child.value + "," + class_val] = a_child.count[class_val]
            # delete children
            subtree.root.children = []

        # now update the rest of the attributes of the tree
        # headers, sorting_order_per_attribute, sorting_order_per_value, transactions_info

        # headers ==> just delete everything that is not in next_att or in rest_of_attributes
        new_headers = {}
        # keys should be the same for headers and sorting_order_per_attribute
        for key in subtree.headers:
            if (key == next_att) or (key in rest_of_attributes):
                new_headers[key] = subtree.headers[key]
        subtree.headers = new_headers
        # del subtree.headers[current_att]

        # sorting_order_per_attribute ==> just delete current and previous attributes
        subtree.sorting_order_per_attribute.remove(current_att)
        for val in previous_attributes:
            subtree.sorting_order_per_attribute.remove(val)

        # sorting_order_per_value ==> delete value of current attribute and previous attributes
        values_of_current_att = subtree.transactions_info[att_type_key][current_att][:]
        for val in values_of_current_att:
            subtree.sorting_order_per_value.remove(val)
        # for previous attributes
        for att in previous_attributes:
            temp_key = subtree.get_attribute_type(att)
            values_of_current_att = subtree.transactions_info[temp_key][att][:]
            for val in values_of_current_att:
                subtree.sorting_order_per_value.remove(val)
        # delete values of class attribute
        for val in current_class_values:
            subtree.sorting_order_per_value.remove(val)
        # now add new class values
        for val in new_class_values:
            subtree.sorting_order_per_value.append(val)

        # transactions_info ==> update 'class' and 'var/inv'
        # class - set new class values
        subtree.transactions_info['class'] = new_class_values[:]
        # var/inv - delete the values of current attribute
        del subtree.transactions_info[att_type_key][current_att]
        # and delete from ordering info
        subtree.transactions_info[att_type_key]['order'].remove(current_att)
        # delete previous attributes
        for att in previous_attributes:
            temp_key = self.get_attribute_type(att)
            # delete the values
            del subtree.transactions_info[temp_key][att]
            # delete from ordering info
            subtree.transactions_info[temp_key]['order'].remove(att)

        return subtree

    def get_attribute_type(self, attribute):
        if attribute in self.transactions_info['var']:
            return 'var'
        else:
            return 'inv'

    @staticmethod
    def update_node_counts_according_to_children(node, class_values):
        if len(node.children) > 0:
            node.count = {}
            # set all values here to 0
            for class_val in class_values:
                node.count[class_val] = 0
            for a_child in node.children:
                for class_val in class_values:
                    node.count[class_val] += a_child.count[class_val]

    def node_to_string(self, node, tab_count=0, is_add_children=False):
        tabs_str = ''
        for i in range(0, tab_count):
            tabs_str += '\t'

        node_str = tabs_str + str(node.value) + ': '  # + str(node.count)
        class_str = ''
        for key in self.transactions_info['class']:
            class_str += key + ': ' + str(node.count[key]) + ', '
        node_str += '{' + class_str + '}'

        children_str = ''
        if is_add_children:
            for child_node in node.children:
                children_str += '\n\t' + tabs_str + self.node_to_string(child_node, tab_count+1, True)

        return node_str + children_str

    def to_string(self, only_tree=True, is_add_children=False):
        tree_structure_str = self.node_to_string(self.root, 0, is_add_children).rstrip()
        if not only_tree:
            # add info about other structures of the tree
            temp = '\nheaders: '
            for key in self.headers:
                temp += '\n\t' + key + '\t' + str(self.headers[key])
            tree_structure_str += temp
            # tree_structure_str += '\nheaders: ' + str(self.headers)
            tree_structure_str += '\nsorting_order_per_attribute:\n\t' + str(self.sorting_order_per_attribute)
            tree_structure_str += '\nsorting_order_per_value:\n\t' + str(self.sorting_order_per_value)
            temp = '\ntransactions_info:'
            for key in self.transactions_info:
                temp += '\n\t' + key + '\t' + str(self.transactions_info[key])
            tree_structure_str += temp
            temp = '\nscr_ruleitems:'
            if self.scr_ruleitems is None:
                temp += "\n\tNone"
            else:
                for key in self.scr_ruleitems_info:
                    #temp = self.scr_ruleitems_info[key]
                    temp += '\n\t' + key + '\t' + str(self.scr_ruleitems_info[key])
                for key in self.scr_ruleitems:
                    temp += '\n\t' + key + '\t' + self.scr_ruleitems[key].to_string()
                #temp += '\n\tchosen_class\t' + self.scr_ruleitems.chosen_class
                #temp += '\n\trule_conf\t' + self.scr_ruleitems.rule_conf
            tree_structure_str += temp
        return tree_structure_str


def find_frequent_patterns(transactions, transactions_info, support_threshold, confidence_threshold, is_verbose=False):
    """
    Given a set of transactions, find the patterns in it
    over the specified support threshold.
    """
    tree = FPTree(transactions, transactions_info)
    if is_verbose:
        print 'Original FP_tree\n' + tree.to_string(False)
    #print tree.to_string()
    return tree.mine_patterns(support_threshold, confidence_threshold, transactions_info, len(transactions), is_verbose)

