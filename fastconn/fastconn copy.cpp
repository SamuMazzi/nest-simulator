#include <Python.h>

#include "kernel_manager.h"
#include "connection_manager.h"
#include "connection.h"
#include "dictutils.h"
#include "model.h"
#include "model_manager.h"

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
    index synmodel_id = -1;

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

    auto& cm = kernel().connection_manager;
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

        if (synmodel_id != -1 && conn.get_synapse_model_id() != synmodel_id)
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
