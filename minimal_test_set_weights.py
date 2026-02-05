import nest
import numpy as np
import time
from line_profiler import profile
nest.SetKernelStatus({
                        "local_num_threads": 4,
                        # "local_num_threads": 24,
                     })

CUSTOM_MODEL = True
N_FOR = 4000
N_NEURONS = 10_000
if CUSTOM_MODEL:
    neuron_model_name="hill_tononi_neuron_nestml__with_stdp_tsodyks_Tartarini_synapse_nestml"
    nest.Install("CustomModels/target/ht_tso_stdp_module")
neurons=nest.Create(neuron_model_name if CUSTOM_MODEL else 'ht_neuron', N_NEURONS)
np.random.seed(42)
seed = np.random.randint(1, N_NEURONS+1)
pre = np.array([(x * seed) % N_NEURONS for x in range(N_FOR)])
pre = np.sort(pre)
post = np.array([(x * seed + 2) % N_NEURONS for x in range(N_FOR)])
# post = np.random.randint(1, N_NEURONS+1, N_FOR)
weights = np.random.uniform(0.001, 1, N_FOR)
for i in range(N_FOR):
    nest.Connect(
        neurons[pre[i]],
        neurons[post[i]],
        {'rule':'all_to_all'},
        {
            'synapse_model':'stdp_tsodyks_Tartarini_synapse_nestml__with_hill_tononi_neuron_nestml' if CUSTOM_MODEL else 'stdp_synapse',
            'weight':weights[i],
            'delay':1,
            'receptor_type':1
        }
    )


# N_FOR = 4000
# neurons=nest.Create('ht_neuron',10000)
# for i in range(N_FOR):
#     nest.Connect(neurons[i],neurons[i+100],{'rule':'all_to_all'},{'synapse_model':'stdp_synapse','weight':2,'delay':1,'receptor_type':1})
#     # nest.Connect(neurons[i],neurons[i+100],{'rule':'all_to_all'},{'synapse_model':'stdp_synapse','weight':i/10,'delay':1,'receptor_type':1})

# pre =np.arange(0,N_FOR)
# post=pre+100
# weights=pre/10

# start=time.time()
# conns=nest.GetConnections(source=neurons)
# end=time.time()
# print("Get connections:", end-start)

def new_test_set(pre,post,weights):
    t1=time.time()
    conns=nest.GetConnections(source=neurons[pre], custom=True)
    sources = conns['source']
    targets = conns['target']
    weight = conns['weight']
    t2=time.time()
    print('New time: ',t2-t1)
    return

@profile
def test_set(pre,post,weights, getConnCustom):
    conns=nest.GetConnections(source=neurons[pre], custom=getConnCustom)
    res = conns.get(custom=True) if not getConnCustom else conns
    sources = res['source']
    targets = res['target']
    # mask = np.isin(pre+1,sources)
    # saved_targ = post[mask]+1
    # index_mapping = {}
    # for index,value in enumerate(targets):
    #     if value in index_mapping:
    #         index_mapping[value].append(index)
    #     else:
    #         index_mapping[value] = [index]

    # found_index = np.empty_like(saved_targ, dtype=int)
    # for i, value in enumerate(saved_targ):
    #     idx = index_mapping[value].pop(0)
    #     found_index[idx] = i

    #print(idp,source[0], len(targ),len(ww[pre==idp]), len(found_index) )
    if getConnCustom:
        conns=nest.GetConnections(source=neurons[pre])
    np.random.seed(21)
    weights = np.random.uniform(0.001, 1, N_FOR)
    # conns=nest.GetConnections(source=neurons[pre], custom=getConnCustom)
    # res = conns.get(custom=True) if not getConnCustom else conns
    # new_weights = res['weight']
    # print("new", new_weights)
    conns=nest.GetConnections(source=neurons[pre], custom=False)
    # conns.set({'weight':weights})
    conns.set_weights(weights)  # [mask][found_index]
    print("Types", type(conns), type(conns.set_weights), type(weights))
    res = conns.get(custom=True) if not getConnCustom else conns
    old_weights = res['weight']
    print("old", old_weights)
    # equals = new_weights.tolist() == old_weights.tolist()
    # assert equals, "Weights were not correctly set!"

# a = time.time()
# test_set(pre,post,weights, getConnCustom=True)
# b = time.time()
# print("Total time:", b-a)
a = time.time()
test_set(pre,post,weights, getConnCustom=False)
b = time.time()
print("Total time false:", b-a)
# new_test_set(pre,post,weights)
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
