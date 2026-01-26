import nest
import numpy as np
import time
nest.SetKernelStatus({
                        "local_num_threads": 1,
                        # "local_num_threads": 24,
                     })

N_FOR = 4000
neurons=nest.Create('ht_neuron',10000)
for i in range(N_FOR):
    nest.Connect(neurons[i],neurons[i+100],{'rule':'all_to_all'},{'synapse_model':'stdp_synapse','weight':2,'delay':1,'receptor_type':1})
    # nest.Connect(neurons[i],neurons[i+100],{'rule':'all_to_all'},{'synapse_model':'stdp_synapse','weight':i/10,'delay':1,'receptor_type':1})

pre =np.arange(0,N_FOR)
post=pre+100
weights=pre/10

# start=time.time()
# conns=nest.GetConnections(source=neurons)
# end=time.time()
# print("Get connections:", end-start)

"""
getConnections time:  0.03264188766479492
get status src time:  0.012678384780883789
get status trg time:  0.007352352142333984
0.050
0.025
"""
def new_test_set(pre,post,weights):
    t1=time.time()
    conns=nest.GetConnections(source=neurons[pre], custom=True)
    sources = conns['source']
    targets = conns['target']
    weight = conns['weight']
    t2=time.time()
    print('New time: ',t2-t1)
    return

def test_set(pre,post,weights):
    t1=time.time()
    conns=nest.GetConnections(source=neurons[pre])
    t2=time.time()
    res = conns.get(custom=True)
    sources = res['source']
    targets = res['target']
    t3=time.time()
    print('getConnections time: ',t2-t1)
    print('get time: ',t3-t2)
    print('global time', t3-t1)
    return
    t4=time.time()
    # print(targets)
    mask = np.isin(pre+1,sources)
    saved_targ = post[mask]+1
    index_mapping = {}
    for index,value in enumerate(targets):
        if value in index_mapping:
            index_mapping[value].append(index)
        else:
            index_mapping[value] = [index]
    t5=time.time()
    print('index mapping time: ',t5-t4)

    found_index = np.empty_like(saved_targ, dtype=int)
    for i, value in enumerate(saved_targ):
        idx = index_mapping[value].pop(0)
        found_index[idx] = i
    t6=time.time()
    print('found index time: ',t6-t5)

    print(weights.shape)
    print(weights[mask].shape)
    print(found_index.shape)
    #print(idp,source[0], len(targ),len(ww[pre==idp]), len(found_index) )
    conns.set({'weight':weights[mask][found_index]})
    t7=time.time()
    print('conns set time: ',t7-t6)

test_set(pre,post,weights)
new_test_set(pre,post,weights)
exit(1)
print("Connections created")

nest.Simulate(100)
print("Connections created")


start=time.time()
conns=nest.GetConnections(source=neurons)
end=time.time()
print(end-start)

# print(conns.sources)
# print(conns.sources())
# for con_s in conns.get("source"):  # sources():
#     n=1
    # print(con_s)
# print(dir(conns._datum[0]))
# conns_sources=conns.get(['source'])
# conns.print_full = True
# print(conns)
end2=time.time()
print(end2-end)
print(type(conns))
conns_res=conns.get(custom=True)
print('done',time.time()-end2)

print('sources:',conns_res['source'][:10])
print('targets:',conns_res['target'][:10])
print('weights:',conns_res['weight'][:10])
# print('conns:',conns)
