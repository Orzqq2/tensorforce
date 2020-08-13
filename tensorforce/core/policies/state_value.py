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

import tensorflow as tf

from tensorforce.core import Module, SignatureDict, TensorSpec, tf_function
from tensorforce.core.policies import Policy


class StateValue(Module):
    """
    Base class for state-value functions, here categorized as "degenerate" policy.

    Args:
        device (string): Device name
            (<span style="color:#00C000"><b>default</b></span>: inherit value of parent module).
        l2_regularization (float >= 0.0): Scalar controlling L2 regularization
            (<span style="color:#00C000"><b>default</b></span>: inherit value of parent module).
        name (string): <span style="color:#0000C0"><b>internal use</b></span>.
        states_spec (specification): <span style="color:#0000C0"><b>internal use</b></span>.
        auxiliaries_spec (specification): <span style="color:#0000C0"><b>internal use</b></span>.
        actions_spec (specification): <span style="color:#0000C0"><b>internal use</b></span>.
    """

    def __init__(
        self, *, device=None, l2_regularization=None, name=None, states_spec=None,
        auxiliaries_spec=None, actions_spec=None
    ):
        super().__init__(device=device, l2_regularization=l2_regularization, name=name)

        self.states_spec = states_spec
        self.auxiliaries_spec = auxiliaries_spec
        self.actions_spec = actions_spec

    def input_signature(self, *, function):
        if function == 'past_horizon':
            return SignatureDict()

        elif function == 'state_value':
            return SignatureDict(
                states=self.states_spec.signature(batched=True),
                horizons=TensorSpec(type='int', shape=(2,)).signature(batched=True),
                internals=self.internals_spec.signature(batched=True),
                auxiliaries=self.auxiliaries_spec.signature(batched=True)
            )

        else:
            return super().input_signature(function=function)

    def output_signature(self, *, function):
        if function == 'past_horizon':
            return SignatureDict(
                singleton=TensorSpec(type='int', shape=()).signature(batched=False)
            )

        elif function == 'state_value':
            return SignatureDict(
                singleton=TensorSpec(type='float', shape=()).signature(batched=True)
            )

        else:
            return super().output_signature(function=function)

    @tf_function(num_args=4)
    def state_value(self, *, states, horizons, internals, auxiliaries):
        raise NotImplementedError
