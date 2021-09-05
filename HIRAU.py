##################
### HIRAU v3.0 ###
##################

### header ###
import numpy as np
import matplotlib.pyplot as plt
import osmnx as ox
import geocoder as geo
import networkx as nx
from openjij import SQASampler
from dwave.system import LeapHybridSampler #,DWaveSampler, EmbeddingComposite

K = 3 # ひらわない経路の候補数
nSample = 3 # OpenJijの試行回数
distance = 0.0050 # 地図範囲
aspect_ratio = 1.3

### functions ###
def toDict(full):
  dict = {}
  for i in range(full.shape[0]):
    for j in range(full.shape[1]):
      if full[i][j] != 0.0:
        dict[(i,j)] = full[i][j]
  return dict

### 道路rを番号で定義 ###
def roadDict(route_list):
  road_dict = {}
  r = 0
  for route in route_list:
    for l in range(len(route)-1):
      road = ( min(route[l],route[l+1]), max(route[l],route[l+1]) )
      if road not in road_dict.keys():
        road_dict[road] = r
        r += 1
  return road_dict

### 経路の長さを返す関数 ###
def len_route(G,route):
  L = 0.0
  for l in range(len(route)-1):
    i = route[l]
    j = route[l+1]
    L += G[i][j][0]['length']
  return L

def extend_used_route(G,route,extend_factor):
  for k in range(len(route)-1):
    i = route[k]
    j = route[k+1]
    G[i][j][0]['length'] *= extend_factor

def restore_used_route(G,route,extend_factor):
  for k in range(len(route)-1):
    i = route[k]
    j = route[k+1]
    G[i][j][0]['length'] /= extend_factor

def x_QA(Qdict, nSample, token):
  if token == "":
    OJij_sampler = SQASampler()
    sampleset = OJij_sampler.sample_qubo(Qdict, num_reads = nSample)
    sortedset = sorted(sampleset.record, key=lambda x: x[1])
    answer = sortedset[0][0]
  else:
    print("Submitted to D-Wave!")
    endpoint = 'https://cloud.dwavesys.com/sapi/'
    Hy_sampler = LeapHybridSampler(solver='hybrid_binary_quadratic_model_version2', token=token, endpoint=endpoint)
    sampleset = Hy_sampler.sample_qubo(Qdict)
    # DW_sampler = DWaveSampler(solver='Advantage_system1.1', token=token, endpoint=endpoint)
    # sampler = EmbeddingComposite(DW_sampler)
    # sampleset = DW_sampler.sample_qubo(Qdict, num_reads = nSample)
    answer = sampleset.record[0][0]
    print("Returned from D-Wave!")
  return answer

def geometry(geo_address,distance,aspect_ratio):
  geo_location = geo.osm(geo_address)
  lat = geo_location.latlng[0]
  lng = geo_location.latlng[1]
  mr = {
      'north': lat + distance, 'south': lat - distance,
      'east': lng + distance*aspect_ratio, 'west': lng - distance*aspect_ratio
  }
  G = ox.graph_from_bbox(mr['north'], mr['south'], mr['east'], mr['west'], network_type='drive')
  G = ox.utils_graph.remove_isolated_nodes(G) # 孤立ノードを除くらしい。が、効果は見られない？
  ### node抽出 ###
  node_list_all = []
  for key in G.nodes(data=False):
      node_list_all.append(key)
  nNodes_all = len(node_list_all)
  # 繋がっていないノードを除く（ちょっと遅いけれど）
  node_list = []
  for i in range(nNodes_all):
    test_node = node_list_all[i]
    nConnected = 0
    for j in range(nNodes_all):
      nConnected += nx.has_path(G,test_node,node_list_all[j]) #目的地までのパスがある(1)かない(0)か
    if nConnected > nNodes_all/2:
      node_list.append(test_node)
  return G, node_list


#####################
def map(geo_address, S, M, E):
  ### 経路インデックスを返す関数 ###
  def x_indx(k,s):
    i = k + s*Ns
    return i
  #----ここからメイン---------------------------#
  Nh = M
  Ne = E * K
  Ns = Nh + Ne
  N = S * Ns
  print("QUBOサイズ = ",N)
  ### 地図情報 ###
  G, node_list = geometry(geo_address,distance,aspect_ratio)
  nNodes = len(node_list)
  ### 目的地をランダムに決める ###
  flag = 0
  nTry = 0
  while flag == 0:
    flag = 1
    nTry += 1
    perm_list = np.random.permutation(node_list).tolist()
    end_list = perm_list[:E]
    leader_list = perm_list[E:E+S]
    hirau_list = perm_list[E+S:E+S+M]
    for s in range(S):
      node = leader_list[s]
      for e in range(E):
        flag *= nx.has_path(G,node,end_list[e]) #目的地までのパスがある(1)かない(0)か
      if flag == 1:
        for m in range(M):
          flag *= nx.has_path(G,node,hirau_list[m]) #目的地までのパスがある(1)かない(0)か
    if flag == 1:
      for m in range(M):
        node = hirau_list[m]
        for e in range(E):
          flag *= nx.has_path(G,node,end_list[e]) #目的地までのパスがある(1)かない(0)か
  ### 目的地表示 ###
  temp_list = end_list + leader_list + hirau_list
  nodes_for_plot = [ [temp_list[i]] for i in range(len(temp_list)) ]
  nodes_color_list = ['w']*len(end_list) + ['r']*len(leader_list) + ['g']*len(hirau_list)
  fig, ax = ox.plot_graph_routes(G, nodes_for_plot, route_colors=nodes_color_list, route_alpha=1.0)
  ### 経路生成 ###
  # 経路生成 M-E
  MEroute_list = []
  for m in range(M):
    len_min = 1.0e10 # なんかデカい数
    for e in range(E):
      temp_route = nx.shortest_path(G, hirau_list[m], end_list[e], 'length') # M-E
      if len_route(G,temp_route) < len_min: # Eのうち一番近いもの
        shortest_route = temp_route
        len_min = len_route(G,shortest_route)
    MEroute_list.append(shortest_route)
  # 経路生成 S-M-EとS-E
  route_list = []
  route_penalty_factor = 2.0
  for s in range(S):
    for m in range(M):
      temp_route = nx.shortest_path(G, leader_list[s], hirau_list[m], 'length') # S-M
      # S-MとM-Eをつなげる
      route_list.append(temp_route + MEroute_list[m][1:]) # S-M終点とM-E始点の被り注意
    for e in range(E):
      for k in range(K):
        temp_route = nx.shortest_path(G, leader_list[s], end_list[e], 'length') # S-E
        route_list.append(temp_route)
        extend_used_route(G,temp_route,route_penalty_factor)
      for k in range(K):
        restore_used_route(G,route_list[-k-1],route_penalty_factor) # 一番後ろの要素は [-1]
  return fig, ax, G, route_list, nodes_for_plot, nodes_color_list

