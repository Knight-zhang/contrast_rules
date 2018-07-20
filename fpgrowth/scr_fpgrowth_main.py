import sys
import scr_fpgrowth
import time

sys.path.insert(0, '../util')
import util_functions


def run_census(file_name, support_number_threshold, confidence_threshold, output_file_name=None):
    """
    Generate SCR-patterns for census data files.

    :param file_name: file with transactions
    :param support_number_threshold: minimum support number
    :param confidence_threshold: minimum confidence
    :param output_file - a file to save resulting patterns, if none, the results are printed
    :return:
    """
    trans_info = {"inv": {"order": ["06", "07", "08", "09", "10", "11"],
                          "06": ['06-Husb.:no school',
                                 '06-Husb.:school',
                                 '06-Husb.:no college',
                                 '06-Husb.:college',
                                 '06-Husb.:bachelor',
                                 '06-Husb.:master',
                                 '06-Husb.:associate',
                                 '06-Husb.:doctor'],
                          "07": ['07-Wife:no school',
                                 '07-Wife:school',
                                 '07-Wife:no college',
                                 '07-Wife:college',
                                 '07-Wife:bachelor',
                                 '07-Wife:master',
                                 '07-Wife:associate',
                                 '07-Wife:doctor'],
                          "08": ['08-Husb.:West Europe',
                                 '08-Husb.:Latino',
                                 '08-Husb.:Other American',
                                 '08-Husb.:Afro-American',
                                 '08-Husb.:Mexico',
                                 '08-Husb.:other Asia',
                                 '08-Husb.:Pasific',
                                 '08-Husb.:North Africa and SouthAsia',
                                 '08-Husb.:East Europe',
                                 '08-Husb.:Australia',
                                 '08-Husb.:other Africa',
                                 '08-Husb.:Central America Islands'],
                          "09": ['09-Wife:West Europe',
                                 '09-Wife:Mexico',
                                 '09-Wife:Other American',
                                 '09-Wife:Afro-American',
                                 '09-Wife:East Europe',
                                 '09-Wife:Latino',
                                 '09-Wife:other Asia',
                                 '09-Wife:Pasific',
                                 '09-Wife:North Africa and SouthAsia',
                                 '09-Wife:other Africa',
                                 '09-Wife:Australia',
                                 '09-Wife:Central America Islands'],
                          "10": ['10-Husb.work.class=PrivateWorker',
                                 '10-Husb.work.class=GovernmWorker',
                                 '10-Husb.work.class=NoWork',
                                 '10-Husb.work.class=SelfEmployed'],
                          "11": ['11-Wife.work.class=GovernmWorker',
                                 '11-Wife.work.class=PrivateWorker',
                                 '11-Wife.work.class=NoWork',
                                 '11-Wife.work.class=SelfEmployed']
                          },
                  "var": {"order": ["01", "02", "03", "12"],
                          "01": ['01-H. not owned', '01-H. owned'],
                          "02": ['02-Apart.', '02-Det. house', '02-No stat. home', '02-Att. house'],
                          "03": ['03-Vechicl.=2', '03-Vechicl.=1', '03-Vechicl.>=4', '03-Vechicl.=0', '03-Vechicl.=3'],
                          "12": ['12-Husb.Income=05', '12-Husb.Income=04', '12-Husb.Income=02', '12-Husb.Income=03',
                                 '12-Husb.Income=06', '12-Husb.Income=07', '12-Husb.Income=08', '12-Husb.Income=10',
                                 '12-Husb.Income=01', '12-Husb.Income=09', '12-Husb.Income=11']
                          },
                  "class": ['YES', 'NO']}

    transactions = util_functions.unzip_transactions_2(file_name)

    start = time.time()
    patterns = scr_fpgrowth.find_frequent_patterns(transactions, trans_info, support_number_threshold,
                                                     confidence_threshold, is_verbose=False)
    end = time.time()
    print('Total elapsed for patterns construction {}'.format(end - start))
    str_res = util_functions.patterns_to_string(patterns)
    if output_file_name is None:
        # print the results
        print('\nPatterns')
        print(str_res)
    else:
        # print results into a file
        print('Saving results to {}   ...'.format(output_file_name))
        with open(output_file_name, 'w') as output_file:
            output_file.write(str_res)


if __name__ == '__main__':
    path = '../data/'
    transactions_file_name = 'toMine_1_1.txt'
    min_supp_count = 10
    min_conf = 0.7
    output_file_name = '../results/scr_fpgrowth/{}_supp_{}_conf_{}.txt'. \
        format(transactions_file_name[:transactions_file_name.find('.txt')], min_supp_count,
               str(min_conf).replace('.', ''))
    run_census(path + transactions_file_name, min_supp_count, min_conf,
               output_file_name)
