### header ###
import streamlit as st
from PIL import Image # 画像表示
import numpy as np
import matplotlib.pyplot as plt
import HIRAU

"""
### ~量子技術で命を救う~
# 地域住民避難誘導アプリ HIRAU
"""
# st.title('避難誘導アプリ HIRAU')

param_column, logo_column = st.columns(2)

img = Image.open('HIRAU_logo.png')
logo_column.image(img, caption='HIRAU v3.2', use_column_width=True)

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
if param_column.checkbox('量子計算機で加速'):
    token = param_column.text_input('D-Wave トークン (空欄:OpenJij)',value='', type='password')

# K = 3 # ひらわない経路の候補数
# nSample = 3 # OpenJijの試行回数
# distance = 0.0050 # 地図範囲
# aspect_ratio = 1.3

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
    st.session_state.display_route = False
fig_left_column.pyplot(st.session_state.fig_map, caption='map', use_column_width=True)

##### Run button #####
button_main = fig_right_column.button('誘導経路探索')
if button_main:
    st.session_state.fig_route, st.session_state.ax_route, st.session_state.answer_list = HIRAU.main(st.session_state.G, S, M, E, st.session_state.route_list, st.session_state.nodes_for_plot, st.session_state.nodes_color_list, token)
    st.session_state.display_route = True

if 'display_route' not in st.session_state: 
    st.session_state.display_route = False

if st.session_state.display_route:
    fig_right_column.pyplot(st.session_state.fig_route, caption='route', use_column_width=True)
    st.write(f'黄線：ひらう経路')
    st.write(f'青線：ひらわない経路')



st.write(f'赤：リーダー（{S}人）')
st.write(f'緑：避難弱者（{M}人）')
st.write(f'白：避難所（{E}カ所）')


if st.session_state.display_route:
    indiv_left_column, indiv_right_column = st.columns(2)

    iLeader = indiv_left_column.selectbox(
        '表示するリーダー番号を選択して下さい。',
        list(range(1,S+1))
    )
    fig_indiv, ax_indiv = HIRAU.individual(iLeader-1, st.session_state.G, S, M, E, st.session_state.answer_list, st.session_state.route_list, st.session_state.nodes_for_plot, st.session_state.nodes_color_list)
    indiv_right_column.pyplot(fig_indiv, caption='map', use_column_width=True)
