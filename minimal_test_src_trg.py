import nest
import numpy as np
import time
nest.SetKernelStatus({
                        "local_num_threads": 1,
                        # "local_num_threads": 24,
                     })
neurons=nest.Create('ht_neuron',15000)
for i in range(11000):
    nest.Connect(neurons[i],neurons[i+100],{'rule':'all_to_all'},{'synapse_model':'stdp_synapse','weight':i/10,'delay':1,'receptor_type':1})
nest.Simulate(300)
print("Connections created")


start=time.time()
conns=nest.GetConnections(source=neurons)
end=time.time()
print("Get connections:", end-start)

def test_set():
    for idp in (id_pyr.astype(int) + 1):
        #print(idp)
        conn = nest.GetConnections(neurons, custom=True) # node_collections[pop_name_full][idp-1])
        source = conn["source"] #nest.GetStatus(conn, 'source')
        targ = conn["target"] #nest.GetStatus(conn, 'target')
        ww = conn["weight"] #nest.GetStatus(conn, 'weight')
        mask = (pre==idp)
        saved_targ = post[mask]
        index_mapping ={}
        for index,value in enumerate(targ):
            if value in index_mapping:
                index_mapping[value].append(index)
            else:
                index_mapping[value] = [index]

        found_index = np.empty_like(saved_targ, dtype=int)
        for i, value in enumerate(saved_targ):
            idx = index_mapping[value].pop(0)
            found_index[idx] = i

        #print(idp,source[0], len(targ),len(ww[pre==idp]), len(found_index) )
        conn.set({'weight':ww[mask][found_index]})


def test_get():
    # run conns.get(custom=...) N times (half True, half False) and record timings
    N = 150  # choose an even number
    if N % 3 != 0:
        raise ValueError("N must be even")

    print(f"Running conns.get(custom=...) {N} times")
    times_really_custom = []
    times_custom = []
    times_false = []
    for i in range(N):
        really_custom = i < (N // 3)
        custom = i < (2 * N // 3)
        t0 = time.time()
        conns=nest.GetConnections(source=neurons, custom=really_custom)
        if not really_custom:
            conns.get(custom=custom)
        # print("python res", res)
        t1 = time.time()
        # print(f"Run {i+1}/{N} with custom={flag}:\t{t1 - t0} seconds")
        if really_custom:
            times_really_custom.append(t1 - t0)
        elif custom:
            times_custom.append(t1 - t0)
        else:
            times_false.append(t1 - t0)
        # print("type", type(res['source']))
        # assert len(res['source']) == len(res['target']), f"Mismatch in lengths of source {len(res['source'])} and target {len(res['target'])}"
        # assert all(res['source'][i] == res['target'][i]-100 for i in range(len(res['source']))), "Source and target values do not match expected pattern"
        # assert len(res['weight']) == len(res['source'])

    print("really custom avg:\t", sum(times_really_custom) / len(times_really_custom) if times_really_custom else float('nan'))
    print("custom avg:\t", sum(times_custom) / len(times_custom) if times_custom else float('nan'))
    print("non custom avg:\t", sum(times_false) / len(times_false) if times_false else float('nan'))
    # print(conns_sources)
    # print(conns_tagets)
    # assert all(conns_sources['source'][i] == neurons[i//100] for i in range(len(conns_sources['source'])))
    # print('queried ',len(conns.get(['source'])['source']), ' connections in: ', end-start,'ms')
    # print(np.unique(conns.get(['source'])['source']).shape)
    # print(np.unique(conns.get(['target'])['target']).shape)


test_get()
