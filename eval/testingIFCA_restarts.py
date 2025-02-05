import logging
import time
from pathlib import Path
from shutil import copy

from localconfig import LocalConfig
from torch import multiprocessing as mp

from decentralizepy import utils
from decentralizepy.mappings.Linear import Linear
from decentralizepy.node.DPSGDNodeFederatedIFCA import DPSGDNodeFederatedIFCA
from decentralizepy.node.FederatedParameterServerIFCA import (
    FederatedParameterServerIFCA,
)


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
    utils.write_args(args, args.log_dir)

    n_machines = args.machines
    procs_per_machine = args.procs_per_machine[0]
    l_mapping = Linear(n_machines, procs_per_machine)
    m_id = args.machine_id

    sm = args.server_machine
    sr = args.server_rank

    while True:
        # dict to handle early restart
        manager = mp.Manager()
        return_dict = manager.dict()
        return_dict["early_stop"] = False

        processes = []
        if sm == m_id:
            processes.append(
                mp.Process(
                    target=FederatedParameterServerIFCA,
                    args=[
                        sr,
                        m_id,
                        l_mapping,
                        my_config,
                        args.iterations,
                        args.log_dir,
                        args.weights_store_dir,
                        log_level[args.log_level],
                        args.test_after,
                        args.train_evaluate_after,
                        args.working_rate,  # bit weird to call that a rate, its a ratio
                        return_dict,
                    ],
                )
            )

        for r in range(0, procs_per_machine):
            processes.append(
                mp.Process(
                    target=DPSGDNodeFederatedIFCA,
                    args=[
                        r,
                        m_id,
                        l_mapping,
                        my_config,
                        args.iterations,
                        args.log_dir,
                        args.weights_store_dir,
                        log_level[args.log_level],
                        args.test_after,
                        args.train_evaluate_after,
                        args.reset_optimizer,
                        sr,
                        return_dict,
                    ],
                )
            )

        for p in processes:
            p.start()

        for p in processes:
            p.join()

        if not return_dict["early_stop"]:
            print("Normal stop")
            break

        # new seed because of fail to settle
        time.sleep(10)
        my_config["DATASET"]["random_seed"] = (
            int(my_config["DATASET"]["random_seed"]) + 123456
        )
        print("Early restart, new seed is: ", my_config["DATASET"]["random_seed"])
