
import os
import sys
import json
import requests
from dotenv import load_dotenv
import openai
import json


# 環境変数の読み込み
load_dotenv()
PROMPT_FILE = os.environ["PROMPT_FILE"]
OPEN_API_KEY = os.environ["OPEN_API_KEY"]
openai.api_key = OPEN_API_KEY

# メッセージのテンプレート
MESSAGE_TEMPLATE = ""
MESSAGE_PARAMS = {
    'keyword' : "あなたは聞き分けのプロです。これから与えられた音声テキストをJSON形式で正規化します。",
    'additional_info': "最適な変換を行えるために、最大限頑張りましょう。大丈夫、あなたは天才です。"
}

def load_template():
    try:
        with open(PROMPT_FILE,"r",encoding='utf-8') as f:
            return f.read()

    except FileNotFoundError:
        print("テンプレートファイルが存在しません")
        raise Exception("TemplateFileNotfound")

def to_json(json_data,file_path):
        # ファイル名の拡張子を.jsonに変更
        file_name, file_extension = os.path.splitext(file_path)
        json_file_path = file_name + '.json'        
        # JSONデータをファイルに保存
        with open(json_file_path, "w", encoding='utf-8') as json_file:
            # エスケープ文字を改行に変換して表示
            json_data = json.loads(response)
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        return json_file_path

def convert_to_json(src_text):

    MESSAGE_TEMPLATE = load_template()

    try:
        system_message_content = MESSAGE_TEMPLATE.format(**MESSAGE_PARAMS)
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
        content = content.replace("まる","。")
        content = content.replace("丸","。")
        content = content.replace("マル","。")
        #print(content)

        response = convert_to_json(content)
        print(response)

        json_file_path = to_json(response, file_path)
        print(f'変換されたデータを {json_file_path} に保存しました。')

