function S=compact_result(R,P,job)
% Scalar outcomes and time series needed for reproducible comparisons.
S=struct();S.job=job;S.n=P.n0+P.n1;S.mode=R.mode;S.pen=R.pen;S.seed=R.seed;
fields={'comp_rate','n_merged','n_merge_total','fuel_L','fuel_L100','v_mean','sigma_v','a_rms','min_gap','final_gap_violation_steps','filter_hdv','filter_cav','filter_delta_mean','filter_delta_max','jerk_rms','n_abort','closure_clamps','closure_overshoot','closure_front_clearance','filter_infeasible','filter_infeasible_steps','minimum_cap','standstill_violations','headway_violations','minimum_headway_margin','dense_min_gap','dense_overlap','dense_standstill','delay_vehicle_s','merging_delay_s'};
for j=1:numel(fields),f=fields{j};S.(f)=R.(f);end
S.acceleration_min=min(R.actual_acceleration,[],'all');S.acceleration_max=max(R.actual_acceleration,[],'all');
S.jerk_abs_max=max(abs(R.actual_jerk),[],'all');
S.command_acceleration_min=min(R.recA,[],'all');S.command_acceleration_max=max(R.recA,[],'all');
S.command_jerk_abs_max=max(abs(diff(R.recA)/P.Ts),[],'all');
S.qp=R.qp;S.completion_time=R.completion_time;
S.completion_curve=R.completion_curve;S.residual_queue=R.residual_queue;
S.cumulative_fuel_L=R.cumulative_fuel_L;S.delay_curve=R.delay_curve;
S.fuel_by_vehicle_L=R.fuel_by_vehicle_L;S.final_x=R.recX(end,1:P.n0);
S.final_y=R.recY(end,1:P.n0);S.final_speed=R.recV(end,1:P.n0);S.final_role=R.recRole(end,1:P.n0);
S.hold_vehicle_s=sum(R.hold_steps)*P.Ts;
S.closure_interventions=R.closure_interventions;
S.closure_infeasible=R.closure_infeasible;
S.closure_boundary_samples=R.closure_boundary_samples;
S.stop_steps=R.stop_steps;
S.stopped_vehicle_s=R.stop_steps*P.Ts;
S.actual_acceleration_rms=sqrt(mean(R.actual_acceleration.^2,'all'));
S.actual_jerk_rms=sqrt(mean(R.actual_jerk.^2,'all'));
S.mean_information_age=R.mean_information_age;
S.maximum_information_age=R.maximum_information_age;
S.realized_packet_loss=R.realized_packet_loss;
end
