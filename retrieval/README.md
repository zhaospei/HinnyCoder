# setup
- read the `README.md` in `docker` folder

# things to do
- optimize index_params
- metric_type l2 and ip
- index_type (GPU_IVF_FLAT and GPU_IVF_PQ)
- gpu support (done)

# note
- always parallel, always backup (make checkpoints)
- optimize the query part, redesign the multithread (collection based?)

# how to retrieve?
1. install dependencies with `pip install -r requirements.txt`
2. run the docker containter
3. place your datas inside `data/raw` folder. use our parser and please follow the naming format below:
- name format: `{repo_name}_types.json` and `{repo_name}_methods.json`. `types` are data types (classes) in the project, `methods` are methods in the project.
4. run `python gpu_test.py --scan_databases` (please read the flags)
5. run `python query.py <flags you need to run with>`. you must follow the format of the retrieval column:
- retrieval column format:
```python
    Dict{
        "types": List[], # types you want to retrieve
        "methods": List[], # methods you want to retrieve
        "similar_methods": List[], # similar methods you want to retrieve
    }
```
- this will retrieve with the same algorithm we've discussed in our paper.