##########
def main(G, S, M, E, route_list, nodes_for_plot, nodes_color_list, token):
  ### 経路インデックスを返す関数 ###
  def x_indx(k,s):
    i = k + s*Ns
    return i
  ### 制約違反数を返す関数 ###
  def violation(answerset):
    pena = 0
    for s in range(S):
      pena = pena + (sum(answerset[0+s*Ns:Ns+s*Ns]) - 1)**2
    for m in range(M):
      pena = pena + (sum(answerset[m::Ns]) - 1)**2
    return pena
  #----ここからメイン---------------------------#
  Nh = M
  Ne = E * K
  Ns = Nh + Ne
  N = S * Ns
  print("QUBOサイズ = ",N)
  ### 罰金 ###
  Q_pen1 = np.zeros(N**2).reshape(N,N)
  for s in range(S):
    for k1 in range(Ns):
      for k2 in range(Ns):
        Q_pen1[x_indx(k1,s),x_indx(k2,s)] += 1.0
        if k1 == k2:
          Q_pen1[x_indx(k1,s),x_indx(k2,s)] -= 2.0
  ### 罰金2 ###
  Q_pen2 = np.zeros(N**2).reshape(N,N)
  for m in range(M):
    for s1 in range(S):
      for s2 in range(S):
        Q_pen2[x_indx(m,s1),x_indx(m,s2)] += 1.0
        if s1 == s2:
          Q_pen2[x_indx(m,s1),x_indx(m,s2)] -= 2.0
  ### 総経路最短化 ###
  Q_len = np.zeros(N**2).reshape(N,N)
  len_ave = sum( len_route(G,route_list[i]) for i in range(N) )/N
  for i in range(N):
    Q_len[i,i] = (len_route(G,route_list[i])-0.5*len_ave)/len_ave
  # Cを作ろう
  road_dict = roadDict(route_list)
  C = np.zeros(N*len(road_dict)).reshape(N,len(road_dict))
  #D = np.zeros(N*len(road_dict)).reshape(N,len(road_dict))
  for k in range(N):
    route = route_list[k]
    for j in range(len(road_dict)):
      for l in range(len(route)-1):
        r = road_dict[( min(route[l],route[l+1]), max(route[l],route[l+1]) )]
        C[k,r] = +1/len(route)
        # if route[l] < route[l+1]:
        #   D[k,r] = +1/len(route)
        # else:
        #   D[k,r] = -1/len(route)
  Q_jam = np.dot(C,C.T)
  for i in range(N):
    Q_jam[i,i] = 0.0
  
  ### 制約条件を満たすまで、QA５回トライ ###
  coeff = 1.0
  iter_max = 5
  for i in range(iter_max):
    ### QUBO行列合成 ###
    # 係数は適宜調整すること！
    Qdict = toDict( coeff*Q_pen1 + coeff*Q_pen2 + 1.0*Q_len + 1.0*Q_jam )
    ### run QA ###
    answer = x_QA(Qdict, nSample, token)
    iflag = violation(answer)
    if iflag == 0:
      break
    else:
      coeff = coeff * 1.1
      print("failed",i,iflag)

  ### 結果表示 ###
  answer_route_list = []
  answer_color_list = []
  answer_list = np.where(answer == 1)
  for i in answer_list[0]:
    answer_route_list.append(route_list[i])
    if i%Ns < M:
      answer_color_list.append('y') # ひらう経路の色
    else:
      answer_color_list.append('b') # ひらわない経路の色
  color_list = answer_color_list + nodes_color_list
  fig, ax = ox.plot_graph_routes(G, answer_route_list + nodes_for_plot, route_colors=color_list, route_alpha=0.7)
  #### 結果確認 ###
  total_length = 0.0
  for i in range( len(answer_list[0]) ):
    total_length += len_route(G,answer_route_list[i])
  print("制約違反数", violation(answer), "　リーダー数", S, "　答えの経路数", sum(answer) )
  print("答えの平均距離/候補の平均距離", (total_length/sum(answer))/len_ave )
  return fig, ax
#############


