function R = simulate_components(mode, pen, seed, P, logTraj)
%SIMULATE_COMPONENTS Simulate COOP, ECO or PASSIVE mandatory merging.
% pen is the target-lane CAV fraction; seed identifies a paired realization.
if nargin < 4 || isempty(P), P = params_merge(); end
if nargin < 5, logTraj = false; end
ecoMode = strcmp(mode,'ECO');
if ecoMode, P.safety_buffer = P.eco_safety_buffer; end
LANE_Y = [P.lane_w/2, P.lane_w*1.5];
Xd = P.X_drop;

V = init_merge(P, pen, seed, LANE_Y);
n = numel(V.x);
nstep = round(P.T_end / P.Ts);
% Network state broadcasts and local sensing have separate random streams.
% Ego state and discrete lane/role labels are measured locally without error.
delay_steps=round(opt(P,'delay_s',0)/P.Ts);
drop_probability=opt(P,'drop_probability',0);
pos_sigma=opt(P,'position_sigma',0); speed_sigma=opt(P,'speed_sigma',0);
net=RandStream('mt19937ar','Seed',seed+100000);
sense=RandStream('mt19937ar','Seed',seed+200000);
packet_received=rand(net,nstep,n)>=drop_probability;
position_error=pos_sigma*randn(sense,nstep,n);
speed_error=speed_sigma*randn(sense,nstep,n);
history_x=zeros(nstep,n);history_v=zeros(nstep,n);history_a=zeros(nstep,n);
packet_x=V.x;packet_v=V.vx;packet_a=V.a;packet_time=zeros(1,n);
age_sum=0;age_max=0;age_count=0;
filter_step_count=zeros(nstep,1);filter_step_delta=zeros(nstep,1);
filter_delta_by_vehicle=zeros(nstep,n);
hold_steps=zeros(nstep,1);vy_peak=zeros(nstep,1);

u_prev = zeros(n,2);
recV = zeros(nstep,n); recA = zeros(nstep,n); recX = zeros(nstep,n);
recLane = zeros(nstep,n);
min_gap = inf; n_hard = 0; n_brake = 0; n_abort = 0;
pre_gap_violation_steps = 0; final_gap_violation_steps = 0;
n_safety = 0; n_gap_corrections = 0;
stop_steps = 0;
    M = repmat(struct('coef',zeros(1,6),'texec',0,'tau',0,'tw',0,'tcoop',0, ...
                      'hold',false,'hold_prev',false,'kinematic',false), 1, n);
traj = [];
if logTraj, traj = zeros(nstep,n,4); end

