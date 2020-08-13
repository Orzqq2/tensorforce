# Copyright 2020 Tensorforce Team. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from collections import OrderedDict

from tensorforce import TensorforceError
from tensorforce.agents import TensorforceAgent


class DeterministicPolicyGradient(TensorforceAgent):
    """
    [Deterministic Policy Gradient](https://arxiv.org/abs/1509.02971) agent (specification key:
    `dpg` or `ddpg`). Action space is required to consist of only a single float action.

    Args:
        states (specification): States specification
            (<span style="color:#C00000"><b>required</b></span>, better implicitly specified via
            `environment` argument for `Agent.create(...)`), arbitrarily nested dictionary of state
            descriptions (usually taken from `Environment.states()`) with the following attributes:
            <ul>
            <li><b>type</b> (<i>"bool" | "int" | "float"</i>) &ndash; state data type
            (<span style="color:#00C000"><b>default</b></span>: "float").</li>
            <li><b>shape</b> (<i>int | iter[int]</i>) &ndash; state shape
            (<span style="color:#C00000"><b>required</b></span>).</li>
            <li><b>num_values</b> (<i>int > 0</i>) &ndash; number of discrete state values
            (<span style="color:#C00000"><b>required</b></span> for type "int").</li>
            <li><b>min_value/max_value</b> (<i>float</i>) &ndash; minimum/maximum state value
            (<span style="color:#00C000"><b>optional</b></span> for type "float").</li>
            </ul>
        actions (specification): Actions specification
            (<span style="color:#C00000"><b>required</b></span>, better implicitly specified via
            `environment` argument for `Agent.create(...)`), arbitrarily nested dictionary of
            action descriptions (usually taken from `Environment.actions()`) with the following
            attributes:
            <ul>
            <li><b>type</b> (<i>"bool" | "int" | "float"</i>) &ndash; action data type
            (<span style="color:#C00000"><b>required</b></span>).</li>
            <li><b>shape</b> (<i>int > 0 | iter[int > 0]</i>) &ndash; action shape
            (<span style="color:#00C000"><b>default</b></span>: scalar).</li>
            <li><b>num_values</b> (<i>int > 0</i>) &ndash; number of discrete action values
            (<span style="color:#C00000"><b>required</b></span> for type "int").</li>
            <li><b>min_value/max_value</b> (<i>float</i>) &ndash; minimum/maximum action value
            (<span style="color:#00C000"><b>optional</b></span> for type "float").</li>
            </ul>
        max_episode_timesteps (int > 0): Upper bound for numer of timesteps per episode
            (<span style="color:#00C000"><b>default</b></span>: not given, better implicitly
            specified via `environment` argument for `Agent.create(...)`).

        memory (int > 0): Replay memory capacity, has to fit at least maximum batch_size + maximum
            network/estimator horizon + 1 timesteps
            (<span style="color:#C00000"><b>required</b></span>).
        batch_size (<a href="../modules/parameters.html">parameter</a>, int > 0): Number of
            timesteps per update batch
            (<span style="color:#C00000"><b>required</b></span>).

        network ("auto" | specification): Policy network configuration, see the
            [networks documentation](../modules/networks.html)
            (<span style="color:#00C000"><b>default</b></span>: "auto", automatically configured
            network).
        use_beta_distribution (bool): Whether to use the Beta distribution for bounded continuous
            actions by default.
            (<span style="color:#00C000"><b>default</b></span>: true).

        update_frequency ("never" | <a href="../modules/parameters.html">parameter</a>, int > 0):
            Frequency of updates
            (<span style="color:#00C000"><b>default</b></span>: batch_size).
        start_updating (<a href="../modules/parameters.html">parameter</a>, int >= batch_size):
            Number of timesteps before first update
            (<span style="color:#00C000"><b>default</b></span>: none).
        learning_rate (<a href="../modules/parameters.html">parameter</a>, float > 0.0): Optimizer
            learning rate
            (<span style="color:#00C000"><b>default</b></span>: 1e-3).

        horizon (<a href="../modules/parameters.html">parameter</a>, int >= 1): Horizon of
            discounted-sum reward estimation before critic estimate
            (<span style="color:#00C000"><b>default</b></span>: 1).
        discount (<a href="../modules/parameters.html">parameter</a>, 0.0 <= float <= 1.0): Discount
            factor for future rewards of discounted-sum reward estimation
            (<span style="color:#00C000"><b>default</b></span>: 0.99).
        predict_terminal_values (bool): Whether to predict the value of terminal states
            (<span style="color:#00C000"><b>default</b></span>: false).

        critic (specification): Critic network configuration, see the
            [networks documentation](../modules/networks.html)
            (<span style="color:#00C000"><b>default</b></span>: none).
        critic_optimizer (float > 0.0 | specification): Critic optimizer configuration, see the
            [optimizers documentation](../modules/optimizers.html), a float instead specifies a
            custom weight for the critic loss
            (<span style="color:#00C000"><b>default</b></span>: 1.0).

        l2_regularization (<a href="../modules/parameters.html">parameter</a>, float >= 0.0):
            L2 regularization loss weight
            (<span style="color:#00C000"><b>default</b></span>: no L2 regularization).
        entropy_regularization (<a href="../modules/parameters.html">parameter</a>, float >= 0.0):
            Entropy regularization loss weight, to discourage the policy distribution from being
            "too certain"
            (<span style="color:#00C000"><b>default</b></span>: no entropy regularization).

        preprocessing (dict[specification]): Preprocessing as layer or list of layers, see the
            [preprocessing documentation](../modules/preprocessing.html),
            specified per state-type or -name, and for reward/return/advantage
            (<span style="color:#00C000"><b>default</b></span>: linear normalization of bounded
            float states to [-2.0, 2.0]).
        exploration (<a href="../modules/parameters.html">parameter</a> | dict[<a href="../modules/parameters.html">parameter</a>], float >= 0.0):
            Exploration, defined as the probability for uniformly random output in case of `bool`
            and `int` actions, and the standard deviation of Gaussian noise added to every output in
            case of `float` actions, specified globally or per action-type or -name
            (<span style="color:#00C000"><b>default</b></span>: no exploration).
        variable_noise (<a href="../modules/parameters.html">parameter</a>, float >= 0.0):
            Add Gaussian noise with given standard deviation to all trainable variables, as
            alternative exploration mechanism
            (<span style="color:#00C000"><b>default</b></span>: no variable noise).

        others: See the [Tensorforce agent documentation](tensorforce.html).
    """

    def __init__(
        # Required
        self, states, actions, memory, batch_size,
        # Environment
        max_episode_timesteps=None,
        # Network
        network='auto', use_beta_distribution=True,
        # Optimization
        update_frequency='batch_size', start_updating=None, learning_rate=1e-3,
        # Reward estimation
        horizon=1, discount=0.99, predict_terminal_values=False,
        # Critic
        critic='auto', critic_optimizer=1.0,
        # Preprocessing
        preprocessing='linear_normalization',
        # Exploration
        exploration=0.0, variable_noise=0.0,
        # Regularization
        l2_regularization=0.0, entropy_regularization=0.0,
        # Parallel interactions
        parallel_interactions=1,
        # Config, saver, summarizer, recorder
        config=None, saver=None, summarizer=None, recorder=None,
        # Deprecated
        estimate_terminal=None, critic_network=None, **kwargs
    ):
        raise TensorforceError(message='Temporarily broken.')
        if estimate_terminal is not None:
            raise TensorforceError.deprecated(
                name='DPG', argument='estimate_terminal', replacement='predict_terminal_values'
            )
        if critic_network is not None:
            raise TensorforceError.deprecated(
                name='DPG', argument='critic_network', replacement='critic'
            )

        self.spec = OrderedDict(
            agent='dpg',
            states=states, actions=actions, memory=memory, batch_size=batch_size,
            max_episode_timesteps=max_episode_timesteps,
            network=network, use_beta_distribution=use_beta_distribution,
            update_frequency=update_frequency, start_updating=start_updating,
            learning_rate=learning_rate,
            horizon=horizon, discount=discount, predict_terminal_values=predict_terminal_values,
            critic=critic, critic_optimizer=critic_optimizer,
            preprocessing=preprocessing,
            exploration=exploration, variable_noise=variable_noise,
            l2_regularization=l2_regularization, entropy_regularization=entropy_regularization,
            parallel_interactions=parallel_interactions,
            config=config, saver=saver, summarizer=summarizer, recorder=recorder
        )

        policy = dict(
            type='parametrized_distributions', network=network, temperature=0.0,
            use_beta_distribution=use_beta_distribution
        )

        memory = dict(type='replay', capacity=memory)

        update = dict(unit='timesteps', batch_size=batch_size)
        if update_frequency != 'batch_size':
            update['frequency'] = update_frequency
        if start_updating is not None:
            update['start'] = start_updating

        optimizer = dict(type='adam', learning_rate=learning_rate)
        objective = 'deterministic_policy_gradient'

        reward_estimation = dict(
            horizon=horizon, discount=discount, predict_horizon_values='late',
            estimate_advantage=False, predict_action_values=True,
            predict_terminal_values=predict_terminal_values
        )

        baseline = dict(type='parametrized_distributions', network=critic)
        baseline_optimizer = critic_optimizer
        baseline_objective = dict(type='value', value='action')

        super().__init__(
            # Agent
            states=states, actions=actions, max_episode_timesteps=max_episode_timesteps,
            parallel_interactions=parallel_interactions, config=config, recorder=recorder,
            # Model
            preprocessing=preprocessing, exploration=exploration, variable_noise=variable_noise,
            l2_regularization=l2_regularization, saver=saver, summarizer=summarizer,
            # TensorforceModel
            policy=policy, memory=memory, update=update, optimizer=optimizer, objective=objective,
            reward_estimation=reward_estimation, baseline=baseline,
            baseline_optimizer=baseline_optimizer, baseline_objective=baseline_objective,
            entropy_regularization=entropy_regularization, **kwargs
        )
