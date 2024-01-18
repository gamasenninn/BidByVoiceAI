
import os
import sys
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from dotenv import load_dotenv
import openai
import json


# 環境変数の読み込み
load_dotenv()
OPEN_API_KEY = os.environ["OPEN_API_KEY"]
openai.api_key = OPEN_API_KEY

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# メッセージのテンプレート
MESSAGE_TEMPLATE = """
{keyword}次に示す項目ごとに効果的に変換して。
出力は下記の項目だけを純粋な配列のJSON形式でお願いします。
{{
    listing=[{{
        'listing_number':(出品番号),
        'entry_date':(記入日),
        'scode':(管理番号),
        'responsible_person':(担当者),
        'product_name':(商品名),
        'maker':(メーカー),
        'model':(モデル),
        'size_depth':(サイズ縦),
        'size_width':(サイズ横),
        'size_height':(サイズ高さ),
        'engine_model': (エンジン型式), 
        'max_ps': (馬力),
        'fuel_type':(燃料種別),
        'plowing_width':(耕耘幅),
        'mowing_width':(刈幅。制約1を参照),
        'battery_size':(バッテリーサイズ),
        'primary_transmission': (主変速。制約2),
        'secondary_transmission':(副変速),
        'listing_details':[(出品詳細)] 
    }}]
}}
#制約1
仮幅となっている場合があります。刈幅としてください。
#制約2
内容がF2R1など略語になっている場合があります。次のように変換してください。
例:
F2R1 -> 前進1-2、後進1
F3R3 -> 前進1-2-3、後進1-2-3

"""

def convert_to_json(src_text):
    #req_text = extract_text(src_text)

    try:
        keyword = "中古農機具店での電話のやりとりです。"
        system_message_content = MESSAGE_TEMPLATE.format(keyword=keyword)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            response_format={ "type": "json_object" },
            messages=[
                {
                    "role": "system",
                    "content": system_message_content
                },
                {
                    "role": "user",
                    "content": src_text
                }
            ],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Exception in text summarization:", str(e))
        return str(e) # エラーが発生した場合はエラーメッセージを要約とする
    

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input('ファイル名を入力してください')

    with open(file_path,"r",encoding='utf-8') as f:
        content = f.read()

        response = convert_to_json(content)

        print(response)
        # ファイル名の拡張子を.jsonに変更
        json_file_path = file_path.split('.')[0] + '.json'

        # JSONデータをファイルに保存
        with open(json_file_path, "w", encoding='utf-8') as json_file:
            # エスケープ文字を改行に変換して表示
            json_data = json.loads(response)
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        print(f'変換されたデータを {json_file_path} に保存しました。')