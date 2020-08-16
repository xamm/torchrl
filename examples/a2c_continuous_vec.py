import torch
import os
import time
import sys
import os.path as osp
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from torchrl.utils import get_args
from torchrl.utils import get_params
from torchrl.replay_buffers.on_policy import OnPolicyReplayBuffer
from torchrl.utils import Logger
import torchrl.policies as policies
import torchrl.networks as networks
from torchrl.algo import A2C
from torchrl.collector.on_policy import VecOnPlicyCollector
import gym
import random
from torchrl.env import get_vec_env


args = get_args()
params = get_params(args.config)


def experiment(args):

    device = torch.device(
        "cuda:{}".format(args.device) if args.cuda else "cpu")

    env = get_vec_env(
        params["env_name"],
        params["env"],
        args.vec_env_nums
    )

    env.seed(args.seed)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)
    if args.cuda:
        torch.cuda.manual_seed_all(args.seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True

    buffer_param = params['replay_buffer']

    experiment_name = os.path.split(
        os.path.splitext(args.config)[0])[-1] if args.id is None \
        else args.id
    logger = Logger(
        experiment_name, params['env_name'], args.seed, params, args.log_dir)

    params['general_setting']['env'] = env

    replay_buffer = OnPolicyReplayBuffer(
        env_nums=4,
        max_replay_buffer_size=int(buffer_param['size']),
        time_limit_filter=buffer_param['time_limit_filter']
    )
    params['general_setting']['replay_buffer'] = replay_buffer

    params['general_setting']['logger'] = logger
    params['general_setting']['device'] = device

    params['net']['base_type'] = networks.MLPBase
    params['net']['activation_func'] = torch.nn.Tanh
    pf = policies.GuassianContPolicyBasicBias(
        input_shape=env.observation_space.shape[0],
        output_shape=env.action_space.shape[0],
        **params['net'],
        **params['policy']
    )
    vf = networks.Net(
        input_shape=env.observation_space.shape,
        output_shape=1,
        **params['net']
    )
    print(pf)
    print(vf)
    params['general_setting']['collector'] = VecOnPlicyCollector(
        vf, env=env, pf=pf,
        replay_buffer=replay_buffer, device=device,
        train_render=False,
        **params["collector"]
    )
    params['general_setting']['save_dir'] = osp.join(
        logger.work_dir, "model")
    agent = A2C(
            pf=pf,
            vf=vf,
            **params["a2c"],
            **params["general_setting"]
        )
    agent.train()


if __name__ == "__main__":
    experiment(args)
