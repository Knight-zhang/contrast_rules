import car_fpgrowth
import sys
import time

sys.path.insert(0, '../util')
import util_functions


def run(transactions_file_name, min_supp_count, min_conf, possible_class_values, output_file_name=None):

    transactions = util_functions.unzip_transactions_2(transactions_file_name)
    start = time.time()
    patterns = car_fpgrowth.find_frequent_patterns(transactions, min_supp_count, possible_class_values)
    #rules = car_fpgrowth.generate_association_rules_with_one_item_consequent(patterns, min_conf, len(transactions))
    rules = car_fpgrowth.generate_classification_rules(patterns, min_conf, len(transactions), possible_class_values)
    end = time.time()
    print('Total elapsed {}'.format((end - start)))
    if output_file_name is not None:
        print('Saving results to {}'.format(output_file_name))
        rules_str = util_functions.rules_to_string(rules)
        with open(output_file_name, 'w') as output_file:
            output_file.write(rules_str)
    else:
        rules_str = util_functions.rules_to_string(rules)
        print("\nPatterns")
        print(rules_str)


if __name__ == '__main__':
    path_name = '../data/'
    transactions_file_name = 'toMine_1_1.txt'
    min_supp_count = 100
    min_conf = 0.7
    possible_class_values = ["YES", "NO"]
    output_file_name = '../results/car_fpgrowth/{}_supp_{}_conf_{}.txt'.\
        format(transactions_file_name[:transactions_file_name.find('.txt')], min_supp_count,
               str(min_conf).replace('.', ''))
    run(path_name + transactions_file_name, min_supp_count, min_conf, possible_class_values, output_file_name)
