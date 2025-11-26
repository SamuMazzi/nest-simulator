import nest
import numpy as np
import time
nest.SetKernelStatus({
                        "local_num_threads": 1,
                        # "local_num_threads": 24,
                     })
neurons=nest.Create('ht_neuron',10000)
for i in range(4000):
    nest.Connect(neurons[i],neurons[i+100],{'rule':'all_to_all'},{'synapse_model':'stdp_synapse','weight':i/10,'delay':1,'receptor_type':1})
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
# run conns.get(custom=...) N times (half True, half False) and record timings
N = 100  # choose an even number
if N % 2 != 0:
    raise ValueError("N must be even")

print(f"Running conns.get(custom=...) {N} times (half True, half False)")
times_true = []
times_false = []
for i in range(N):
    flag = i < (N // 2)
    t0 = time.time()
    res = conns.get(custom=flag)
    t1 = time.time()
    # print(f"Run {i+1}/{N} with custom={flag}:\t{t1 - t0} seconds")
    if flag:
        times_true.append(t1 - t0)
    else:
        times_false.append(t1 - t0)
    assert len(res['source']) == len(res['target']), f"Mismatch in lengths of source {len(res['source'])} and target {len(res['target'])}"
    assert all(res['source'][i] == res['target'][i]-100 for i in range(len(res['source']))), "Source and target values do not match expected pattern"
    assert len(res['weight']) == len(res['source'])

print("true avg:\t", sum(times_true) / len(times_true) if times_true else float('nan'))
print("false avg:\t", sum(times_false) / len(times_false) if times_false else float('nan'))
# print(conns_sources)
# print(conns_tagets)
# assert all(conns_sources['source'][i] == neurons[i//100] for i in range(len(conns_sources['source'])))
# print('queried ',len(conns.get(['source'])['source']), ' connections in: ', end-start,'ms')
# print(np.unique(conns.get(['source'])['source']).shape)
# print(np.unique(conns.get(['target'])['target']).shape)
