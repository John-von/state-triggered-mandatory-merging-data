function P=tuning_candidate(P,candidate)
% Same four configuration candidates and seed budget for both activation rules.
switch candidate
 case 1
 case 2
  P.eco_T_ramp=6;
 case 3
  P.eco_T_ramp=12;
 case 4
  P.eco_T_ramp=6;P.eco_qg=4;P.eco_qc=3;
 otherwise
  error('Unknown tuning candidate');
end
end
