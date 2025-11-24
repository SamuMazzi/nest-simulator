#include <Python.h>

// Standard C++ includes (Essential for std::vector, std::string)
#include <vector>
#include <string>
#include <unordered_set>
#include <iostream>
#include <omp.h> // OpenMP for parallel speed

// NEST Includes
#include "kernel_manager.h"
#include "connection_manager.h"
#include "connection.h"
#include "dictutils.h"
#include "model.h"
#include "model_manager.h"
#include "nest_types.h" // REQUIRED: Defines the 'index' type used in your code

using namespace nest;

//
// Utility: convert Python list → std::unordered_set<long>
// Returns empty set if pyList is None.
//
std::unordered_set<long> pylist_to_set(PyObject* obj)
{
    std::unordered_set<long> result;

    if (!obj || obj == Py_None)
        return result;

    Py_ssize_t n = PyList_Size(obj);
    result.reserve(n);

    for (Py_ssize_t i = 0; i < n; ++i)
    {
        PyObject* item = PyList_GetItem(obj, i);
        long val = PyLong_AsLong(item);
        result.insert(val);
    }

    return result;
}


//
// fastconn.get_connections(filter_dict)
//
// filter_dict = {
//   "sources": [gid...],
//   "targets": [gid...],
//   "synapse_model": "stdp_synapse",
//   "min_weight": float,
//   "max_weight": float,
//   "min_delay": float,
//   "max_delay": float
// }
//
// All fields are optional.
// Returns a dict with arrays ("source","target","weight","delay").
//
static PyObject* fast_get_connections(PyObject*, PyObject* args)
{
    PyObject* filter_dict;

    if (!PyArg_ParseTuple(args, "O", &filter_dict))
        return nullptr;

    if (!PyDict_Check(filter_dict)) {
        PyErr_SetString(PyExc_TypeError, "Expected a dict");
        return nullptr;
    }

    // --- Extract filters ---
    PyObject* py_sources = PyDict_GetItemString(filter_dict, "sources");
    PyObject* py_targets = PyDict_GetItemString(filter_dict, "targets");
    PyObject* py_synmodel = PyDict_GetItemString(filter_dict, "synapse_model");

    PyObject* py_min_weight = PyDict_GetItemString(filter_dict, "min_weight");
    PyObject* py_max_weight = PyDict_GetItemString(filter_dict, "max_weight");
    PyObject* py_min_delay = PyDict_GetItemString(filter_dict, "min_delay");
    PyObject* py_max_delay = PyDict_GetItemString(filter_dict, "max_delay");

    auto source_filter = pylist_to_set(py_sources);
    auto target_filter = pylist_to_set(py_targets);

    std::string synmodel_filter;
    if (py_synmodel && py_synmodel != Py_None)
        synmodel_filter = PyUnicode_AsUTF8(py_synmodel);

    double min_weight = (py_min_weight && py_min_weight != Py_None) ?
                        PyFloat_AsDouble(py_min_weight) : -1e99;
    double max_weight = (py_max_weight && py_max_weight != Py_None) ?
                        PyFloat_AsDouble(py_max_weight) :  1e99;

    double min_delay = (py_min_delay && py_min_delay != Py_None) ?
                       PyFloat_AsDouble(py_min_delay) : -1e99;
    double max_delay = (py_max_delay && py_max_delay != Py_None) ?
                       PyFloat_AsDouble(py_max_delay) :  1e99;

    // Synapse model → model ID (for fast comparison)
    synindex synmodel_id = MAX_SYN_ID;  // -1

    if (!synmodel_filter.empty()) {
        try {
            synmodel_id = kernel().model_manager.get_synapse_model_id(synmodel_filter);
        } catch (...) {
            PyErr_SetString(PyExc_KeyError, "Unknown synapse model");
            return nullptr;
        }
    }

    // --- Prepare output vectors ---
    std::vector<long> out_source;
    std::vector<long> out_target;
    std::vector<double> out_weight;
    std::vector<double> out_delay;

    auto& cm = kernel().connection_manager.get_all_connections();
    out_source.reserve(cm.size() / 10);
    out_target.reserve(cm.size() / 10);
    out_weight.reserve(cm.size() / 10);
    out_delay .reserve(cm.size() / 10);

    // --- Main loop through all connections ---
    for (auto it = cm.begin(); it != cm.end(); ++it)
    {
        const auto& conn = *it;

        long src_gid = conn.get_source_node_id().get_gid();
        long tgt_gid = conn.get_target_node_id().get_gid();

        if (!source_filter.empty() && source_filter.count(src_gid) == 0)
            continue;

        if (!target_filter.empty() && target_filter.count(tgt_gid) == 0)
            continue;

        if (synmodel_id != MAX_SYN_ID && conn.get_synapse_model_id() != synmodel_id)
            continue;

        double w = conn.get_weight();
        if (w < min_weight || w > max_weight)
            continue;

        double d = conn.get_delay();
        if (d < min_delay || d > max_delay)
            continue;

        // Passed filters
        out_source.push_back(src_gid);
        out_target.push_back(tgt_gid);
        out_weight.push_back(w);
        out_delay.push_back(d);
    }

    // --- Build Python dict result ---
    PyObject* dict = PyDict_New();

    auto build_list_long = [](const std::vector<long>& v) {
        PyObject* list = PyList_New(v.size());
        for (size_t i = 0; i < v.size(); ++i)
            PyList_SET_ITEM(list, i, PyLong_FromLong(v[i]));
        return list;
    };

    auto build_list_double = [](const std::vector<double>& v) {
        PyObject* list = PyList_New(v.size());
        for (size_t i = 0; i < v.size(); ++i)
            PyList_SET_ITEM(list, i, PyFloat_FromDouble(v[i]));
        return list;
    };

    PyDict_SetItemString(dict, "source", build_list_long(out_source));
    PyDict_SetItemString(dict, "target", build_list_long(out_target));
    PyDict_SetItemString(dict, "weight", build_list_double(out_weight));
    PyDict_SetItemString(dict, "delay",  build_list_double(out_delay));

    return dict;
}


