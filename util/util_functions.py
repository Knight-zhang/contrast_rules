import constants
import sys
import collections


#######################
# reading transactions
#######################
def unzip_transactions_2(zipped_transactions_file):
    """
    Read transactions from zipped_transactions_file and put them into transactions_list
    """
    transactions_list = []
    with open(zipped_transactions_file) as f:
        for line in f:
            temp = line.rstrip().split(',')
            transactions_list.append(temp)
    return transactions_list


#######################
# transforming patterns into string
#######################
def patterns_to_string(patterns_list):
    str_result = '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(constants.LHS, constants.RHS,
                                                           constants.LHS_SUPP_COUNT, constants.RULE_SUPP_COUNT,
                                                           constants.LHS_SUPP, constants.RULE_SUPP, constants.RULE_CONF,
                                                           constants.LINKS)
    for pattern in patterns_list:
        for rule in pattern:
            str_result += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                rule[constants.LHS], rule[constants.RHS],
                rule[constants.LHS_SUPP_COUNT], rule[constants.RULE_SUPP_COUNT],
                rule[constants.LHS_SUPP], rule[constants.RULE_SUPP], rule[constants.RULE_CONF], rule[constants.LINKS])
        str_result += '\n'
    return str_result


def rules_to_string(rules_list):
    str_result = '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(constants.LHS, constants.RHS,
                                                           constants.LHS_SUPP_COUNT, constants.RULE_SUPP_COUNT,
                                                           constants.LHS_SUPP, constants.RULE_SUPP, constants.RULE_CONF,
                                                           constants.LINKS)
    for rule in rules_list:
        if rule == set():
            str_result += '\n'
            continue
        str_result += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
            rule[constants.LHS], rule[constants.RHS],
            rule[constants.LHS_SUPP_COUNT], rule[constants.RULE_SUPP_COUNT],
            rule[constants.LHS_SUPP], rule[constants.RULE_SUPP], rule[constants.RULE_CONF], rule[constants.LINKS])
    str_result += '\n'
    return str_result


#######################
# analysis of possible attribute values
#######################
def analyze_transactions_info(transactions_info):
    """
    Used in get_all_possible_values_of_attributes
    """
    num_of_attributes = len(transactions_info[0])
    attribute_values = []
    for i in range(0, num_of_attributes):
        attribute_values.append([])

    for el in transactions_info:
        for i in range(0, len(el)):
            val = el[i]
            if val not in attribute_values[i]:
                attribute_values[i].append(val)

    # now print the values
    for el in attribute_values:
        print(el)


def get_all_possible_values_of_attributes(file_name):
    """
    Utility function to get and print all possible values of every attribute
    The list of transactions is read from the file file_name
    """
    transactions = unzip_transactions_2(file_name)
    analyze_transactions_info(transactions)


#######################
# get support count for itemsets
#######################
def find_itemsets_in_transactions(transactions, itemsets_to_find):
    """
    Is used in get_support_count
    """
    # transactions - array of arrays
    # itemsets_to_find - dictionary of arrays
    tot_support_num = {}
    for itemset_key in itemsets_to_find:
        tot_support_num[itemset_key] = 0
    # loop through the set of transactions
    for transaction in transactions:
        # now check if this transaction contains any of itemsets
        for itemset_key in itemsets_to_find:
            itemset = itemsets_to_find[itemset_key]
            has_all = True
            for item in itemset:
                if item not in transaction:
                    has_all = False
                    break
            if has_all:
                tot_support_num[itemset_key] += 1
    return tot_support_num


def get_support_count():
    """
    Get support count for every itemset in itemsets_to_find_str
    The transactions are red from file_with_transactions
    :return:
    """
    file_with_transactions = '../data/toMine_1_1.txt'
    itemsets_to_find_str = ['01-H. not owned,03-Vechicl.=1,10-Husb.work.class=PrivateWorker,11-Wife.work.class=PrivateWorker',
                            '01-H. not owned,03-Vechicl.=1,10-Husb.work.class=PrivateWorker,11-Wife.work.class=PrivateWorker,NO',
                            'NO',
                            '01-H. not owned,11-Wife.work.class=GovernmWorker,NO',
                            '01-H. not owned,11-Wife.work.class=GovernmWorker',
                            ]
    itemsets_to_find_arr = {}
    for key in itemsets_to_find_str:
        itemsets_to_find_arr[key] = key.split(',')

    transactions = unzip_transactions_2(file_with_transactions)
    tot_support_num = find_itemsets_in_transactions(transactions, itemsets_to_find_arr)
    for el in tot_support_num:
        print('{} : {}'.format(el, tot_support_num[el]))


