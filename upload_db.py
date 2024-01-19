from sqlwrap import dict_insert,sql_connect,json_select_all_key
import json
import sys
import os

def upload_to_db(file_path):

    table_name = "出品商品管理票"

    # ファイルから JSON データを読み込む
    with open(file_path, 'r', encoding='utf-8') as file:
        data_dict = json.load(file)

    conn_str = os.environ["CONN_STR"]
    conn = sql_connect(conn_str)

    for data in  data_dict:
        #print(data)
        ret = dict_insert(conn,table_name,data)
        print(ret)

    conn.commit()
    conn.close()






if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input('ファイル名を入力してください')

    upload_to_db(file_path)