static PyObject* fast_get_connections_2(PyObject*, PyObject* args)
{
    // 1. Get all nodes managed by this machine (The "Targets")
    //    We only have access to connections landing on THESE nodes.
    const auto& local_nodes = kernel().node_manager.get_local_nodes(0); // thread 0 -> TODO: Make for each thread
    
    // 2. Optimization: Pre-calculate total connections to reserve memory exactly once.
    //    This avoids "growing" the vector which is expensive.
    size_t total_connections = 0;
    
    // We assume getting connection count is fast.
    // (If connection_manager doesn't have a fast count, we can skip this or estimate).
    // For max speed, we might skip exact reservation and guess, but let's try to be precise:
    total_connections = kernel().connection_manager.get_num_connections(); 
    // Note: get_num_connections() is usually global, so this might be an over-estimate for local, 
    // which is fine (better to over-reserve than under).

    // 3. Allocate C++ Vectors
    std::vector<long>   src_vec; src_vec.reserve(total_connections);
    std::vector<long>   tgt_vec; tgt_vec.reserve(total_connections);
    std::vector<double> w_vec;   w_vec.reserve(total_connections);
    std::vector<double> d_vec;   d_vec.reserve(total_connections);

    // 4. The Loop (The Heavy Lifting)
    // We iterate over every node we own and ask for its incoming connections.
    
    // We use a temporary buffer per node to avoid threading issues if we used OMP here,
    // but for simplicity/safety, we do this serial first. 
    // (Parallelizing the writing to the single src_vec is complex without locking).
    
    std::vector<ConnectionDatum> temp_res;
    
    // Reuse the same Target vector to avoid re-allocating it 1000 times
    std::vector<long> single_target_query; 
    single_target_query.reserve(1);

    for (const auto& node_id : local_nodes) {
        long target_gid = node_id.get_node().get_node_id();
        
        single_target_query.clear();
        single_target_query.push_back(target_gid);

        // Direct Kernel Call (No SLI)
        // We ask: "Who connects to this specific target node?"
        kernel().connection_manager.get_connections(
            {},                   // Any source
            single_target_query,  // Specific target
            -1, -1,               // Any model, Any label
            temp_res              // Output
        );

        // Copy to main buffers
        for (const auto& c : temp_res) {
            src_vec.push_back(c.source);
            tgt_vec.push_back(c.target);
            w_vec.push_back(c.weight);
            d_vec.push_back(c.delay);
        }
        
        // Clear temp buffer for next node (keeps memory allocated)
        temp_res.clear();
    }

    // 5. Batch Convert to Python Objects (The inevitable cost)
    size_t N = src_vec.size();
    PyObject* py_src = PyList_New(N);
    PyObject* py_tgt = PyList_New(N);
    PyObject* py_w   = PyList_New(N);
    PyObject* py_d   = PyList_New(N);

    for (size_t i = 0; i < N; ++i) {
        // Using macros is slightly faster than functions
        PyList_SET_ITEM(py_src, i, PyLong_FromLong(src_vec[i]));
        PyList_SET_ITEM(py_tgt, i, PyLong_FromLong(tgt_vec[i]));
        PyList_SET_ITEM(py_w,   i, PyFloat_FromDouble(w_vec[i]));
        PyList_SET_ITEM(py_d,   i, PyFloat_FromDouble(d_vec[i]));
    }

    PyObject* dict = PyDict_New();
    PyDict_SetItemString(dict, "source", py_src);
    PyDict_SetItemString(dict, "target", py_tgt);
    PyDict_SetItemString(dict, "weight", py_w);
    PyDict_SetItemString(dict, "delay",  py_d);

    return dict;
}

// --- Python registration table ---
static PyMethodDef FastConnMethods[] = {
    {"get_connections", fast_get_connections, METH_VARARGS,
     "Get filtered connections directly from C++"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef fastconnmodule = {
    PyModuleDef_HEAD_INIT,
    "fastconn",
    "Fast direct-access C++ connection API for NEST",
    -1,
    FastConnMethods
};

PyMODINIT_FUNC PyInit_fastconn(void)
{
    return PyModule_Create(&fastconnmodule);
}