#######################
# Compare the outputs of two files
#######################
def compare_outputs(first_file, second_file):
    """
    Compares the rules from two different files

    :return: a tuple of similiraties and dissimilarities
    """
    similar = -2
    different = 0
    with open(second_file) as open_second_file:
        for line2 in open_second_file:
            with open(first_file) as open_first_file:
                for line1 in open_first_file:
                    if line1 == line2:
                        similar += 1
                        break
                if line1 != line2:
                    different += 1
    print('There are {} similar rules and {} different rules.'.format(similar, different))


#######################
# Get the different rules between two files
#######################
def get_different_rules(first_file, second_file):
    """
    Get the rules that exist in the second file but do not exist
    in the first file

    """
    with open(second_file) as open_second_file:
        for line2 in open_second_file:
            with open(first_file) as openfileobject:
                for line1 in openfileobject:
                    if line1 == line2:
                        break
                if line1 != line2:
                    print(line2)


#######################
# Compare the rules with statistica
#######################
def compare_with_statistica(file, statistica_file):
    """
    Compares the results of the given file with association rules generates with statistica

    :returns a list of the different rules that exist in statistica but not in the file
    """
    similarities = 0
    differences = 0
    different_rules = []
    with open(statistica_file) as open_statistica_file:
        open_statistica_file.readline()
        for line1 in open_statistica_file:
            temp1 = line1.split('\t')
            temp1[0] = sorted(temp1[0].split(', '))
            with open(file) as open_file:
                open_file.readline()
                for line2 in open_file:
                    temp2 = line2.split('\t')
                    temp2[0] = sorted(temp2[0].split(','))
                    if temp1[:2] == temp2[:2]:
                        # Comparing the difference between the supports with a fixed values that can be changed
                        if (float(temp1[3].replace(',', '.'))/100) - float(temp2[6]) < 0.001:
                            similarities += 1
                        break
                if temp1[:2] != temp2[:2]:
                    differences += 1
                    different_rules.append(line1)
    print('There are {} similar rules and {} different rules'.format(similarities, differences))
    return different_rules


#######################
# comparing SCR_patterns
#######################
def read_rule_from_str(str_value):
    """
    Construct a rule in a form of dictionary from its string representation
    """
    temp = str_value.split("\t")
    # recreate links and also subtract 1 from each link (like this a link can be used as an index in an array)
    links_str = temp[7].rstrip()
    links_arr = []
    for link in links_str.split(','):
        links_arr.append(int(link) - 1)
    a_rule = {constants.LHS: temp[0], constants.LHS_SET: set(temp[0].split(",")),
              constants.RHS: temp[1], constants.RHS_SET: {temp[1]},
              constants.LHS_SUPP_COUNT: temp[2],
              constants.RULE_SUPP_COUNT: temp[3], constants.LHS_SUPP: temp[4], constants.RULE_SUPP: temp[5],
              constants.RULE_CONF: temp[6], constants.LINKS: links_arr}
    return a_rule


def read_scr_patterns_from_file(file_name):
    scr_patterns_list = []
    with open(file_name) as input_file:
        data = input_file.read().rstrip().split('\n')
        # skip the first line with headers
        scr_pattern = []
        for i in range(1, len(data)):
            line = data[i]
            if len(line) == 0:
                # new pattern starts
                scr_patterns_list.append(transform_scr_pattern_into_dic(scr_pattern[:]))
                scr_pattern = []
            else:
                # continue generating rules for current pattern
                a_rule = read_rule_from_str(line)
                scr_pattern.append(a_rule)
        # and add the last pattern
        scr_patterns_list.append(transform_scr_pattern_into_dic(scr_pattern[:]))

    return scr_patterns_list


def transform_scr_pattern_into_dic(scr_patter):
    """
    Transfrom scr_pattern represented as an array into a dictionary.
    key is 'LHS==>RHS'
    links are replaces with keys
    """
    pos_to_key = {}

    scr_pattern_dic = {}
    for i in range(0, len(scr_patter)):
        rule = scr_patter[i]
        key = rule[constants.LHS] + '==>' + rule[constants.RHS]
        scr_pattern_dic[key] = rule
        pos_to_key[i] = key

    # now update the links
    for key in scr_pattern_dic:
        rule = scr_pattern_dic[key]
        rule_links_array = rule[constants.LINKS]
        rule_links_key = []
        for link in rule_links_array:
            rule_links_key.append(pos_to_key[link])
        rule[constants.LINKS_KEYS] = rule_links_key
        rule[constants.POS_TO_KEY] = pos_to_key
    return scr_pattern_dic


