import multiprocessing as mp
import numpy as np
import pandas as pd
from commons.get_driver import *
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
# LOCAL_PATH = os.getcwd()
today_string = datetime.now().strftime("%Y%m%d")
time_string = datetime.now().strftime("%H")
today_folder = os.path.join(LOCAL_PATH, today_string)
time_folder = os.path.join(today_folder, time_string + "時")
path = (pd.read_excel(os.path.join(
        LOCAL_PATH, "crawling_list.xlsx"), engine='openpyxl', sheet_name="KEYWORD"))['path'][0]
sub_move_folder = os.path.join(path, today_string, time_string + "時")
os.makedirs(today_folder, exist_ok=True)
os.makedirs(time_folder, exist_ok=True)
os.makedirs(sub_move_folder, exist_ok=True)


def read_script(filename):
    with open(os.path.join(LOCAL_PATH, '00_setting', filename), "r", encoding="UTF-8", errors="ignore") as file:
        script = file.read()
    return script


def read_crawl_list():
    df = pd.read_excel(os.path.join(
        LOCAL_PATH, "crawling_list.xlsx"), engine='openpyxl', sheet_name="KEYWORD")
    sub = df[df['KEYWORD'] != ""]
    list_keys = list(sub['KEYWORD'])
    return list_keys


def get_info(script):
    return read_script(script)


def load_webpage(browsers, script):
    return json.loads(browsers.driver.execute_script(script))


def dataframe(json_change):
    return pd.DataFrame(json_change[1:], columns=json_change[0])


def get_data(lit_keys: list):
    process_name = mp.current_process().name
    browsers = WebDriver(exe_path=os.path.join(LOCAL_PATH, "00_setting", "chrome_driver.exe"))
    # read scripts
    crawl_script_1 = get_info('node_sb_top.txt')
    crawl_script_2 = get_info('node_sp_o_mid.txt')
    crawl_script_3 = get_info('node_sp_mid.txt')
    crawl_script_4 = get_info('node_sb_mid_bottom.txt')
    index = 0
    for keys in lit_keys:
        index = index + 1 
        print(f'{process_name} : {index}/{len(lit_keys)} : {keys}')
        browsers.driver.get(f"https://www.amazon.co.jp/s?k={keys}")
        sleep(1)
        browsers.wait_redirected()
        # load webpages
        response_1 = load_webpage(browsers, crawl_script_1)
        sleep(0.5)
        response_2 = load_webpage(browsers, crawl_script_2)
        sleep(0.5)
        response_3 = load_webpage(browsers, crawl_script_3)
        sleep(0.5)
        response_4 = load_webpage(browsers, crawl_script_4)
        sleep(0.5)
        # create dataframes
        df_1 = dataframe(response_1)
        df_2 = dataframe(response_2)
        df_3 = dataframe(response_3)
        df_4 = dataframe(response_4)
        lst_df = []
        if len(df_1) > 0:
            lst_df.append(df_1[:3])
        if len(df_2) > 0:
            lst_df.append(df_2[:10])
        if len(df_3) > 0:
            lst_df.append(df_3[:5])
        if len(df_4) > 0:
            lst_df.append(df_4[:1])
        if len(df_2) > 0:
            lst_df.append(df_2[10:])
        if len(df_4) > 1:
            lst_df.append(df_4[1:])
        if len(df_3) > 5:
            lst_df.append(df_3[5:])

        df_final = pd.concat(lst_df, ignore_index=True)
        df_final.to_csv(os.path.join(time_folder, f"{today_string}_{time_string}時_{keys}.csv"),
                        encoding='utf-16', sep="\t", index=False)
        if sub_move_folder:
            shutil.copy2(os.path.join(time_folder, f"{today_string}_{time_string}時_{keys}.csv"), os.path.join(sub_move_folder,f"{today_string}_{time_string}時_{keys}.csv"))
        else:
            f"{sub_move_folder}：存在しない"
    browsers.quit()


if __name__ == '__main__':
    mp.freeze_support()
    try:
        this_start = datetime.now()
        print("==========START==========")
        lst_keys = read_crawl_list()
        WORKERS = 2
        if len(lst_keys) < 10:
            get_data(lst_keys)
        else:
            list_of_lists = np.array_split(lst_keys, WORKERS)
            # converting numpy arrays to lists
            output = [lst.tolist() for lst in list_of_lists]
            with mp.Pool(WORKERS) as pool:
                pool.map(get_data, output)

        this_end = datetime.now()

        print(f"COMPLETED, {this_start.strftime('%H:%M:%S')}~{this_end.strftime('%H:%M:%S')}, "
                    f"in {timedelta(seconds=int((this_end - this_start).total_seconds()))} seconds")
    except Exception as total_e:
        print("TOTAL ERROR", total_e)
