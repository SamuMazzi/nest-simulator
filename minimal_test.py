import time
import nest
import os
import numpy as np
# import fastconn

print("ciao", os.environ.get("PYTHONPATH"))

nest.set_verbosity("M_ALL")
nest.ResetKernel()
dt=.1
nest.SetKernelStatus({
                        "local_num_threads": 4,
                        "print_time" : True,
	                    "rng_seed": 12345,
	                    "resolution": dt,
                        
                        })

"""
With devices: (no spike generators/recorders)
1000 -> 0.296s (3.09s)
2000 -> 1.187s (12.6s)
3000 -> 2.703s (26.53s)
4000 -> 4.904s (48.56s)
5000 -> 7.817s (80.29s)
"""
"""
Original (kind of):
GetStatus command time: 0.002809286117553711 seconds
sps time: 0.09752345085144043 seconds
sr result time: 0.8054587841033936 seconds
spp result time: 0.10624837875366211 seconds
GetStatus result time: 1.009230613708496 seconds
Restructure data time: 0.0030670166015625 seconds
Output formatting time: 1.430511474609375e-06 seconds
Conns.get: 1.0200791358947754 seconds
GetConnections time: 0.08451318740844727 seconds
Simulation time: 1.7574677467346191 seconds
"""
# TODO: Try to benchmark without devices too
# TODO: Then try with spikes

start_t = time.time()
neurons=nest.Create('ht_neuron',500)
nest.Connect(neurons,neurons,{'rule':'all_to_all'},
             {'synapse_model':'stdp_synapse','weight':1,'delay':1,'receptor_type':1})
# sg=nest.Create('spike_generator',{'spike_times':[10,20,30,40]})
# nest.Connect(sg,neurons[:10],{'rule':'all_to_all'},
#              {'synapse_model':'static_synapse','weight':5,'delay':1,'receptor_type':1})
# sr=nest.Create('spike_recorder')
# nest.Connect(neurons,sr)
start_get_conn = time.time()
conns = nest.GetConnections(source=neurons, synapse_model='stdp_synapse')
# res = fastconn.get_connections({})
# print(len(res["source"]))
# print(conns)
end_get_conn = time.time()
# nest.Simulate(100)
# a = conns.sources()
conns.get("source")
c = time.time()
# print(len(np.unique(conns.get(["target"])["target"])))
# print(conns.get(["source"])["source"])
# print(conns)
# print(nest.GetStatus(sr,'events'))
end_t = time.time()
print("Conns.get:", c - end_get_conn, "seconds")
print("GetConnections time:", end_get_conn - start_get_conn, "seconds")
print("Simulation time:", end_t - start_t, "seconds")