def transform_scr_dic_into_array(scr_dic):
    """
    Transfrom scr_pattern represented as a dictionary into an array.
    key is 'LHS==>RHS'
    links are replaces with keys
    """
    scr_pattern_arr = []
    key = next(iter(scr_dic))
    pos_to_key = scr_dic[key][constants.POS_TO_KEY]
    for pos in pos_to_key:
        key = pos_to_key[pos]
        scr_pattern_arr.append(scr_dic[key])
    return scr_pattern_arr


def is_rules_match(rule_1, rule_2):
    """
    We already know that antecedents and consequents of rule_1 and rule_2 match.
    Just compare support_counts and links
    """
    result = False
    if rule_1[constants.LHS_SUPP_COUNT] == rule_2[constants.LHS_SUPP_COUNT] \
            and rule_1[constants.RULE_SUPP_COUNT] == rule_2[constants.RULE_SUPP_COUNT]:
        # now compare the set of links
        if collections.Counter(rule_1[constants.LINKS_KEYS]) == collections.Counter(rule_1[constants.LINKS_KEYS]):
            result = True
    return result


def is_patterns_match(scr_pat_1, scr_pat_2):
    # compare if scr-patterns match
    # perform multiple tests
    result = False

    # 1. number of rules should be the same
    if len(scr_pat_1) == len(scr_pat_2):
        # 2. compare the set of keys, they should be the same
        if collections.Counter(scr_pat_1.keys()) == collections.Counter(scr_pat_2.keys()):
            # 3. now for every rule get its matching pair and compare supports and links
            rules_matching = True
            for key in scr_pat_1:
                rule_1 = scr_pat_1[key]
                rule_2 = scr_pat_2[key]
                if not is_rules_match(rule_1, rule_2):
                    rules_matching = False
                    break
            result = rules_matching
    return result


def compare_files_with_scr_patterns(file_name_1, file_name_2):
    # read patterns from both files into memory
    scr_patterns_1 = read_scr_patterns_from_file(file_name_1)
    scr_patterns_2 = read_scr_patterns_from_file(file_name_2)
    found_1 = []
    found_2 = []

    # now try to find matches
    for i in range(0, len(scr_patterns_1)):
        scr_pat_1 = scr_patterns_1[i]
        for j in range(0, len(scr_patterns_2)):
            if j not in found_2:
                scr_pat_2 = scr_patterns_2[j]
                if is_patterns_match(scr_pat_1, scr_pat_2):
                    found_1.append(i)
                    found_2.append(j)
                    break

    # now found_1 and found_1 contain the indices of found scr_patterns, the others are missing
    missing_scr_1 = []
    missing_scr_2 = []
    for i in range(0, len(scr_patterns_1)):
        if i not in found_1:
            missing_scr_1.append(transform_scr_dic_into_array(scr_patterns_1[i]))
    for j in range(0, len(scr_patterns_2)):
        if j not in found_2:
            missing_scr_2.append(transform_scr_dic_into_array(scr_patterns_2[j]))

    print('Total found = {}'.format(len(found_1)))
    print('no matches from {} = {}'.format(file_name_1, len(missing_scr_1)))
    print('no matches from {} = {}'.format(file_name_2, len(missing_scr_2)))

    if len(missing_scr_1) > 0:
        print('\nMissing from {}...'.format(file_name_1))
        print(patterns_to_string(missing_scr_1))

    if len(missing_scr_2) > 0:
        print('Missing from {}...'.format(file_name_2))
        print(patterns_to_string(missing_scr_2))


#######################
# entry point
#######################
if __name__ == '__main__':
    compare_files_with_scr_patterns('../results/scr_fpgrowth/toMine_1_1_supp_50_conf_07.txt',
                                    '../results/scr_fpgrowth/toMine_1_1_supp_50_conf_07.txt')
    #compare_outputs('../results/apriori/toMine_3_3_supp_100_conf_06.txt',
    #                '../results/fpgrowth/toMine_3_3_supp_100_conf_06.txt')
    #get_different_rules('../results/car_apriori/toMine_1_1_supp_200_conf_07.txt',
    #                    '../results/apriori/toMine_1_1_supp_200_conf_07.txt')
    #different_rules = compare_with_statistica('../results/apriori/toMine_1_1_supp_200_conf_07.txt',
    #                                          '../results/statistica/toMine_1_1_supp_200_conf_07.txt')
    #get_support_count()
    #get_all_possible_values_of_attributes("../data/toMine_1_1.txt")
