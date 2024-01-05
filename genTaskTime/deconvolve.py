"""
 3dDeconvolve                                                  \\
    -nodata 410 1.300                                           \\
    -polort 1                                                   \\
    -num_stimts 6                                               \\
    -stim_times 1 g_chose.1D GAM                                \\
    -stim_label 1 good                                          \\
    -stim_times 2 g_fbk.1D GAM                                  \\
"""
import re
from .LastLeaves import LastLeaves
from .EventNode import uniquenode


def d_append(d: dict, k, v):
    "append list of key in dict. or crete new aray"
    if d.get(k):
        d[k].append(v)
    else:
        d[k] = [v]


StimDictist = list[dict]
GLTDict = list[dict[str, str]]


def extract_stims(last_leaves: LastLeaves) -> tuple[StimDictist, GLTDict]:
    stim = {}
    glt = {}
    for n in uniquenode(last_leaves):
        if re.matches(r"__catch__\d+", n.name):
            continue

        name = n.name
        model = n.model

        # 0s dur are sub-events. they're 1D files will have parent name prefix
        # and we'll probably want to model all as single event collapsed in parent
        # use glt for that
        if n.dur == 0:
            parent = n.path[-2]
            name = f"{parent.name}_{n.name}"
            if parent.model != n.model:
                model = parent.model
            d_append(glt, parent.name, n.name)

        stim += {"name": name, "model": model}

    # sum subevent nodes to make glt to represent their shared parent
    # format like other GLTs parsed by the AST/gammar/user input
    parent_glt = [{"name": k, "formula": "+".join(v)} for k, v in glt.items()]
    return (stim, parent_glt)


def decon(stims: StimDictist, parent_glt: GLTDict, settings: dict):
    cmd = f"""
    -nodata {settings['total_dur']} {settings['tr']} \\
    -polort 3 \\
    -num_stimts {len(stims)} \\
    """
    for i, stim in enumerate(stims):
        cmd += (
            f'-stim_label {i+1} {stim["name"]} '
            + f'-stim_times {i+1} {stim["name"]}.1D {stim["model"]} \\\n'
        )

    # make
    all_glts = parent_glt + settings["glts"]
    if len(all_glts) > 0:
        cmd += f"-num_glt {len(all_glts)} \\\n"

    for glt in all_glts:
        cmd += f'-glt_label {i+1} {glt["name"]} -gltsym "sym:{glt["formula"]}"\\\n'

    return cmd
