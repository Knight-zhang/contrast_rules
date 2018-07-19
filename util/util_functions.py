import constants

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
        print el


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
    itemsets_to_find_str = ['03-Vechicl.=2,12-Husb.Income=05',
                            '03-Vechicl.=2,12-Husb.Income=05,NO',
                            '02-Apart.,03-Vechicl.=2,08-Husb.:West Europe,10-Husb.work.class=PrivateWorker,11-Wife.work.class=PrivateWorker,NO',
                            '02-Apart.',
                            ]
    itemsets_to_find_arr = {}
    for key in itemsets_to_find_str:
        itemsets_to_find_arr[key] = key.split(',')

    transactions = un_zip_transactions_2(file_with_transactions)
    tot_support_num = find_itemsets_in_transactions(transactions, itemsets_to_find_arr)
    for el in tot_support_num:
        print('{} : {}'.format(el, tot_support_num[el]))


#######################
# entry point
#######################
if __name__ == '__main__':
    # get_support_count()
    get_all_possible_values_of_attributes("../data/toMine_1_1.txt")
