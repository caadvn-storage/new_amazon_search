
from commons.get_driver import *
import numpy as np
import multiprocessing as mp
import sys
import pandas as pd
import logging


# LOCAL_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
LOCAL_PATH = os.getcwd()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log.txt", mode='w')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s', datefmt="%H:%M")
handler.setFormatter(formatter)

logger.addHandler(handler)
today_string = datetime.now().strftime("%Y%m%d")
time_string = datetime.now().strftime("%H")
today_folder = os.path.join(LOCAL_PATH, today_string)
time_folder = os.path.join(today_folder, time_string + "時_Rank")
path = (pd.read_excel(os.path.join(
        LOCAL_PATH, "crawling_list.xlsx"), engine='openpyxl', sheet_name="RANKING"))['path'][0]
sub_move_folder = os.path.join(path, today_string, time_string + "時_Rank")
os.makedirs(today_folder, exist_ok=True)
os.makedirs(time_folder, exist_ok=True)
os.makedirs(sub_move_folder, exist_ok=True)


def read_script(filename):
    with open(os.path.join(LOCAL_PATH, '00_setting', filename), "r", encoding="UTF-8", errors="ignore") as file:
        script = file.read()
    return script


def read_crawl_list():
    df = pd.read_excel(os.path.join(
        LOCAL_PATH, "crawling_list.xlsx"), engine='openpyxl', sheet_name="RANKING")
    sub = df[df['RANKING_URL'] != ""]
    list_links = list(sub['RANKING_URL'])
    return list_links


def get_info(script):
    return read_script(script)


def load_webpage(browsers, script):
    return json.loads(browsers.driver.execute_script(script))


def dataframe(json_change):
    return pd.DataFrame(json_change[1:], columns=json_change[0])


def get_data(list_links: list):
    global category_name
    process_name = mp.current_process().name
    browsers = WebDriver()
    # read scripts
    crawl_script_1 = get_info('crawl_rank.txt')

    page_lst = ["?ie=UTF8&ref_=sv_hpc_1", "ref=zg_bs_pg_2_hpc?ie=UTF8&pg=2"]
    index = 0
    for links in list_links:
        index = index + 1 
        print(f'{process_name} : {index}/{len(list_links)} : {links}')
        lst_df = []
        for page in page_lst:
            if links.endswith("/"):
                url = links + page
            else:
                url = links + "/" + page
            browsers.driver.get(url)
            category_name = browsers.get_element_by_xpath(
                '//h1[@class="a-size-large a-spacing-medium a-text-bold"]').text.split("の")[0]
            browsers.wait_redirected()
            browsers.driver.execute_script('window.scrollBy(0, 500000);')
            sleep(1)
            browsers.wait_redirected()
            try:
                browsers.wait_element_by_xpath('.//div[@id="gridItemRoot"][50]')
            except:
                print("50下")
            # load webpages
            response_1 = load_webpage(browsers, crawl_script_1)

            # create dataframes
            df_1 = dataframe(response_1)

            if len(df_1) > 0:
                lst_df.append(df_1)
                if len(df_1) < 50:
                    break
            
        df_final = pd.concat(lst_df, ignore_index=True)
        category_id = links.split("/")[-2]
        file_name = f"{today_string}_{time_string}時_{category_name}({category_id}).csv"
        df_final.to_csv(os.path.join(time_folder, file_name),
                        encoding='utf-16', sep="\t", index=False)
        if sub_move_folder:
            shutil.copy2(os.path.join(time_folder, file_name), os.path.join(sub_move_folder,file_name))
        else:
            f"{sub_move_folder}：存在しない"
    browsers.quit()


if __name__ == '__main__':
    logging.basicConfig(filename="log.txt", filemode='w',
                    level="INFO", format='%(asctime)s - %(name)s - %(message)s', datefmt="%H:%M")
    mp.freeze_support()
    try:
        this_start = datetime.now()
        print("==========START==========")
        list_links = read_crawl_list()
        WORKERS = 2
        if len(list_links) < 10:
            get_data(list_links)
        else:
            list_of_lists = np.array_split(list_links, WORKERS)
            # converting numpy arrays to lists
            output = [l.tolist() for l in list_of_lists]
            with mp.Pool(WORKERS) as pool:
                pool.map(get_data, output)

        this_end = datetime.now()

        print(f"COMPLETED, {this_start.strftime('%H:%M:%S')}~{this_end.strftime('%H:%M:%S')}, "
                    f"in {timedelta(seconds=int((this_end - this_start).total_seconds()))} seconds")
    except Exception as total_e:
        print("TOTAL ERROR", total_e)

