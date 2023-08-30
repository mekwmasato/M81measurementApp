from math import sqrt
from time import sleep


import keyboard
import PySimpleGUI as sg
from lakeshore import SSMSystem  # M81のこと

import csv
import datetime
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

is_connected = False

Header = ["距離[mm]", "R[V]", "theta[θ]"]
Data = []

distance = 50
step = 2


def ConnectM81():
    M81 = SSMSystem() #引数なし:USB,Serial接続
    return 0

def SetupM81(fq,cr):
    S1 = M81.get_source_module(1) #ソースモジュール
    M1 = M81.get_measure_module(1) #計測モジュール
    S1.set_shape('SINUSOID') #sin波のこと
    S1.set_frequency(fq) #周波数[Hz]
    S1.set_current_amplitude(cr) #電流[A]
    S1.set_current_offset(0)
    S1.configure_i_range(0, max_ac_level=0.1) #Range設定(autoを使うか、max_level,max_ac_level,max_dc_level)どれか一つ指定
    S1.set_cmr_source('INTernal') #CMRのソースを設定
    S1.enable_cmr() #CMRを有効化
    #advanced setting
    S1.use_ac_coupling() #カップリングをACに設定
    M1.setup_lock_in_measurement('S1', 0.1) #S1の周波数を参照信号にし、timeconstantを100msに設定
    return 0



Titlesize = (20,1)
Textsize = (10,1)
TitleFont = ("meiryo", 30)
Font = ("meiryo", 15)


layout = [
    [sg.Text("M81計測App", size=Titlesize, font=TitleFont, justification='center'), ],
    [sg.Text("M81に接続", size=Textsize, font=Font), sg.Button("接続", font=Font, key="Connect")],
    [sg.Text("周波数[Hz]:", size=Textsize, font=Font), sg.InputText(font=Font, size=Textsize, default_text="1000", key="-FQ-")],
    [sg.Text("電流[A]:", size=Textsize, font=Font),  sg.InputText(font=Font, size=Textsize, default_text="0.01", key="-CR-")],
    [sg.Text("初期位置[mm]:", size=Textsize, font=Font),  sg.InputText(font=Font, size=Textsize, default_text="50", key="-DT-")],
    [sg.Text("ステップ[mm]:", size=Textsize, font=Font),  sg.InputText(font=Font, size=Textsize, default_text="2", key="-ST-")],
    [sg.Button("Set", disabled=not is_connected, font=Font, key="Setup")],
    [sg.Button("ON", disabled=not is_connected, font=Font, key="ON"), sg.Button("OFF(CSVに保存)", disabled=not is_connected, font=Font, key="OFF")],
    [sg.Text("Aで計測,Nで一つ消す", font=Font)],

    [sg.Table(Data, headings=Header, auto_size_columns=True, key='-TABLE-')],
]



#layout = [sg.Column(layout_settings), sg.Column(layout_canvas)]


window = sg.Window("M81ロックイン計測", layout, return_keyboard_events=True)




while True:
    event, value = window.read()


    if event == "Connect": #接続ボタン押したとき
        print(f"event:{event}")    
        try:
            ConnectM81()
            is_connected = True #接続状態を更新
            sg.Popup("接続されました", auto_close=True, auto_close_duration=1)
        except Exception as e: #接続できなかったとき
            sg.PopupError(f'エラー:{e}')
    

    if event == "Setup":
        print(f"event:{event}")    
        try:
            frequency = int(value["-FQ-"])
            current   = float(value["-CR-"])
            distance  = int(value["-DT-"])
            step = int(value["-ST-"])
            SetupM81(frequency, current)

        except ValueError:
            sg.PopupError("数値を入力してください")
        except Exception:
            sg.PopupError(f'機器を接続してください')
    
    
    if event == "ON":
        print(f"event:{event}")    
        S1.enable() #S1を起動
        sleep(1.5)
        sg.Popup("起動中(wait:1.5[s])", auto_close=True, auto_close_duration=2)
        Data = ["distance[mm]", "R[V]", "theta[θ]"]


    if event == "OFF":
        print(f"event:{event}")    
        print("ソースモジュールを停止")    
        S1.disable() #S1を停止
        print(Data)

        #csv setting
        now = datetime.datetime.today()
        hourstr = "_" + now.strftime("%H%M%S")
        filename = "record_" + now.strftime("%Y%m%d") + hourstr + ".csv"
        os.makedirs('M81_CSVrecords',exist_ok=True)
        #create CSV
        print("create csv.")
        with open(os.path.join('M81_CSVrecords',filename), 'a', newline= '') as f:
            writer = csv.writer(f)
            writer.writerow(["距離[mm]","R[V]","theta[Θ]"])
            writer.writerows(Data)
            print("")
        Data.clear()
        print(Data)
        # Table ウィジェットを更新
        window['-TABLE-'].update(values=Data)


    if event == "a": #データを保存
        print(f"event:{event}")    
        try:
            lock_in_magnitude = M1.get_lock_in_r() #LockinモードのRを取得
            lock_in_theta = M1.get_lock_in_theta() 
            d = [distance, lock_in_magnitude, lock_in_theta]
            Data.append(d)
            print(f"append:{d},")
            distance = distance + step
            # Table ウィジェットを更新
            window['-TABLE-'].update(values=Data)

        except Exception:
            sg.PopupError(f'機器を接続し状態:ONにしてください')


    if event == "b": #データを保存test
        print(f"event:{event}")    
        try:
            d = [distance,2,3]
            Data.append(d)
            distance = distance + step
            # Table ウィジェットを更新
            window['-TABLE-'].update(values=Data)
        except Exception:
            sg.PopupError(f'機器を接続し状態:ONにしてください')


    if event == "n": #データを一つ消去
        print(f"event:{event}")    
        try:
            Data.pop()
            distance = distance - step
            # Table ウィジェットを更新
            window['-TABLE-'].update(values=Data)
        except Exception:
            sg.PopupError(f'データがありません')


    if event == None:
        break


window.close()