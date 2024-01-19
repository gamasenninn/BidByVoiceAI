from gspread_dataframe import get_as_dataframe, set_with_dataframe
import gspread
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_JSON = os.environ["SECRET_JSON"]
SPREADSHEET_KEY = os.environ["SPREADSHEET_KEY"]

#---------Googleスプレッドシートの事前設定 ---------------------

#ServiceAccountCredentials：Googleの各サービスへアクセスできるservice変数を生成します。
from oauth2client.service_account import ServiceAccountCredentials

#2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

#認証情報設定
#ダウンロードしたjsonファイル名をクレデンシャル変数に設定
credentials = ServiceAccountCredentials.from_json_keyfile_name(SECRET_JSON, scope)

#OAuth2の資格情報を使用してGoogle APIにログインします。
gc = gspread.authorize(credentials)

#----------------- 売約シート(店売)の読み込み・整理 ---------------------
workbook = gc.open_by_key(SPREADSHEET_KEY)
worksheet = workbook.worksheet('出品データ')
gs_df = get_as_dataframe(worksheet,evaluate_formulas=True)

# 空白行を削除
gs_df.dropna(how='all', inplace=True)

# 'Unnamed:' で始まるカラムを識別して削除
gs_df = gs_df.loc[:, ~gs_df.columns.str.contains('^Unnamed')]

print(gs_df.head)


