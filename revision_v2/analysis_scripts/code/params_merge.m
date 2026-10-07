function P = params_merge()
%PARAMS_MERGE Lane-closure scenario and strategy parameters.
P = params();  % Base control, dynamics and fuel parameters

% Lane-closure geometry
P.X_drop = 750.0;  % Lane-closure coordinate (m)
P.D_crit = 25.0;  % Critical distance to closure (m)
P.b = 2.1;  % Lateral proximity threshold (m)

% Safety settings
P.a_emg   = -6.0;  % Modeled emergency acceleration lower bound (m/s^2)
P.g_stop  = 1.0;  % Emergency gap threshold (m)
P.T_lc    = 3.5;  % Lane-change duration (s)
P.k_pred  = 1.0;  % Relative-speed prediction coefficient
P.g_abort = 0.3;  % Early-maneuver rear-gap threshold offset (m)
P.f_abort = 0.45;  % Early-maneuver hold window fraction
P.g_gap_correction = 0.4;  % Optional correction gap (m)
P.v_lc_min = 3.0;  % Minimum speed for reference progression (m/s)
P.v_lc_dyn_min = 5.0;  % Minimum speed for dynamic lateral update (m/s)
P.y_merge_tol = 0.10;  % Lateral completion tolerance (m)
P.vy_merge_tol = 0.50;  % Lateral-speed completion tolerance (m/s)
P.psi_merge_tol = 5*pi/180;  % Heading completion tolerance (rad)
P.tau_safe = 1.30;  % Safety-filter headway (s)
P.safety_buffer = 0.0;  % Additional gap buffer (m)

% Initial traffic state
% All closing-lane vehicles must merge.
P.n0 = 12;  P.sp0 = 26.0;  P.v0 = 16.0;   P.x0_head = 500.0;
% Target-lane density is set by the experiment script.
P.n1 = 26;  P.sp1 = 28.0;  P.v1 = 22.0;   P.x1_head = 720.0;

% Simulation horizon
P.T_end = 90.0;

% Gap-creation reference
P.g_open_fac = 1.0;  % Multiplier of 2*(d0+tau_h*v)
P.T_ramp = 12.0;  % Gap-reference ramp time (s)

% Merge scheduling
P.dt_release = 0.0;  % Admission interval (s), zero allows continuous admission
P.N_prep = 4;  % Maximum simultaneous gap preparations
P.N_lc_active = 2;  % Maximum simultaneous lane changes

% ECO settings
P.eco_density_min = 35.0;  % Density activation threshold (veh/km)
P.eco_trigger_dist = 400.0;  % Activation distance from closure (m)
P.eco_N_prep = 3;  % Maximum ECO gap preparations
P.eco_N_lc_active = 3;  % Maximum ECO lane changes
P.eco_T_ramp = 3.0;  % ECO gap-reference ramp time (s)
P.eco_g_open_fac = 1.0;  % ECO gap-target multiplier
P.eco_k_pred = 0.8;  % ECO relative-speed prediction coefficient
P.eco_tau_gap = 1.00;  % ECO operational headway (s)
P.eco_qv = 4.0;  % Speed-tracking weight
P.eco_qa = 8.0;  % Acceleration weight
P.eco_ru = 2.0;  % Jerk weight
P.eco_qg = 8.0;  % Gap-error weight
P.eco_qr = 0.0;  % Relative-speed weight
P.eco_qc = 6.0;  % Gap-centering weight
P.eco_kp_gap = 0.40;  % Gap proportional gain
P.eco_kd_gap = 0.90;  % Relative-speed gain
P.eco_a_min = -2.0;  % Gap-creation acceleration lower bound (m/s^2)
P.eco_a_max = 1.2;  % Gap-creation acceleration upper bound (m/s^2)
P.eco_safety_buffer = 0.10;  % ECO gap buffer (m)
P.eco_hold_merge_speed = false;  % Optional speed-hold switch

% Safety-ablation switches
P.use_predictive_gap = true;  % Use relative-speed gap prediction
P.use_abort = true;  % Enable early-maneuver hold
P.use_safety_filter = true;  % Enable the barrier-based filter
P.use_gap_correction = false;  % Post-update position correction, disabled by default
end
