import PySimpleGUI as sg
import subprocess
import threading
import os
import json

# スレッド停止フラグ
stop_thread = False
process_status = None

# コマンド定義ファイル読み込み
def load_commands(filename):
    with open(filename, 'r', encoding='utf8') as file:
        return json.load(file)

commands_details = load_commands('sg_launcher_config.json')

# コマンドを非同期で実行する関数
def run_command(command, parameters, window,wait_sw=True):
    global stop_thread
    try:
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = "1"  # Pythonぷろせすにはこれが必要
        command_list = command.split() + parameters.split()
        process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE,  text=True, bufsize=1, universal_newlines=True,env=env)

        if wait_sw:
            while True:
                if stop_thread:
                    process.terminate()
                    window.write_event_value('-THREAD_STOPPED-', 'スレッドが停止しました')
                    stop_thread = False
                    break
                output = process.stdout.readline()
                if output:
                    print(output,end='' )
                    window.write_event_value('-COMMAND_OUTPUT-', output.strip())
                
                elif process.poll() is not None:
                    error = process.stderr.read()
                    if error:
                        print("エラー内容",error)
                        window.write_event_value('-COMMAND_ERROR-', error)
                        raise Exception("呼出先でエラーです。")
                    elif process.poll() is not None:
                        break


    except Exception as e:
        print(e)
        window.write_event_value('-COMMAND_ERROR-', f'エラー: {e}')
    finally:
        # スレッドが停止したことを通知
        #window.write_event_value('-THREAD_STOPPED-', 'スレッドが停止しました')
        window['-START-'].update(disabled=False)
        window['-STOP-'].update(disabled=True)        

# GUIのレイアウトを定義
initial_command = list(commands_details.values())[0]
initial_command_body = initial_command['command']
initial_command_params = initial_command['params']
initial_command_description = initial_command['description']

# 各行のレイアウトをカラムとして定義
command_column = sg.Column([
    [sg.Text('コマンド:', size=(12, 1)), sg.Combo(list(commands_details.keys()), default_value=list(commands_details.keys())[0], key='-COMMAND-', readonly=True,enable_events=True)]
])
command_body_column = sg.Column([
    [sg.Text('コマンド実体:', size=(12, 1)), sg.InputText(initial_command_body,key='-COMMAND_BODY-', readonly=True, size=(25, 1))]
])
params_column = sg.Column([
    [sg.Text('パラメーター:', size=(12, 1)), sg.Multiline(initial_command_params,key='-PARAMS-', size=(50, 3))]
])

layout = [
    [command_column],
    [command_body_column],
    [params_column],
    [sg.Text('説明:'), sg.InputText(initial_command_description, key='-DESCRIPTION-', readonly=True, size=(75, 1))],
    [sg.Text('コマンドの出力:')],
    [sg.Multiline(default_text='', size=(80, 20), key='-OUTPUT-', autoscroll=True, disabled=True)],
    [sg.Button('開始', key='-START-'), sg.Button('停止', key='-STOP-', disabled=True), sg.Button('終了', key='-END-')]
]

# ウィンドウの作成
window = sg.Window('非同期コマンド実行', layout)

# イベントループ
while True:
    event, values = window.read(timeout=100)
    #print(event,values)
    
    if event == sg.WIN_CLOSED or event == '-END-':
        break

    if event == '-COMMAND-':
        selected_command = commands_details[values['-COMMAND-']]
        #print(selected_command)
        window['-COMMAND_BODY-'].update(selected_command['command'])
        window['-PARAMS-'].update(selected_command['params'])
        window['-DESCRIPTION-'].update(selected_command['description'])
        params_allow_input = selected_command.get('params_allow_input', True)  # デフォルトはTrue
        print(params_allow_input)
        window['-PARAMS-'].update(disabled=not params_allow_input)        

    if event == '-START-':
        # 開始ボタン: 無効, 停止ボタン: 有効
        window['-START-'].update(disabled=True)
        window['-STOP-'].update(disabled=False)        
        selected_command_name = values['-COMMAND-']
        selected_command = commands_details[selected_command_name]['command']
        user_params = values['-PARAMS-']  # ユーザーが入力したパラメータ
        should_wait = commands_details[selected_command_name].get('wait', True)  # waitキーがなければTrueをデフォルト値とする
        # 'params_allow_input' に基づいてパラメータ入力フィールドの有効/無効を切り替える
        # スレッドを開始する
        threading.Thread(target=run_command, args=(selected_command, user_params, window,should_wait), daemon=True).start()
        window['-OUTPUT-'].update(f'コマンドを投入しました{selected_command_name}....\n')

    elif event == '-STOP-':
        stop_thread = True

    if event == '-COMMAND_OUTPUT-':
        # コマンドの出力をマルチラインに追加
        window['-OUTPUT-'].update(values[event] + '\n', append=True, autoscroll=True)

    if event == '-COMMAND_ERROR-':
        # エラーをポップアップ表示
        sg.PopupError(values[event])

    if event == '-THREAD_STOPPED-':
        # スレッドが停止したとき、ボタンの状態を元に戻す
        window['-START-'].update(disabled=False)
        window['-STOP-'].update(disabled=True)
        # スレッドが停止したことを示すメッセージを出力
        window['-OUTPUT-'].update(values[event] + '\n', append=True, autoscroll=True)


# 終了処理
window.close()
