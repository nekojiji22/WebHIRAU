### header ###
import streamlit as st
from PIL import Image # 画像表示
import numpy as np
import matplotlib.pyplot as plt
# import osmnx as ox
# import geocoder as geo
# import networkx as nx
# from openjij import SQASampler
# from dwave.system import LeapHybridSampler #,DWaveSampler, EmbeddingComposite
import HIRAU

"""
### ~量子技術で命を救う~
# 地域住民避難誘導アプリ HIRAU
"""
# st.title('避難誘導アプリ HIRAU')

param_column, logo_column = st.columns(2)

img = Image.open('HIRAU_logo.png')
logo_column.image(img, caption='HIRAU v3.0', use_column_width=True)

### パラメータ入力 ###
geo_address = param_column.text_input('住所入力',value='宮城県仙台市青葉区')

# リーダーの数
S = param_column.number_input(
    'リーダーの人数(1~20)',
    min_value = 1,
    max_value = 20,
    value = 10
)

# 避難弱者の数
M = param_column.number_input(
    f'避難弱者の数(1~{S-1})',
    min_value = 1,
    max_value = S-1,
    value = int(S/2)
)

# 避難所の数
E = param_column.number_input(
    '避難所の数(1~10)',
    min_value = 1,
    max_value = 10,
    value = 4
)


token = '' # 空欄だとOpenJij。正しいのを入れるとD-Wave Hybrid Solver

K = 3 # ひらわない経路の候補数
nSample = 3 # OpenJijの試行回数
distance = 0.0050 # 地図範囲
aspect_ratio = 1.3

route_list = []
nodes_for_plot = []
nodes_color_list = []

fig_left_column, fig_right_column = st.columns(2)


# if 'button_map' not in st.session_state: 
#     st.session_state.button_map = False #countがsession_stateに追加されていない場合，0で初期化

if 'fig_map' not in st.session_state: 
    st.session_state.fig_map, ax_map, st.session_state.G, st.session_state.route_list, st.session_state.nodes_for_plot, st.session_state.nodes_color_list = HIRAU.map(geo_address, S, M, E)

##### Auto Run #####
button_map = fig_left_column.button('配置リセット')
if button_map:
    st.session_state.fig_map, ax_map, st.session_state.G, st.session_state.route_list, st.session_state.nodes_for_plot, st.session_state.nodes_color_list = HIRAU.map(geo_address, S, M, E)
fig_left_column.pyplot(st.session_state.fig_map, caption='map', use_column_width=True)

##### Run button #####
button_main = fig_right_column.button('誘導経路探索')
if button_main:
    fig_route, ax_route = HIRAU.main(st.session_state.G, S, M, E, st.session_state.route_list, st.session_state.nodes_for_plot, st.session_state.nodes_color_list, token)
    fig_right_column.pyplot(fig_route, caption='route', use_column_width=True)
    st.write(f'黄線：ひらう経路')
    st.write(f'青線：ひらわない経路')



st.write(f'赤：リーダー（{S}人）')
st.write(f'緑：避難弱者（{M}人）')
st.write(f'白：避難所（{E}カ所）')


