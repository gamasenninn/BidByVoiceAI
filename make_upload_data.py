import os
import sys
import json
import json
from datetime import datetime
import re
import csv
import pandas as pd
from dotenv import load_dotenv
import time

load_dotenv()

UPLOAD_FILE_NAME = os.environ["UPLOAD_FILE_NAME"]

detail_replacements = {
        "堀取機": "手回しによる回転確認済です。",
        "ハロー": "手回しによる回転確認済です。",
        "トラクター": "エンジン始動し、走行、ロータリーの回転などの動作確認済です",
        "管理機": "エンジン始動し、走行、ロータリーの回転などの動作確認済です",
        "コンバイン": "エンジン始動し、走行、刈取などの動作確認済です。\\実際の稲を使っての実戦テストは環境上行っておりません。",
        "田植機": "エンジン始動し、走行、植付などの動作確認済です",
        "草刈機": "エンジン始動し、走行、刈刃の回転などの動作確認済です"
    }

def make_top_sentence(text):
    for key, value in detail_replacements.items():
        # キーがtextに含まれていたらvalueを返す
        if key in text:
            return value
    return ""


def convert_data(src_data):

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

    # 現在の日付を取得し、YYYY/MM/DD形式に変換
    current_date = datetime.now().strftime("%Y/%m/%d")


    detail = ""
    # 冒頭文を作成
    if src_data.get('product_name',""):
        detail += make_top_sentence(src_data.get('product_name',""))+"\\"

    # アワー
    if src_data.get('hour',""): 
        detail += 'アワーメーター: '+ src_data.get('hour') + "\\（展示移動によるメーター加算はご了承ください）\\"  

    # 主変速
    if src_data.get('primary_transmission',""): 
        detail += '主変速: '+ src_data.get('primary_transmission') + "\\"  

    #副変速
    if src_data.get('secondary_transmission',""): 
        detail += '副変速: '+ src_data.get('secondary_transmission')+ "\\"

    #耕耘幅
    if src_data.get('plowing_width',""): 
        detail += '\\耕耘幅: '+ src_data.get('plowing_width')+ "\\"

    #刈幅
    if src_data.get('mowing_width',""): 
        detail += '\\刈幅: '+ src_data.get('mowing_width')+ "\\"

    #エンジン型式
    detail += "\\"
    if src_data.get('engine_model',""): 
        detail += 'エンジン型式: '+ src_data.get('engine_model')+ "\\"

    #最大出力
    if src_data.get('max_ps',""): 
        detail += '最大出力: '+ src_data.get('max_ps')+ "PS\\"

    #燃料種別
    if src_data.get('fuel_type',""): 
        detail += '燃料種別: '+ src_data.get('fuel_type')+ "\\"

    #定型文
    detail+= "\\経年と使用によるサビ、傷、汚れがあります。\\画像のもので全てです。"       

    converted = {
        '相対番号': src_data.get('listing_number',""),
        '記入日':   entry_date,
        '仕切書No': src_data.get('scode',""),
        '担当者':   src_data.get('responsible_person',""),
        '商品名':   src_data.get('product_name',""),
        'メーカー': src_data.get('maker',""),
        '型式': src_data.get('model',""),
        '梱包サイズ縦': src_data.get('size_depth') if src_data.get('size_depth',"") else "0",
        '梱包サイズ横': src_data.get('size_width') if src_data.get('size_width',"") else "0",
        '梱包サイズ高': src_data.get('size_height') if src_data.get('size_height',"") else "0",
        '出品詳細': detail,
        '商品ランク': '-',
        '出品担当': "小野",
        '発送': "直接",
        '商品状態': "istatus_used20",
        '出品日数': "2",
        'PDNSメーカー': src_data.get('maker',""),
        '備考': src_data.get('memo',""),
        '出品日': current_date,
        '他出品': "P"      
    }

    return converted


def make_upload_data(src_json_data):
    converted_list = []
    for j in src_json_data.get('listing'):
        converted = convert_data(j)
        converted_list.append(converted)

    df = pd.DataFrame(converted_list)
    return df

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input('ファイル名を入力してください\n')

    with open(file_path,"r",encoding='utf-8') as f:
        json_data = json.load(f)
 
    df = make_upload_data(json_data)
    # データフレームを JSON 形式の辞書に変換
    data_dict = df.to_dict(orient='records')

    # CSVファイルに出力
    df.to_csv(f'{UPLOAD_FILE_NAME}.csv', index=False)

    # ファイルに出力
    output_file = f'{UPLOAD_FILE_NAME}.json'  # 出力するファイル名
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data_dict, file, ensure_ascii=False, indent=4)

    print(f"データが {output_file} に保存されました。\n")


