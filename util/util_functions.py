import constants
import sys


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
# Get scr_patterns from CAR_file
#######################
def get_scrpatterns_from_car(file):
    with open(file) as open_file:
        line = open_file.readline()
        print(line.split('\t')[:-1])


#######################
# entry point
#######################
if __name__ == '__main__':
    #compare_outputs('../results/apriori/toMine_3_3_supp_100_conf_06.txt',
    #                '../results/fpgrowth/toMine_3_3_supp_100_conf_06.txt')
    #get_different_rules('../results/car_apriori/toMine_1_1_supp_200_conf_07.txt',
    #                    '../results/apriori/toMine_1_1_supp_200_conf_07.txt')
    #different_rules = compare_with_statistica('../results/apriori/toMine_1_1_supp_200_conf_07.txt',
    #                                          '../results/statistica/toMine_1_1_supp_200_conf_07.txt')
    get_scrpatterns_from_car('../results/car_apriori/toMine_1_1_supp_200_conf_07.txt')
    #get_support_count()
    #get_all_possible_values_of_attributes("../data/toMine_1_1.txt")
