import os
import sys
import json
import json
from datetime import datetime
import re
import csv
import pandas as pd

def make_csv(src_data):

    # CSVファイルへの書き出し
    with open('output.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # ヘッダーの書き込み
        writer.writerow(src_data.keys())
        # データ行の書き込み
        writer.writerow(src_data.values())

    print("CSVファイルにデータが書き出されました。")


def make_sql(src_data):

    # テーブル名
    table_name = "出品管理票"

    # SQL文の基本形を作成
    columns = ", ".join(src_data.keys())
    placeholders = ", ".join(["%s"] * len(src_data))
    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    # 値をタプルとして抽出
    values = tuple(src_data.values())

    # SQL文を生成
    sql = insert_query % values

    print(sql)

def convert_data(src_data):
    print(json.dumps(src_data, ensure_ascii=False, indent=4))
    print("-----------------------")

    #記入日変換
    entry_date = src_data.get('entry_date',"")
    #1月16日　-> 2023/01/06に変換する
    if entry_date:
        # 日付の形式が '1月16日' のようであることを確認
        match = re.match(r'(\d+)月(\d+)日', entry_date)
        if match:
            month = match.group(1)
            day = match.group(2)
            # 年は2023年と仮定
            formatted_date = datetime.strptime(f'2024-{month}-{day}', '%Y-%m-%d').strftime('%Y/%m/%d')
            entry_date = formatted_date

    detail = ""
    # アワー
    if src_data.get('primary_transmission',""): 
        detail += 'アワーメーター: '+ src_data.get('hour') + "//（展示移動によるメーター加算はご了承ください）//"  

    # 主変速
    if src_data.get('primary_transmission',""): 
        detail += '主変速: '+ src_data.get('primary_transmission') + "//"  

    #副変速
    if src_data.get('secondary_transmission',""): 
        detail += '副変速: '+ src_data.get('secondary_transmission')+ "//"

    #耕耘幅
    if src_data.get('plowing_width',""): 
        detail += '//耕耘幅: '+ src_data.get('plowing_width')+ "//"

    #刈幅
    if src_data.get('mowing_width',""): 
        detail += '//刈幅: '+ src_data.get('mowing_width')+ "//"

    #エンジン型式
    detail += "//"
    if src_data.get('engine_model',""): 
        detail += 'エンジン型式: '+ src_data.get('engine_model')+ "//"

    #最大出力
    if src_data.get('max_ps',""): 
        detail += '最大出力: '+ src_data.get('max_ps')+ "PS//"

    #燃料種別
    if src_data.get('fuel_type',""): 
        detail += '燃料種別: '+ src_data.get('fuel_type')+ "//"

    #定型文
    detail+= "経年と使用によるサビ、傷、汚れがあります。//画像のもので全てです。"       

    converted = {
        '相対番号': src_data.get('listing_number',""),
        '記入日':   entry_date,
        '仕切書No': src_data.get('scode',""),
        '担当者':   src_data.get('responsible_person',""),
        '商品名':   src_data.get('product_name',""),
        'メーカー': src_data.get('maker',""),
        '型式': src_data.get('model',""),
        '梱包サイズ縦': src_data.get('size_depth',""),
        '梱包サイズ横': src_data.get('size_width',""),
        '梱包サイズ高': src_data.get('size_height',""),
        '出品詳細': detail,
        '商品ランク': '-',
        '出品担当': "小野",
        '発送': "直接",
        '商品状態': "istatus_used20",
        '出品日数': "2",
        'PDNSメーカー': src_data.get('maker',""),
        '備考': src_data.get('memo',""),
        '他出品': "P"      
    }

    return converted


def make_upload_data(src_json_data):
    converted_list = []
    for j in src_json_data.get('listing'):
        converted = convert_data(j)
        print(converted)
        converted_list.append(converted)

        #make_sql(converted)
        #make_csv(converted)
    df = pd.DataFrame(converted_list)
    return df

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input('ファイル名を入力してください')

    with open(file_path,"r",encoding='utf-8') as f:
        json_data = json.load(f)
 
    df = make_upload_data(json_data)
    print(df)
    df.to_csv('output.csv', index=False)



    # データフレームを JSON 形式の辞書に変換
    data_dict = df.to_dict(orient='records')

    # ファイルに出力
    output_file = 'output.json'  # 出力するファイル名

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data_dict, file, ensure_ascii=False, indent=4)

    print(f"データが {output_file} に保存されました。")