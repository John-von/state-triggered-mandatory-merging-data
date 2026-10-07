function P = params()
%PARAMS Base vehicle and control parameters.
P.lane_w = 3.5;  % Lane width (m)
P.Lc     = 5.0;  % Vehicle length (m)
P.Wc     = 1.8;  % Vehicle width (m)

% Vehicle dynamics
P.m   = 1500;  % Vehicle mass (kg)
P.Iz  = 3000;  % Yaw inertia (kg m^2)
P.lf  = 1.2;  % Center of mass to front axle (m)
P.lr  = 1.6;  % Center of mass to rear axle (m)
P.Cf  = 80000;  % Front cornering stiffness (N/rad)
P.Cr  = 80000;  % Rear cornering stiffness (N/rad)

% Motion constraints
P.v_min = 5.0;   P.v_max = 33.0;  % Speed bounds (m/s)
P.a_min = -2.0;  P.a_max = 2.0;  % Acceleration bounds (m/s^2)
P.j_min = -2.0;  P.j_max = 2.0;  % Jerk bounds (m/s^3)
P.df_max = 0.10;  % Steering-angle bound (rad)
P.ddf_max = 0.02;  % Steering increment bound (rad/step)

% Gap parameters
P.d0      = 2.0;  % Standstill gap (m)
P.tau_h   = 1.0;  % Following headway (s)
P.tau_acc = 1.0;  % Initial admission headway (s)
P.tau_min = 0.5;  % Minimum admission headway (s)
P.t_imp   = 20.0;  % Headway relaxation time (s)

% Simulation settings
P.Ts = 0.1;  % Sampling interval (s)
P.n_sub = 5;  % Integration substeps
P.T_end = 120.0;  % Simulation horizon (s)
P.t_dec = 5.0;  % Decision time (s)

% Gap-creation MPC
P.Np_g = 20;  % Prediction horizon
P.Nc_g = 6;  % Control horizon
P.k_con = [4 8 12 16 20];  % Constrained prediction steps, one-based
P.qv = 1.0;  % Speed-tracking weight
P.qa = 4.0;  % Acceleration weight
P.ru = 1.0;  % Jerk weight
P.qg = 6.0;  % Gap-error weight
P.qr = 3.0;  % Relative-speed weight
P.qc = 2.0;  % Gap-centering weight

% Lane-change MPC
P.Np_t = 12;  P.Nc_t = 4;
P.qY = 600;  P.qpsi = 150;  P.qvx = 8;
P.r_ax = 1.0;  P.r_df = 4e3;

% Maneuver timing
P.T_lc = 5.0;  % Lane-change duration (s)
P.T_ramp = 15.0;  % Gap-reference ramp time (s)
P.T_prep_max = 40.0;  % Preparation timeout (s)
P.dt_batch = 10.0;  % Batch interval (s)

% Scheduling defaults
P.T_win = 60.0;  % Scheduling window (s)
P.N_max = 6;  % Maneuvers per window
P.w = [0.30 0.25 0.25 0.20];  % Scheduling weights

% Following controllers
P.kp_c = 0.45;  P.kd_c = 0.9;                 % CAV: CACC
P.kp_pid_x = 0.30; P.kd_pid_x = 0.80;  % Longitudinal PID gains
P.kp_pid_y = 0.10; P.kp_pid_psi = 0.70; P.kd_pid_r = 0.25;  % Lateral PID gains
P.idm = struct('v0',25.0,'T',1.0,'s0',2.0,'a',1.5,'b',2.0,'delta',4.0);  % HDV

% Initial traffic state
P.n0 = 20;  P.sp0 = 22.0;  P.v0 = 16.0;  % Closing lane
P.n1 = 14;  P.sp1 = 30.0;  P.v1 = 18.0;  % Target lane
P.x0_head = 520.0;  P.x1_head = 700.0;

% Fuel and emission parameters
P.em = struct('g',9.81,'Cr',0.015,'rho',1.206,'Cd',0.32,'Af',2.2, ...
              'eta',0.30,'LHV',44.0e6,'idle',0.35,'rho_f',737.0, ...
              'co2',3.13,'nox',0.62);
end
