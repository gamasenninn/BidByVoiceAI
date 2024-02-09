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
import pprint

load_dotenv()

UPLOAD_FILE_NAME = os.environ["UPLOAD_FILE_NAME"]

detail_replacements = {
        "堀取機": "手回しによる回転確認済です。",
        "ハロー": "手回しによる回転確認済です。",
        "トラクター用": "手回しによる回転確認済です",
        "トラクター": "エンジン始動し、走行、ロータリーの回転などの動作確認済です",
        "管理機": "エンジン始動し、走行、ロータリーの回転などの動作確認済です",
        "コンバイン": "エンジン始動し、走行、刈取などの動作確認済です。\\実際の稲を使っての実戦テストは環境上行っておりません。",
        "田植機": "エンジン始動し、走行、植付などの動作確認済です",
        "運搬車": "エンジン始動し、走行、◯◯ダンプ動作などの動作確認済です",
        "草刈機": "エンジン始動し、走行、刈刃の回転などの動作確認済です"
    }

def make_top_sentence(text):
    for key, value in detail_replacements.items():
        # キーがtextに含まれていたらvalueを返す
        if key in text:
            return value
    return ""

def extract_count(input_str, index):
    """Extracts the numeric count following a character at a given index."""
    if index != -1:
        end_index = index + 1
        while end_index < len(input_str) and input_str[end_index].isdigit():
            end_index += 1
        return int(input_str[index + 1:end_index]) if end_index > index + 1 else 1
    return 0

def create_movement_string(direction, count):
    """Creates a formatted string for the movement."""
    if count > 0:
        moves = '-'.join(str(i) for i in range(1, count + 1))
        return f"前進{moves}" if direction == 'f' else f"後進{moves}"
    return ""

def convert_movement_instructions(input_str):
    input_str = input_str.replace(" ", "").lower()

    # Extract counts for forward and reverse movements
    forward_count = extract_count(input_str, input_str.find('f'))
    reverse_count = extract_count(input_str, input_str.find('r'))

    # Generate formatted strings for each movement
    forward_str = create_movement_string('f', forward_count)
    reverse_str = create_movement_string('r', reverse_count)

    # Combine the results
    return "、".join(filter(None, [forward_str, reverse_str]))

def extract_and_format_number(input_str):
    # 正規表現を使用して、数字を見つける
    match = re.search(r'\d+', input_str)
    if match:
        return match.group() + "cm"
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
        detail += 'アワーメーター: '+ str(src_data.get('hour')) + "\\（展示移動によるメーター加算はご了承ください）\\"  

    # 主変速
    if src_data.get('primary_transmission',""):
        pt = convert_movement_instructions(src_data.get('primary_transmission')) 
        detail += '主変速: '+ pt + "\\"  

    #副変速
    if src_data.get('secondary_transmission',""): 
        detail += '副変速: '+ src_data.get('secondary_transmission')+ "\\"

    #耕耘幅
    if src_data.get('plowing_width',""): 
        detail += '\\耕耘幅: '+ extract_and_format_number(src_data.get('plowing_width'))+ "\\"

    #刈幅
    if src_data.get('mowing_width',""): 
        detail += '\\刈幅: '+ extract_and_format_number(src_data.get('mowing_width'))+ "\\"

    #荷台寸法
    if src_data.get('cargo_size',""): 
        detail += '\\荷台寸法: '+ src_data.get('cargo_size')+ "\\"
        
    #最大積載量
    if src_data.get('max_load',""): 
        detail += '\\最大積載量: '+ src_data.get('max_load')+ "\\"

    #作業機情報
    if src_data.get('sub_machine',""): 
        detail += '\\作業機: '+ src_data.get('sub_machine')+ "\\"


    #エンジン型式
    detail += "\\"
    if src_data.get('engine_model',""): 
        detail += 'エンジン型式: '+ src_data.get('engine_model').replace(' ','').upper()+ "\\"

    #最大出力
    if src_data.get('max_ps',""): 
        detail += '最大出力: '+ str(src_data.get('max_ps'))+ "PS\\"

    #燃料種別
    if src_data.get('fuel_type',""): 
        detail += '燃料種別: '+ src_data.get('fuel_type')+ "\\"

    #仕様
    if src_data.get('spec',""): 
        detail += '\\【仕様】: '+ src_data.get('spec')+ "\\"
    #定型文
    detail+= "\\経年と使用によるサビ、傷、汚れがあります。\\画像のもので全てです。"

    #備考
    memo = src_data.get('memo',"")
    if src_data.get('battery_size',""):
        memo +=  '\\バッテリーサイズ: ' + src_data.get('battery_size',"")+ "\\"      

    converted = {
        '相対番号': src_data.get('listing_number',""),
        '記入日':   entry_date,
        '仕切書No': src_data.get('scode',""),
        '担当者':   src_data.get('responsible_person',""),
        '商品名':   src_data.get('product_name',""),
        'メーカー': src_data.get('maker',""),
        '型式': src_data.get('model',"").replace(" ","").upper(),
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
        '備考': memo,
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
    pprint.pprint(data_dict,indent=4)

    # CSVファイルに出力
    df.to_csv(f'{UPLOAD_FILE_NAME}.csv', index=False)

    # ファイルに出力
    output_file = f'{UPLOAD_FILE_NAME}.json'  # 出力するファイル名
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data_dict, file, ensure_ascii=False, indent=4)

    print(f"データが {output_file} に保存されました。\n")


