"""Sim2Sim bridge implementation using ZMQ IPC for simulation."""

import json
import os
import numpy as np
import zmq
from loguru import logger

from holosoma.bridge.base.basic_sdk2py_bridge import BasicSdk2Bridge

IPC_DIR = "/tmp/holosoma_sim2sim"


class Sim2SimBridge(BasicSdk2Bridge):
    """Sim2Sim bridge using ZMQ IPC for communication between simulator and policy."""

    def _init_sdk_components(self):
        """Initialize ZMQ components for sim2sim communication."""
        os.makedirs(IPC_DIR, exist_ok=True)
        
        self._context = zmq.Context()
        
        # Publisher for robot state (simulator -> policy)
        self._state_pub = self._context.socket(zmq.PUB)
        self._state_pub.bind(f"ipc://{IPC_DIR}/state")
        
        # Subscriber for commands (policy -> simulator)
        self._cmd_sub = self._context.socket(zmq.SUB)
        self._cmd_sub.connect(f"ipc://{IPC_DIR}/cmd")
        self._cmd_sub.setsockopt_string(zmq.SUBSCRIBE, "cmd")
        self._cmd_sub.setsockopt(zmq.RCVTIMEO, 0)  # Non-blocking
        
        # Command storage
        self._last_cmd = None
        
        logger.info("Sim2Sim bridge initialized (IPC)")

    def low_cmd_handler(self, msg=None):
        """Receive commands from policy via ZMQ."""
        try:
            topic, data = self._cmd_sub.recv_multipart(zmq.NOBLOCK)
            self._last_cmd = json.loads(data.decode())
        except zmq.Again:
            pass
        except Exception as e:
            logger.debug(f"Error receiving command: {e}")

    def publish_low_state(self):
        """Publish robot state to policy via ZMQ."""
        positions, velocities, accelerations = self._get_dof_states()
        actuator_forces = self._get_actuator_forces()
        quaternion, gyro, acceleration = self._get_base_imu_data()
        
        state = {
            "quat": quaternion.detach().cpu().numpy().tolist(),
            "gyro": gyro.detach().cpu().numpy().tolist(),
            "accel": acceleration.detach().cpu().numpy().tolist(),
            "q": positions.tolist(),
            "dq": velocities.tolist(),
            "ddq": accelerations.tolist(),
            "tau_est": actuator_forces.tolist(),
            "tick": int(self.sim_time * 1e3),
        }
        
        data = json.dumps(state).encode()
        self._state_pub.send_multipart([b"state", data])

    def compute_torques(self):
        """Compute torques from received commands."""
        if self._last_cmd is None:
            # Hold default pose until policy connects (prevents falling during startup)
            if not hasattr(self, '_startup_kp'):
                # Use per-joint stiffness/damping from robot control config
                stiffness = self.robot.control.stiffness
                damping = self.robot.control.damping
                dof_names = self.simulator.dof_names  # e.g. ['left_hip_pitch_joint', ...]
                self._startup_kp = np.zeros(self.num_motor)
                self._startup_kd = np.zeros(self.num_motor)
                for i, dof_name in enumerate(dof_names):
                    # Strip _joint suffix and left_/right_ prefix for lookup
                    key = dof_name.replace('_joint', '')
                    # Try exact match first, then strip side prefix
                    if key in stiffness:
                        self._startup_kp[i] = stiffness[key]
                        self._startup_kd[i] = damping[key]
                    else:
                        # Try without left_/right_ prefix
                        for prefix in ['left_', 'right_']:
                            if key.startswith(prefix):
                                base_key = key[len(prefix):]
                                if base_key in stiffness:
                                    self._startup_kp[i] = stiffness[base_key]
                                    self._startup_kd[i] = damping[base_key]
                                    break
                # Default fallback
                self._startup_kp[self._startup_kp == 0] = 50.0
                self._startup_kd[self._startup_kd == 0] = 2.0
                # Default joint angles from init state
                default_angles = self.robot.init_state.default_joint_angles
                self._startup_q = np.zeros(self.num_motor)
                for i, dof_name in enumerate(dof_names):
                    if dof_name in default_angles:
                        self._startup_q[i] = default_angles[dof_name]
                logger.info(f"Sim2Sim startup: holding default pose (KP range: {self._startup_kp.min():.0f}-{self._startup_kp.max():.0f})")
            q_actual = self.simulator.dof_pos[0].detach().cpu().numpy()
            dq_actual = self.simulator.dof_vel[0].detach().cpu().numpy()
            self.torques = np.clip(
                self._startup_kp * (self._startup_q - q_actual) + self._startup_kd * (0 - dq_actual),
                -self.torque_limit, self.torque_limit
            )
            return self.torques
        
        try:
            cmd = self._last_cmd
            return self._compute_pd_torques(
                tau_ff=np.array(cmd.get("tau", [0.0] * self.num_motor)),
                kp=np.array(cmd.get("kp", [0.0] * self.num_motor)),
                kd=np.array(cmd.get("kd", [0.0] * self.num_motor)),
                q_target=np.array(cmd.get("q", [0.0] * self.num_motor)),
                dq_target=np.array(cmd.get("dq", [0.0] * self.num_motor)),
            )
        except Exception as e:
            logger.error(f"Error computing torques: {e}")
            return self.torques