step_seconds=zeros(nstep,1); filter_hdv=0; filter_cav=0; filter_delta_sum=0; filter_delta_max=0; filter_count=0;
for k = 1:nstep
    step_clock=tic;
    t = (k-1)*P.Ts;
    history_x(k,:)=V.x;history_v(k,:)=V.vx;history_a(k,:)=V.a;
    source_index=k-delay_steps;
    if source_index>=1
        received=packet_received(k,:) & V.cav;
        packet_x(received)=history_x(source_index,received);
        packet_v(received)=history_v(source_index,received);
        packet_a(received)=history_a(source_index,received);
        packet_time(received)=(source_index-1)*P.Ts;
    end
    % Last received CAV broadcast is extrapolated at constant velocity.
    % HDV states come from current local sensing; they do not broadcast.
    age=t-packet_time; observed=V;
    observed.x(V.cav)=packet_x(V.cav)+packet_v(V.cav).*age(V.cav);
    observed.vx(V.cav)=packet_v(V.cav);observed.a(V.cav)=packet_a(V.cav);
    observed.x=observed.x+position_error(k,:);
    observed.vx=max(0,observed.vx+speed_error(k,:));
    age_sum=age_sum+sum(age(V.cav));age_count=age_count+sum(V.cav);
    age_max=max(age_max,max(age(V.cav)));

    acc = zeros(1,n);  handled = false(1,n);
    committedTF = false(1,n);
    n_lc_active = sum(V.role==3);

    active = find(V.lane==0 & V.role~=4);
    commit_id = -1;
    if ~isempty(active)
        [~,ord] = sort(Xd - V.x(active));  % Prioritize proximity to the closure
        active = active(ord);
        candidates = active(V.role(active)==1);
        if ~isempty(candidates), commit_id = candidates(1); end
    end

    % Merging-vehicle control
    for aa = 1:numel(active)
        i = active(aa);
        S=ego_estimate(observed,V,i);
        v_i = V.vx(i);
        [TP,TF] = lane1_targets(S, i, P);

        % Lane-change execution
        if V.role(i) == 3
            tau = M(i).tau;
            if v_i < P.v_lc_dyn_min && ~M(i).kinematic
                M(i).kinematic = true;
                M(i).tau = 0;
                tau = 0;
                M(i).coef = quintic_traj(V.y(i), V.vy(i), 0, LANE_Y(2), P.T_lc);
            end
            gr = inf; if TF>0, gr = S.x(i) - S.x(TF) - P.Lc; end
            hold = M(i).hold;
            if P.use_abort && tau < P.f_abort*P.T_lc && TF>0 && gr < P.g_abort
                hold = true;
            elseif gr > P.d0
                hold = false;
            end
            if hold && ~M(i).hold_prev, n_abort = n_abort + 1; end
            M(i).hold = hold;  M(i).hold_prev = hold;
            motion_hold = hold || v_i < P.v_lc_min;
            vTP = v_i; if TP>0, vTP = S.vx(TP); end
            vTF = v_i; if TF>0, vTF = S.vx(TF); end
            vref = 0.5*vTP + 0.5*vTF;
            ref = zeros(P.Np_t,3);
            for kk = 1:P.Np_t
                [Yr,dYr] = quintic_eval(M(i).coef, tau + (kk-1)*P.Ts, P.T_lc);
                ref(kk,:) = [Yr, atan2(dYr, max(v_i,1)), vref];
            end
            xi = [V.vx(i); V.vy(i); V.om(i); V.psi(i); V.y(i)];
            u = ltv_mpc_tracking(xi, u_prev(i,:)', ref, P);
            if M(i).kinematic, u(1) = 0.6*(vref-v_i); end
            if motion_hold, u(2) = -P.kd_pid_r*V.om(i) - 0.6*V.vy(i); end
            if TP>0
                gf_ = S.x(TP) - S.x(i) - P.Lc;
                a_saf = P.kp_c*(gf_-(P.d0+P.tau_h*v_i)) + P.kd_c*(S.vx(TP)-v_i);
                u(1) = min(u(1), a_saf);
            end
            u(1) = min(max(u(1), P.a_min), P.a_max);
            u(2) = min(max(u(2), -P.df_max), P.df_max);
            u_prev(i,:) = u';
            acc(i) = u(1);  handled(i) = true;
            if ~motion_hold, M(i).tau = tau + P.Ts; end
            continue;
        end

        % Gap search and preparation
        if P.use_predictive_gap
            Pgap = P;
            if ecoMode
                Pgap.k_pred = P.eco_k_pred;
                Pgap.tau_h = P.eco_tau_gap;
            end
            okMerge = predictive_gap_ok(S, i, TP, TF, Pgap);
        else
            Pstatic = P; Pstatic.k_pred = 0;
            okMerge = predictive_gap_ok(S, i, TP, TF, Pstatic);
        end
        dist2drop = Xd - V.x(i);

        standardCoop = strcmp(mode,'COOP') && aa <= P.N_prep;
        if isfield(P,'revision_trigger_only') && P.revision_trigger_only
            standardCoop = standardCoop && eco_activation_ok(V,i,TP,TF,dist2drop,P);
        end
        ecoCoop = ecoMode && aa <= P.eco_N_prep && ...
            eco_activation_ok(V, i, TP, TF, dist2drop, P);
        if (standardCoop || ecoCoop) && ~okMerge && dist2drop > P.D_crit
            grp = i;
            if TP>0 && V.cav(TP) && ~committedTF(TP), grp(end+1)=TP; end %#ok<AGROW>
            if TF>0 && V.cav(TF) && ~committedTF(TF), grp(end+1)=TF; end %#ok<AGROW>
            if numel(grp) >= 2 && V.cav(i)
                Pc = P; tref = t;
                if ecoMode
                    Pc = eco_control_params(P);
                    tref = M(i).tcoop;
                    if opt(P,'global_ramp_clock',false),tref=t;end
                    M(i).tcoop = M(i).tcoop + P.Ts;
                end
                a_grp = coop_gap_control(S, i, TP, TF, grp, tref, Pc);
                for gg = 1:numel(grp)
                    j = grp(gg);
                    if ecoMode
                        a_cmd = a_grp(gg);
                        if j==i && P.eco_hold_merge_speed
                            a_cmd = seek_accel(S, i, Xd, P, false);
                        end
                        acc(j) = min(max(a_cmd, P.eco_a_min), P.eco_a_max);
                    else
                        acc(j) = min(max(a_grp(gg), P.a_min), P.a_max);
                    end
                    handled(j) = true;  committedTF(j) = true;
                end
            else
                if TF>0 && V.cav(TF) && ~committedTF(TF)
                    Pc = P;
                    if ecoMode, Pc = eco_control_params(P); end
                    acc(TF) = open_gap_cacc(S, TF, TP, i, Pc);
                    if ecoMode
                        acc(TF) = min(max(acc(TF), P.eco_a_min), P.eco_a_max);
                        M(i).tcoop = M(i).tcoop + P.Ts;
                    end
                    handled(TF) = true;  committedTF(TF) = true;
                end
                acc(i) = seek_accel(S, i, Xd, P, ~okMerge);
                handled(i) = true;
            end
        else
            acc(i) = seek_accel(S, i, Xd, P, ~okMerge);
            handled(i) = true;
        end

        M(i).tw = M(i).tw + P.Ts;
        activeLimit = P.N_lc_active;
        if ecoMode, activeLimit = P.eco_N_lc_active; end
        if okMerge && i==commit_id && n_lc_active < activeLimit
            V.role(i) = 3; observed.role(i)=3; M(i).texec = t;  M(i).tau = 0;
            M(i).coef = quintic_traj(V.y(i), V.vy(i), 0, LANE_Y(2), P.T_lc);
            M(i).kinematic = v_i < P.v_lc_dyn_min;
            u_prev(i,:) = [0 0];
            n_lc_active = n_lc_active + 1;
        end
    end

    % Target-lane following
    for i = 1:n
        if handled(i), continue; end
        if V.lane(i)==1 && V.role(i)~=3
            if V.cav(i), S=ego_estimate(observed,V,i); acc(i) = cacc_accel(S,i,P); else, acc(i) = hdv_accel(V,i,P); end
        else
            S=ego_estimate(observed,V,i); acc(i) = seek_accel(S, i, Xd, P, true);   % fallback
        end
        handled(i) = true;
    end

    % Apply nominal jerk limits before safety filtering.
    for i = 1:n
        if acc(i) >= P.a_min
            acc(i) = min(max(acc(i), V.a(i)-P.j_max*P.Ts), V.a(i)+P.j_max*P.Ts);
            acc(i) = min(max(acc(i), P.a_min), P.a_max);
        else
            acc(i) = max(acc(i), P.a_emg);
        end
    end

    % Longitudinal safety filter
    if P.use_safety_filter
        before_filter=acc;
        % Default: an exact current local-sensing safety layer isolates the
        % network path. A separate noisy-filter arm perturbs this layer too.
        safety_state=V;
        if opt(P,'noisy_safety',false)
            safety_state.x=V.x+position_error(k,:);
            safety_state.vx=max(0,V.vx+speed_error(k,:));
        end
        [acc, nclip] = safety_filter(safety_state, acc, P);
        delta_filter=before_filter-acc; ix=delta_filter>1e-10;
        filter_delta_by_vehicle(k,:)=max(delta_filter,0);
        filter_step_count(k)=sum(ix);filter_step_delta(k)=sum(delta_filter(ix));
        filter_hdv=filter_hdv+sum(ix & ~V.cav); filter_cav=filter_cav+sum(ix & V.cav);
        filter_delta_sum=filter_delta_sum+sum(delta_filter(ix)); filter_count=filter_count+sum(ix);
        if any(ix), filter_delta_max=max(filter_delta_max,max(delta_filter(ix))); end
        n_safety = n_safety + nclip;
    end

    % State update
    for i = 1:n
        a_cmd = acc(i);
        V.a(i) = a_cmd;
        if V.role(i) == 3
            if M(i).kinematic
                [dx, V.vx(i)] = step_longitudinal(V.vx(i), a_cmd, P);
                V.x(i) = V.x(i) + dx;
                [V.y(i), dY] = quintic_eval(M(i).coef, M(i).tau, P.T_lc);
                V.vy(i) = 0;
                V.psi(i) = atan2(dY, max(V.vx(i),1));
                V.om(i) = 0;
            else
                s = step_dyn3([V.x(i) V.y(i) V.vx(i) V.vy(i) V.psi(i) V.om(i)], ...
                              [a_cmd, u_prev(i,2)], P);
                V.x(i)=s(1); V.y(i)=s(2); V.vx(i)=s(3); V.vy(i)=s(4); V.psi(i)=s(5); V.om(i)=s(6);
            end
        else
            [dx, V.vx(i)] = step_longitudinal(V.vx(i), a_cmd, P);
            V.x(i) = V.x(i) + dx;
            V.vy(i)=0; V.om(i)=0; V.psi(i)=0; V.y(i) = LANE_Y(V.lane(i)+1);
        end
        if V.lane(i)==0 && V.role(i)~=3 && V.x(i) > Xd
            V.x(i) = Xd;  V.vx(i) = 0;  V.a(i) = 0;  % Unmerged vehicles stop at the closure
        end
        if V.role(i)==3 && M(i).tau >= P.T_lc && ...
                abs(V.y(i)-LANE_Y(2)) <= P.y_merge_tol && ...
                abs(V.vy(i)) <= P.vy_merge_tol && abs(V.psi(i)) <= P.psi_merge_tol
            V.role(i) = 4;
            V.lane(i) = 1;
            V.vdes(i) = P.v1;
            V.y(i) = LANE_Y(2);
            V.vy(i) = 0;
            V.psi(i) = 0;
            V.om(i) = 0;
            u_prev(i,:) = [0 0];
        end
    end

    % Apply the optional discrete gap correction when enabled.
    pre_gap_violation_steps = pre_gap_violation_steps + count_gap_violations(V, P);
    if P.use_gap_correction
        [V, nfix] = enforce_min_gap(V, P);
        n_gap_corrections = n_gap_corrections + nfix;
    end

    % Accumulate metrics
    recV(k,:)=V.vx; recA(k,:)=V.a; recX(k,:)=V.x; recLane(k,:)=V.lane;
    n_brake = n_brake + sum(V.a < -1.0);
    stop_steps = stop_steps + sum(V.vx < 1.0);
    for i = 1:n
        [jf, gf] = neighbors(V, i, P);
        if jf > 0
            min_gap = min(min_gap, gf);
            if gf < 0.5*P.tau_h*V.vx(i), n_hard = n_hard + 1; end
            if gf < 0, final_gap_violation_steps = final_gap_violation_steps + 1; end
        end
    end
    if logTraj
        traj(k,:,:) = reshape([V.x(:), V.y(:), V.vx(:), V.a(:)],1,n,4); %#ok<AGROW>
    end
    hold_steps(k)=sum([M.hold]);vy_peak(k)=max(abs(V.vy));
    step_seconds(k)=toc(step_clock);
end

% Performance metrics
n0 = sum(V.lane0_init);
n_merged = sum(V.lane==1 & V.lane0_init);
comp_rate = 100 * n_merged / max(n0,1);
vkt = sum(recX(end,:) - recX(1,:)) / 1000;
fg  = fuel_rate(recV, recA, P) * P.Ts;
fuel_g = sum(fg(:));
fuel_L = fuel_g / P.em.rho_f;

% Retain aliases used by the archived records.
R = struct('mode',mode,'pen',pen,'seed',seed, ...
    'n_merge_total', n0, 'n_merged', n_merged, 'comp_rate', comp_rate, ...
    'fuel_L', fuel_L, ...
    'fuel_per_veh', fuel_L/max(n_merged,1)*1000, ...
    'fuel_L100', fuel_L/max(vkt,1e-9)*100, ...
    'co2_gkm', fuel_g*P.em.co2/max(vkt,1e-9), ...
    'v_mean', mean(recV(:)), 'sigma_v', std(recV(:)), ...
    'a_rms', sqrt(mean(recA(:).^2)), ...
    'stop_steps', stop_steps, 'min_gap', min_gap, ...
    'n_hard', n_hard, 'n_brake', n_brake, 'n_abort', n_abort, ...
    'pre_gap_violation_steps', pre_gap_violation_steps, ...
    'final_gap_violation_steps', final_gap_violation_steps, ...
    'n_gap_corrections', n_gap_corrections, 'n_safety', n_safety, ...
    'overlap_steps', final_gap_violation_steps, ...
    'pre_overlap_steps', pre_gap_violation_steps, ...
    'n_projection', n_gap_corrections, ...
    'step_seconds',step_seconds,'filter_hdv',filter_hdv,'filter_cav',filter_cav, ...
    'filter_delta_mean',filter_delta_sum/max(filter_count,1),'filter_delta_max',filter_delta_max, ...
    'cav',V.cav,'filter_delta_by_vehicle',filter_delta_by_vehicle,'filter_step_count',filter_step_count,'filter_step_delta',filter_step_delta,'hold_steps',hold_steps,'vy_peak',vy_peak,'mean_information_age',age_sum/max(age_count,1),'maximum_information_age',age_max,'realized_packet_loss',mean(~packet_received(:,V.cav),'all'),'jerk_rms',sqrt(mean((diff(recA)/P.Ts).^2,'all')),'traj', traj, 'recV', recV, 'recA', recA, 'recX', recX, 'recLane', recLane);
end

% Local functions
function V = init_merge(P, pen, seed, LANE_Y)
rng(seed, 'twister');
n = P.n0 + P.n1;
V.x=zeros(1,n); V.y=zeros(1,n); V.vx=zeros(1,n); V.lane=zeros(1,n); V.vdes=zeros(1,n);
for i = 1:P.n0
    V.x(i) = P.x0_head - (i-1)*P.sp0 + (rand*3-1.5);
    V.y(i) = LANE_Y(1);  V.vx(i) = P.v0 + (rand*1.2-0.6);
    V.lane(i) = 0;  V.vdes(i) = P.v0;
end
for i = 1:P.n1
    j = P.n0 + i;
    V.x(j) = P.x1_head - (i-1)*P.sp1 + (rand*3-1.5);
    V.y(j) = LANE_Y(2);  V.vx(j) = P.v1 + (rand*1.2-0.6);
    V.lane(j) = 1;  V.vdes(j) = P.v1;
end
V.vy=zeros(1,n); V.psi=zeros(1,n); V.om=zeros(1,n); V.a=zeros(1,n);
V.role = zeros(1,n);
V.role(V.lane==0) = 1;
V.lane0_init = (V.lane==0);
% All merging vehicles are controlled; pen applies to the target lane.
V.cav = false(1,n);
V.cav(1:P.n0) = true;
target = P.n0 + (1:P.n1);
ncav = round(pen*P.n1);
idx = target(randperm(P.n1));
V.cav(idx(1:ncav)) = true;
% Seed-paired bounded uniform IDM variation. Parameters are fixed within run.
V.idmT=P.idm.T*ones(1,n);V.idma=P.idm.a*ones(1,n);
V.idmb=P.idm.b*ones(1,n);V.idms0=P.idm.s0*ones(1,n);
variation=opt(P,'hdv_variation',0);
if variation>0
    driver=RandStream('mt19937ar','Seed',seed+300000);hdv=find(~V.cav);
    V.idmT(hdv)=P.idm.T*(1+variation*(2*rand(driver,1,numel(hdv))-1));
    V.idma(hdv)=P.idm.a*(1+variation*(2*rand(driver,1,numel(hdv))-1));
    V.idmb(hdv)=P.idm.b*(1+variation*(2*rand(driver,1,numel(hdv))-1));
    V.idms0(hdv)=P.idm.s0*(1+variation*(2*rand(driver,1,numel(hdv))-1));
    V.vdes(hdv)=V.vdes(hdv).*(1+0.5*variation*(2*rand(driver,1,numel(hdv))-1));
end
end

% Identify target-lane neighbors
function [TP,TF] = lane1_targets(V, i, ~)
TP = -1; TF = -1; dfm = inf; drm = inf;
for j = 1:numel(V.x)
    if V.lane(j)~=1 || j==i, continue; end
    dx = V.x(j) - V.x(i);
    if dx >= 0 && dx < dfm, dfm = dx; TP = j; end
    if dx < 0 && -dx < drm, drm = -dx; TF = j; end
end
end

% Predictive gap admission
% Evaluate front and rear closing-gap margins over the maneuver horizon.
function ok = predictive_gap_ok(V, i, TP, TF, P)
v_i = V.vx(i);  gf_ok = true;  gr_ok = true;
if TP > 0
    gf = V.x(TP) - V.x(i) - P.Lc;
    dv_f = max(v_i - V.vx(TP), 0);
    gf_req = P.d0 + P.tau_h*v_i + P.k_pred*dv_f*P.T_lc;
    gf_ok = gf >= gf_req;
end
if TF > 0
    gr = V.x(i) - V.x(TF) - P.Lc;
    dv_r = max(V.vx(TF) - v_i, 0);
    gr_req = P.d0 + P.tau_h*V.vx(TF) + P.k_pred*dv_r*P.T_lc;
    gr_ok = gr >= gr_req;
end
ok = gf_ok && gr_ok;
end

% Gap-search acceleration
function a = seek_accel(V, i, Xd, P, useDrop)
v = V.vx(i);
[jf0, gf0] = lane0_pred(V, i, P);
vlead = v; if jf0>0, vlead = V.vx(jf0); end
a = idm_pair(v, V.vdes(i), gf0, vlead, P);
if useDrop
    g_drop = Xd - V.x(i) - 0.5*P.Lc;
    a = min(a, idm_pair(v, V.vdes(i), g_drop, 0, P));
end
a = min(max(a, P.a_min), P.a_max);
end

function [jf, gf] = lane0_pred(V, i, P)
jf = -1; gf = inf;
for j = 1:numel(V.x)
    if V.lane(j)~=0 || j==i || V.role(j)==3, continue; end
    dx = V.x(j) - V.x(i);
    if dx > 0 && dx < gf, gf = dx; jf = j; end
end
if jf>0, gf = gf - P.Lc; end
end

% IDM acceleration
function a = idm_pair(v, vdes, gap, v_lead, P)
if isinf(gap)
    a = 0.6*(vdes - v);  return;
end
s = max(gap, 0.3);  dv = v - v_lead;
ss = P.idm.s0 + max(0, v*P.idm.T + v*dv/(2*sqrt(P.idm.a*P.idm.b)));
a = P.idm.a*(1 - (v/max(vdes,1))^P.idm.delta - (ss/s)^2);
end

% Single-CAV gap creation
function a = open_gap_cacc(V, jTF, jTP, ~, P)
v = V.vx(jTF);
g_open = P.g_open_fac * 2*(P.d0 + P.tau_h*v);
if jTP > 0
    gap_ahead = V.x(jTP) - V.x(jTF) - P.Lc;
    a = P.kp_c*(gap_ahead - g_open) + P.kd_c*(V.vx(jTP) - v);
else
    a = 0.4*(V.vdes(jTF) - v);
end
a = min(max(a, P.a_min), P.a_max);
end

function yes = eco_activation_ok(V, i, TP, TF, dist2drop, P)
density = 1000/P.sp1;
has_controlled_neighbor = (TP>0 && V.cav(TP)) || (TF>0 && V.cav(TF));
if isfield(P,'revision_no_trigger') && P.revision_no_trigger
    yes=has_controlled_neighbor && V.cav(i) && dist2drop>P.D_crit; return;
end
yes = density >= P.eco_density_min && dist2drop <= P.eco_trigger_dist && ...
      dist2drop > P.D_crit && V.cav(i) && has_controlled_neighbor;
end

function Pc = eco_control_params(P)
Pc = P;
Pc.T_ramp = P.eco_T_ramp;
Pc.g_open_fac = P.eco_g_open_fac;
Pc.tau_h = P.eco_tau_gap;
Pc.qv = P.eco_qv;
Pc.qa = P.eco_qa;
Pc.ru = P.eco_ru;
Pc.qg = P.eco_qg;
Pc.qr = P.eco_qr;
Pc.qc = P.eco_qc;
Pc.kp_c = P.eco_kp_gap;
Pc.kd_c = P.eco_kd_gap;
end

% Multi-vehicle gap-creation MPC
function a_grp = coop_gap_control(V, iHC, TP, TF, grp, t, P)
nc = numel(grp);  loc = zeros(1,numel(V.x)); loc(grp)=1:nc;  nn=3*nc;
tvec = (0:P.Np_g-1)'*P.Ts;
st = zeros(nn,1);
for a_=1:nc
    j=grp(a_); st(3*a_-2:3*a_) = [V.x(j); V.vx(j); V.a(j)];
end
v1m = mean(V.vx(V.lane==1));
QT = struct('c',{},'w',{},'r',{});
for a_=1:nc
    j=grp(a_);
    c=zeros(nn,1); c(3*a_-1)=1;
    if j==iHC, rv=v1m; else, rv=V.vdes(j); end
    QT(end+1)=struct('c',c,'w',P.qv,'r',rv*ones(P.Np_g,1)); %#ok<AGROW>
    c=zeros(nn,1); c(3*a_)=1;
    QT(end+1)=struct('c',c,'w',P.qa,'r',zeros(P.Np_g,1)); %#ok<AGROW>
end
if TP>0, sTP = V.x(TP) + V.vx(TP)*tvec; else, sTP = zeros(P.Np_g,1); end
if TF>0, sTF = V.x(TF) + V.vx(TF)*tvec; else, sTF = zeros(P.Np_g,1); end
v_hc = V.vx(iHC);
g_des = P.g_open_fac * 2*(P.d0 + P.tau_h*v_hc);
if TP>0 && TF>0, g0 = V.x(TP)-V.x(TF)-P.Lc; else, g0 = g_des; end
rr = min((t + tvec)/P.T_ramp, 1);
cg = zeros(nn,1);  rg = g0 + (g_des - g0)*rr + P.Lc;
if TP>0 && loc(TP)>0, cg(3*loc(TP)-2)=cg(3*loc(TP)-2)+1; else, rg = rg - sTP; end
if TF>0 && loc(TF)>0, cg(3*loc(TF)-2)=cg(3*loc(TF)-2)-1; else, rg = rg + sTF; end
if any(cg~=0), QT(end+1)=struct('c',cg,'w',P.qg,'r',rg); end
ca=zeros(nn,1); ra=zeros(P.Np_g,1);
ca(3*loc(iHC)-2)=ca(3*loc(iHC)-2)+1;
if TP>0 && loc(TP)>0, ca(3*loc(TP)-2)=ca(3*loc(TP)-2)-0.5; else, ra=ra+0.5*sTP; end
if TF>0 && loc(TF)>0, ca(3*loc(TF)-2)=ca(3*loc(TF)-2)-0.5; else, ra=ra+0.5*sTF; end
QT(end+1)=struct('c',ca,'w',P.qc,'r',ra);
for j=[TP TF]
    if j>0 && loc(j)>0
        c=zeros(nn,1); c(3*loc(j)-1)=1; c(3*loc(iHC)-1)=-1;
        QT(end+1)=struct('c',c,'w',P.qr,'r',zeros(P.Np_g,1)); %#ok<AGROW>
    end
end
CN = cell(P.Np_g,1);
for kk=1:P.Np_g
    rows = zeros(0,3);
    for a_=1:nc
        j=grp(a_);
        [jf,~] = lane1_pred_any(V, j, P);
        if jf<=0, continue; end
        if j==TP && jf==TF, continue; end
        rhs = P.Lc + P.d0;
        if loc(jf)>0
            rows(end+1,:)=[loc(jf), a_, rhs]; %#ok<AGROW>
        else
            rows(end+1,:)=[-1, a_, rhs-(V.x(jf)+V.vx(jf)*tvec(kk))]; %#ok<AGROW>
        end
    end
    CN{kk}=rows;
end
u = gap_mpc(st, QT, CN, nc, P);
a_grp = zeros(1,nc);
for a_=1:nc, a_grp(a_) = V.a(grp(a_)) + u(a_)*P.Ts; end
end

function [jf, gf] = lane1_pred_any(V, i, P)
jf=-1; gf=inf;
for j=1:numel(V.x)
    if abs(V.y(j)-V.y(i))>P.b || j==i, continue; end
    dx = V.x(j)-V.x(i);
    if dx>0 && dx<gf, gf=dx; jf=j; end
end
if jf>0, gf=gf-P.Lc; end
end

% Barrier-based acceleration bound
% Apply the barrier-based acceleration bound, limited by a_emg.
function [acc, nclip] = safety_filter(V, acc, P)
n = numel(V.x);
tau_s = P.tau_safe;  alpha = 1.0;
nclip = 0;
for i = 1:n
    if opt(P,'cav_only_safety',false) && ~V.cav(i),continue;end
    [jf, g] = front_eff(V, i, P);
    if jf<=0, continue; end
    vi = V.vx(i);  vj = V.vx(jf);
    h = g - tau_s*vi - P.d0 - P.safety_buffer;  % Spacing barrier
    a_cap = ((vj - vi) + alpha*h) / tau_s;  % Acceleration bound for dh/dt >= -alpha*h
    if acc(i) > a_cap
        acc(i) = a_cap;
        nclip = nclip + 1;
    end
    if acc(i) < P.a_emg, acc(i) = P.a_emg; end
end
end

function [jf, g] = front_eff(V, i, P)
% A straddling vehicle is visible from both adjacent lanes.
n = numel(V.x); jf = -1; best = inf;
for j = 1:n
    if j==i, continue; end
    if ~shares_longitudinal_path(V, i, j, P), continue; end
    dx = V.x(j) - V.x(i);
    if dx > 0 && dx < best, best = dx; jf = j; end
end
g = best - P.Lc;
end

% Optional discrete gap correction
% Correct discrete positions only when the optional correction is enabled.
function [V, nfix] = enforce_min_gap(V, P)
LANE_Y = [P.lane_w/2, P.lane_w*1.5];
dmin = P.Lc + P.g_gap_correction;
nfix = 0;
for ln = 1:2
    idx = find(abs(V.y - LANE_Y(ln)) <= P.b);
    if numel(idx) < 2, continue; end
    [~,o] = sort(V.x(idx), 'descend');  idx = idx(o);
    for a = 2:numel(idx)
        f = idx(a-1);  r = idx(a);
        if V.x(f) - V.x(r) < dmin
            V.x(r) = V.x(f) - dmin;
            if V.vx(r) > V.vx(f), V.vx(r) = V.vx(f); end
            nfix = nfix + 1;
        end
    end
end
end

function n = count_gap_violations(V, P)
% Count negative-gap samples before optional position correction.
n = 0;
for i = 1:numel(V.x)
    [jf, gf] = neighbors(V, i, P);
    if jf > 0 && gf < 0, n = n + 1; end
end
end

% MPC, dynamics, fuel calculation and quadratic-program solver.
function [jf, gf, jr, gr] = neighbors(V, i, P)
jf = -1; gf = inf; jr = -1; gr = inf;
for j = 1:numel(V.x)
    if j == i || ~shares_longitudinal_path(V, i, j, P), continue; end
    dx = V.x(j) - V.x(i);
    if dx > 0 && dx < gf, gf = dx; jf = j; end
    if dx < 0 && -dx < gr, gr = -dx; jr = j; end
end
gf = gf - P.Lc;  gr = gr - P.Lc;
end

function yes = shares_longitudinal_path(V, follower, other, P)
yes = abs(V.y(other)-V.y(follower)) <= P.b || ...
      (V.lane(follower)==1 && V.role(other)==3);
end

function a = cacc_accel(V, i, P)
[jf, gf] = neighbors(V, i, P);
a_spd = 0.6*(V.vdes(i) - V.vx(i));
if jf <= 0, a = min(max(a_spd,P.a_min),P.a_max); return; end
e = gf - (P.d0 + P.tau_h*V.vx(i));
a_gap = P.kp_c*e + P.kd_c*(V.vx(jf) - V.vx(i));
a = min(max(min(a_spd, a_gap), P.a_min), P.a_max);
end

function a = hdv_accel(V, i, P)
[jf, gf] = neighbors(V, i, P);
v = V.vx(i);
if jf <= 0, a = min(max(0.6*(V.vdes(i)-v), P.a_min), P.a_max); return; end
dv = v - V.vx(jf);  s = max(gf, 0.5);
ss = V.idms0(i) + max(0, v*V.idmT(i) + v*dv/(2*sqrt(V.idma(i)*V.idmb(i))));
a = V.idma(i)*(1 - (v/V.vdes(i))^P.idm.delta - (ss/s)^2);
a = min(max(a, P.a_min), P.a_max);
end

function u = gap_mpc(x0, QT, CN, nc, P)
persistent CACHE
if isempty(CACHE), CACHE = containers.Map('KeyType','double','ValueType','any'); end
Np = P.Np_g; Nc = P.Nc_g; nn = 3*nc;
if CACHE.isKey(nc)
    M = CACHE(nc);  Sx = M.Sx;  Su = M.Su;
else
    A = [1 P.Ts P.Ts^2/2; 0 1 P.Ts; 0 0 1];  B = [0;0;P.Ts];
    Ab = kron(eye(nc), A);  Bb = kron(eye(nc), B);
    Sx = zeros(Np*nn, nn);  Su = zeros(Np*nn, Nc*nc);
    pw = cell(Np+1,1);  pw{1} = eye(nn);
    for k = 1:Np, pw{k+1} = pw{k}*Ab; end
    for k = 1:Np
        Sx((k-1)*nn+1:k*nn, :) = pw{k+1};
        for j = 1:min(k,Nc)
            Su((k-1)*nn+1:k*nn, (j-1)*nc+1:j*nc) = pw{k-j+1}*Bb;
        end
    end
    CACHE(nc) = struct('Sx',Sx,'Su',Su);
end
Qs = zeros(nn,nn);  qb = zeros(Np*nn,1);
for m = 1:numel(QT)
    Qs = Qs + QT(m).w * (QT(m).c * QT(m).c');
    for k = 1:Np
        qb((k-1)*nn+1:k*nn) = qb((k-1)*nn+1:k*nn) - QT(m).w*QT(m).r(k)*QT(m).c;
    end
end
Qb = kron(eye(Np), Qs);
H = 2*(Su'*Qb*Su + P.ru*eye(Nc*nc));
f = 2*(Su'*(Qb*(Sx*x0) + qb));
SxX = Sx*x0;  Ar = [];  br = [];
for kk = P.k_con
    if kk > Np, continue; end
    rg = (kk-1)*nn+1 : kk*nn;
    Sk = SxX(rg);  Suk = Su(rg,:);
    rows = CN{kk};
    for r = 1:size(rows,1)
        il = rows(r,1);  ifo = rows(r,2);  rhs = rows(r,3);
        c = zeros(nn,1);
        if il > 0, c(3*il-2) = c(3*il-2) + 1; end
        c(3*ifo-2) = c(3*ifo-2) - 1;
        c(3*ifo-1) = c(3*ifo-1) - P.tau_h;
        Ar(end+1,:) = -(c'*Suk); br(end+1,1) = c'*Sk - rhs; %#ok<AGROW>
    end
    for a_ = 1:nc
        for sw = 1:2
            if sw==1, idx = 3*a_-1; hi = P.v_max; lo = P.v_min;
            else,     idx = 3*a_;   hi = P.a_max; lo = P.a_min; end
            e = zeros(nn,1); e(idx) = 1;
            Ar(end+1,:) =  (e'*Suk); br(end+1,1) = hi - e'*Sk; %#ok<AGROW>
            Ar(end+1,:) = -(e'*Suk); br(end+1,1) = e'*Sk - lo; %#ok<AGROW>
        end
    end
end
nu = Nc*nc;
Ar = [Ar; eye(nu); -eye(nu)];
br = [br; P.j_max*ones(nu,1); -P.j_min*ones(nu,1)];
U = qp_solve(H, f, Ar, br);
u = U(1:nc);
end

function u = ltv_mpc_tracking(xi, u_prev, ref, P)
Ts = P.Ts; Np = P.Np_t; Nc = P.Nc_t;
[Ac, Bc] = jac3dof(xi, P);
Ad = eye(5) + Ac*Ts;  Bd = Bc*Ts;
dk = (f3dof(xi, u_prev, P) - Ac*xi - Bc*u_prev)*Ts;
nx = 5; nu = 2;
Aa = [Ad Bd; zeros(nu,nx) eye(nu)];
Ba = [Bd; eye(nu)];
da = [dk; zeros(nu,1)];
Cz = zeros(3, nx+nu);  Cz(1,5) = 1;  Cz(2,4) = 1;  Cz(3,1) = 1;
za = [xi; u_prev];
Sx = zeros(3*Np, nx+nu);  Su = zeros(3*Np, nu*Nc);  Sd = zeros(3*Np,1);
pw = cell(Np+1,1);  pw{1} = eye(nx+nu);
for k = 1:Np, pw{k+1} = pw{k}*Aa; end
acc = zeros(nx+nu,1);
for k = 1:Np
    acc = Aa*acc + da;
    Sx(3*k-2:3*k,:) = Cz*pw{k+1};
    Sd(3*k-2:3*k)   = Cz*acc;
    for j = 1:min(k,Nc)
        Su(3*k-2:3*k, (j-1)*nu+1:j*nu) = Cz*pw{k-j+1}*Ba;
    end
end
Q = kron(eye(Np), diag([P.qY, P.qpsi, P.qvx]));
R = kron(eye(Nc), diag([P.r_ax, P.r_df]));
E = Sx*za + Sd - reshape(ref', [], 1);
H = 2*(Su'*Q*Su + R);
f = 2*(Su'*Q*E);
nU = nu*Nc;
dmax = repmat([P.j_max*Ts; P.ddf_max], Nc, 1);
Ar = [eye(nU); -eye(nU)];  br = [dmax; dmax];
for j = 1:Nc
    Sc = zeros(nu, nU);
    for jj = 1:j, Sc(:, (jj-1)*nu+1:jj*nu) = eye(nu); end
    Ar = [Ar; Sc; -Sc]; %#ok<AGROW>
    br = [br; [P.a_max-u_prev(1); P.df_max-u_prev(2)];
              [u_prev(1)-P.a_min; P.df_max+u_prev(2)]]; %#ok<AGROW>
end
dU = qp_solve(H, f, Ar, br);
u = u_prev + dU(1:nu);
u(1) = min(max(u(1), P.a_min), P.a_max);
u(2) = min(max(u(2), -P.df_max), P.df_max);
end

function dx = f3dof(xi, u, P)
vx = max(xi(1),1); vy = xi(2); om = xi(3); psi = xi(4);
ax = u(1); df = u(2);
dx = [ ax + vy*om;
      -(P.Cf+P.Cr)/(P.m*vx)*vy + ((P.lr*P.Cr-P.lf*P.Cf)/(P.m*vx) - vx)*om + P.Cf/P.m*df;
       (P.lr*P.Cr-P.lf*P.Cf)/(P.Iz*vx)*vy - (P.lf^2*P.Cf+P.lr^2*P.Cr)/(P.Iz*vx)*om + P.lf*P.Cf/P.Iz*df;
       om;
       vx*sin(psi) + vy*cos(psi)];
end

function [Ac, Bc] = jac3dof(xi, P)
vx = max(xi(1),1); vy = xi(2); om = xi(3); psi = xi(4);
Ac = zeros(5); Bc = zeros(5,2);
Ac(1,2) = om;  Ac(1,3) = vy;
Ac(2,1) = (P.Cf+P.Cr)/(P.m*vx^2)*vy - (P.lr*P.Cr-P.lf*P.Cf)/(P.m*vx^2)*om - om;
Ac(2,2) = -(P.Cf+P.Cr)/(P.m*vx);
Ac(2,3) = (P.lr*P.Cr-P.lf*P.Cf)/(P.m*vx) - vx;
Ac(3,1) = -(P.lr*P.Cr-P.lf*P.Cf)/(P.Iz*vx^2)*vy + (P.lf^2*P.Cf+P.lr^2*P.Cr)/(P.Iz*vx^2)*om;
Ac(3,2) = (P.lr*P.Cr-P.lf*P.Cf)/(P.Iz*vx);
Ac(3,3) = -(P.lf^2*P.Cf+P.lr^2*P.Cr)/(P.Iz*vx);
Ac(4,3) = 1;
Ac(5,1) = sin(psi);  Ac(5,2) = cos(psi);  Ac(5,4) = vx*cos(psi) - vy*sin(psi);
Bc(1,1) = 1;  Bc(2,2) = P.Cf/P.m;  Bc(3,2) = P.lf*P.Cf/P.Iz;
end

function c = quintic_traj(y0, vy0, ay0, yf, T)
M = [0 0 0 0 0 1; 0 0 0 0 1 0; 0 0 0 2 0 0;
     T^5 T^4 T^3 T^2 T 1;
     5*T^4 4*T^3 3*T^2 2*T 1 0;
     20*T^3 12*T^2 6*T 2 0 0];
c = (M \ [y0; vy0; ay0; yf; 0; 0])';
end

function [Y, dY, ddY] = quintic_eval(c, t, T)
t = min(max(t,0), T);
Y   = c*[t^5; t^4; t^3; t^2; t; 1];
dY  = c*[5*t^4; 4*t^3; 3*t^2; 2*t; 1; 0];
ddY = c*[20*t^3; 12*t^2; 6*t; 2; 0; 0];
end

function s = step_dyn3(s, u, P)
x=s(1); y=s(2); vx=s(3); vy=s(4); psi=s(5); om=s(6);
ax=u(1); df=u(2);  h = P.Ts/P.n_sub;
for q = 1:P.n_sub
    vxs = max(vx,1);
    af = df - atan2(vy + P.lf*om, vxs);
    ar = -atan2(vy - P.lr*om, vxs);
    Fyf = 2*P.Cf*af;  Fyr = 2*P.Cr*ar;
    dvx = ax + vy*om;
    dvy = (Fyf*cos(df) + Fyr)/P.m - vx*om;
    dom = (P.lf*Fyf*cos(df) - P.lr*Fyr)/P.Iz;
        road_vx = vx*cos(psi) - vy*sin(psi);
        x = x + max(road_vx,0)*h;
    y = y + (vx*sin(psi) + vy*cos(psi))*h;
    vx = min(max(vx + dvx*h, 0), P.v_max);
    vy = vy + dvy*h;  psi = psi + om*h;  om = om + dom*h;
end
s = [x y vx vy psi om];
end

function [dx, v_next] = step_longitudinal(v, a, P)
v_next = min(max(v + a*P.Ts, 0), P.v_max);
dx = 0.5*(v + v_next)*P.Ts;
end

function fr = fuel_rate(v, a, P)
p = max((P.m*a + P.m*P.em.g*P.em.Cr + 0.5*P.em.rho*P.em.Cd*P.em.Af*v.^2).*v, 0);
fr = P.em.idle + p/(P.em.eta*P.em.LHV)*1000;
end

function U = qp_solve(H, f, A, b)
nnH = size(H,1);
if any(~isfinite(H(:))) || any(~isfinite(f(:)))
    U = zeros(nnH,1); return;  % Numerical fallback
end
H = 0.5*(H + H');
reg = 1e-8;  L = [];
while true
    [L, p] = chol(H + reg*eye(nnH), 'lower');
    if p == 0, break; end
    reg = reg*10;
    if reg > 1e6, U = -f./max(diag(H),1e-6); return; end  % Diagonal fallback
end
Hi_f = L' \ (L \ f);
U = -Hi_f;
if isempty(A) || all(A*U - b <= 1e-9), return; end
HiAt = L' \ (L \ A');
D = A*HiAt;  d = A*U - b;
step = 1/max(norm(D,2), 1e-9);
lam = zeros(size(A,1),1);  z = lam;  tk = 1;
for it = 1:220
    g = D*z - d;
    lam_n = max(z - step*g, 0);
    tk_n = 0.5*(1 + sqrt(1 + 4*tk^2));
    z = lam_n + (tk-1)/tk_n*(lam_n - lam);
    if max(abs(lam_n - lam)) < 1e-10, lam = lam_n; break; end
    lam = lam_n;  tk = tk_n;
end
U = -(Hi_f + HiAt*lam);
end

function value=opt(P,name,default)
if isfield(P,name),value=P.(name);else,value=default;end
end
function S=ego_estimate(observed,truth,i)
S=observed;
for field={'x','vx','a','y','vy','psi','om','role','lane'}
    name=field{1};S.(name)(i)=truth.(name)(i);
end
end
