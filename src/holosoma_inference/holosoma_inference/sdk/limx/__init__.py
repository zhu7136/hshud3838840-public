"""LimX robot interface for simulation (sim2sim)."""

import json
import os
import numpy as np
import zmq

from holosoma_inference.config.config_types import RobotConfig
from holosoma_inference.sdk.base.base_interface import BaseInterface

IPC_DIR = "/tmp/holosoma_sim2sim"

# Singleton instances to avoid port conflicts in dual-mode
_context = None
_cmd_pub = None
_state_sub = None


class LimxSimInterface(BaseInterface):
    """Interface for LimX robots in simulation (sim2sim)."""

    def __init__(self, robot_config: RobotConfig, domain_id=0, interface_str=None, use_joystick=True):
        super().__init__(robot_config, domain_id, interface_str, use_joystick)
        self._state = None
        self._kp_level = 1.0
        self._kd_level = 1.0
        self._init_zmq()

    @property
    def kp_level(self):
        return self._kp_level

    @kp_level.setter
    def kp_level(self, value):
        self._kp_level = value

    @property
    def kd_level(self):
        return self._kd_level

    @kd_level.setter
    def kd_level(self, value):
        self._kd_level = value

    def _init_zmq(self):
        """Initialize ZMQ IPC for sim2sim (singleton)."""
        global _context, _cmd_pub, _state_sub
        
        if _cmd_pub is not None:
            self._cmd_pub = _cmd_pub
            self._state_sub = _state_sub
            print("LimX sim interface: reusing existing ZMQ connection")
            return
        
        os.makedirs(IPC_DIR, exist_ok=True)
        _context = zmq.Context()
        
        # Publisher for commands (policy -> simulator)
        _cmd_pub = _context.socket(zmq.PUB)
        _cmd_pub.bind(f"ipc://{IPC_DIR}/cmd")
        
        # Subscriber for state (simulator -> policy)
        _state_sub = _context.socket(zmq.SUB)
        _state_sub.connect(f"ipc://{IPC_DIR}/state")
        _state_sub.setsockopt_string(zmq.SUBSCRIBE, "state")
        _state_sub.setsockopt(zmq.RCVTIMEO, 1000)
        
        self._cmd_pub = _cmd_pub
        self._state_sub = _state_sub
        print("LimX sim interface initialized (IPC)")

    def get_low_state(self) -> np.ndarray:
        """Get robot state as numpy array from simulator."""
        try:
            topic, data = self._state_sub.recv_multipart()
            state_dict = json.loads(data.decode())
            
            n = self.robot_config.num_joints
            state = np.zeros((1, 3 + 4 + n + 3 + 3 + n))
            
            state[0, 0:3] = 0.0
            state[0, 3:7] = state_dict["quat"]
            state[0, 7:7+n] = state_dict["q"]
            state[0, 7+n:10+n] = 0.0
            state[0, 10+n:13+n] = state_dict["gyro"]
            state[0, 13+n:13+2*n] = state_dict["dq"]
            
            self._state = state
            return state
        except zmq.Again:
            if self._state is not None:
                return self._state
            n = self.robot_config.num_joints
            return np.zeros((1, 3 + 4 + n + 3 + 3 + n))
        except Exception as e:
            print(f"Error receiving state: {e}")
            if self._state is not None:
                return self._state
            n = self.robot_config.num_joints
            return np.zeros((1, 3 + 4 + n + 3 + 3 + n))

    def send_low_command(
        self,
        cmd_q: np.ndarray,
        cmd_dq: np.ndarray,
        cmd_tau: np.ndarray,
        dof_pos_latest: np.ndarray = None,
        kp_override: np.ndarray = None,
        kd_override: np.ndarray = None,
    ):
        """Send low-level command to simulator."""
        cmd = {
            "q": cmd_q.tolist(),
            "dq": cmd_dq.tolist(),
            "tau": cmd_tau.tolist(),
        }
        if kp_override is not None:
            cmd["kp"] = kp_override.tolist()
        if kd_override is not None:
            cmd["kd"] = kd_override.tolist()
        try:
            data = json.dumps(cmd).encode()
            self._cmd_pub.send_multipart([b"cmd", data])
        except zmq.Again:
            pass

    def get_joystick_msg(self):
        return None

    def get_joystick_key(self, wc_msg=None):
        return None
