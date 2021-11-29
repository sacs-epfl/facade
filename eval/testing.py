import logging
from pathlib import Path
from shutil import copy

from localconfig import LocalConfig
from torch import multiprocessing as mp

from decentralizepy import utils
from decentralizepy.graphs.Graph import Graph
from decentralizepy.mappings.Linear import Linear
from decentralizepy.node.Node import Node


def read_ini(file_path):
    config = LocalConfig(file_path)
    for section in config:
        print("Section: ", section)
        for key, value in config.items(section):
            print((key, value))
    print(dict(config.items("DATASET")))
    return config


if __name__ == "__main__":
    args = utils.get_args()

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    log_level = {
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    config = read_ini(args.config_file)
    my_config = dict()
    for section in config:
        my_config[section] = dict(config.items(section))

    copy(args.config_file, args.log_dir)
    copy(args.graph_file, args.log_dir)
    utils.write_args(args, args.log_dir)

    g = Graph()
    g.read_graph_from_file(args.graph_file, args.graph_type)
    n_machines = args.machines
    procs_per_machine = args.procs_per_machine
    l = Linear(n_machines, procs_per_machine)
    m_id = args.machine_id

    mp.spawn(
        fn=Node,
        nprocs=procs_per_machine,
        args=[
            m_id,
            l,
            g,
            my_config,
            args.iterations,
            args.log_dir,
            log_level[args.log_level],
        ],
    )
