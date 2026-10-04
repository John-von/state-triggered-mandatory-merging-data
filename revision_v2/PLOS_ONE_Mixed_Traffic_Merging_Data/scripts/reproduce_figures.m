%% Reproduce the eight result figures from the archived public data
clear; close all; clc;

scriptDir = fileparts(mfilename('fullpath'));
repoDir = fileparts(scriptDir);
rawDir = fullfile(repoDir,'data','raw');
summaryDir = fullfile(repoDir,'data','summary');
trajectoryDir = fullfile(repoDir,'data','trajectories');
figDir = fullfile(repoDir,'reproduced_figures');
if ~exist(figDir,'dir'), mkdir(figDir); end

set(groot,'defaultAxesFontName','Times New Roman');
set(groot,'defaultTextFontName','Times New Roman');
set(groot,'defaultAxesFontSize',11.5);
set(groot,'defaultTextFontSize',12);
set(groot,'defaultAxesLineWidth',0.8);
set(groot,'defaultLineLineWidth',1.4);

colors = [0.68 0.20 0.17; 0.10 0.42 0.30; 0.24 0.32 0.58];
labels = {'Safety-priority cooperation','State-triggered cooperation','Passive merging'};
modes = [1 3 2];

baseline = readmatrix(fullfile(rawDir,'joint_raw.csv'),'NumHeaderLines',1);
eco = readmatrix(fullfile(rawDir,'eco_joint_raw.csv'),'NumHeaderLines',1);
raw = [baseline; eco];
vsCoop = readmatrix(fullfile(summaryDir,'eco_vs_coop_paired_summary.csv'),'NumHeaderLines',1);
vsPassive = readmatrix(fullfile(summaryDir,'eco_vs_passive_paired_summary.csv'),'NumHeaderLines',1);

%% Figure 1: representative longitudinal trajectories
load(fullfile(trajectoryDir,'eco_typical_trajectory.mat'), ...
    'ecoTypical','coopTypical','passiveTypical','penetration','P');
typical = {coopTypical,ecoTypical,passiveTypical};
t = (0:size(ecoTypical.recX,1)-1)'*P.Ts;
assert(all(diff(ecoTypical.recX,1,1)>=-1e-9,'all') && ...
       all(diff(coopTypical.recX,1,1)>=-1e-9,'all') && ...
       all(diff(passiveTypical.recX,1,1)>=-1e-9,'all'), ...
       'Representative trajectories contain backward longitudinal motion.');

f = figure('Color','w','Position',[100 100 1200 980],'ToolBar','none','MenuBar','none');
tl = tiledlayout(3,1,'Padding','compact','TileSpacing','compact');
lineColors = turbo(P.n0);
for s = 1:3
    ax = nexttile; hold(ax,'on');
    for j = 1:P.n0
        plot(ax,t,typical{s}.recX(:,j),'Color',lineColors(j,:),'LineWidth',0.85);
    end
    yline(ax,P.X_drop,'k--','Closure','LabelHorizontalAlignment','left', ...
        'LineWidth',1.0,'HandleVisibility','off');
    ylabel(ax,'Longitudinal coordinate (m)');
    text(ax,0.015,0.96,sprintf('(%c) %s',char(96+s),labels{s}), ...
        'Units','normalized','VerticalAlignment','top','FontSize',12, ...
        'FontWeight','bold','BackgroundColor','w','Margin',2);
    grid(ax,'on'); box(ax,'on');
end
xlabel(tl,'Time (s)');
export_clean(f,fullfile(figDir,'Figure_1.png'));

%% Figure 2: representative speed, queue, fuel, and traveled distance
f = figure('Color','w','Position',[100 100 1160 760],'ToolBar','none','MenuBar','none');
tl = tiledlayout(2,2,'Padding','compact','TileSpacing','compact');
metricSeries = cell(3,4);
for s = 1:3
    R = typical{s};
    metricSeries{s,1} = mean(R.recV,2);
    metricSeries{s,2} = sum(R.recV<1,2);
    metricSeries{s,3} = cumulative_fuel(R.recV,R.recA,P);
    metricSeries{s,4} = (sum(R.recX,2)-sum(R.recX(1,:)))/1000;
end
yLabels = {'Fleet mean speed (m/s)','Stopped vehicles', ...
    'Cumulative fuel (L)','Cumulative distance (veh km)'};
panelLabels = {'(a)','(b)','(c)','(d)'};
for panel = 1:4
    ax = nexttile; hold(ax,'on');
    for s = 1:3
        if panel == 2
            stairs(ax,t,metricSeries{s,panel},'Color',colors(s,:));
        else
            plot(ax,t,metricSeries{s,panel},'Color',colors(s,:));
        end
    end
    xlabel(ax,'Time (s)'); ylabel(ax,yLabels{panel});
    if panel == 1
        text(ax,0.97,0.95,panelLabels{panel},'Units','normalized', ...
            'HorizontalAlignment','right','VerticalAlignment','top', ...
            'FontSize',12,'FontWeight','bold','BackgroundColor','w','Margin',2);
    else
        text(ax,0.03,0.95,panelLabels{panel},'Units','normalized', ...
            'VerticalAlignment','top','FontSize',12,'FontWeight','bold', ...
            'BackgroundColor','w','Margin',2);
    end
    grid(ax,'on'); box(ax,'on');
    if panel == 1, legend(ax,labels,'Location','best'); end
end
export_clean(f,fullfile(figDir,'Figure_2.png'));

%% Figure 3: density effects at 75% target-lane CAV penetration
% Group by the exact initial spacing. The archived baseline and ECO files
% store the corresponding densities at slightly different precision.
spacings = unique(raw(:,2),'stable');
densities = 1000./spacings;
metricCols = [9 11 13 21];
metricNames = {'Fuel per 100 km (L/100 km)','Speed standard deviation (m/s)', ...
    'Stopped-vehicle time (veh s)','Mean speed (m/s)'};
panelLabels = {'(a)','(b)','(c)','(d)'};
f = figure('Color','w','Position',[100 100 1160 800],'ToolBar','none','MenuBar','none');
tl = tiledlayout(2,2,'Padding','compact','TileSpacing','compact');
legendHandles = gobjects(1,3);
for panel = 1:4
    ax = nexttile; hold(ax,'on');
    for s = 1:3
        [mu,ci] = grouped_stats(raw,2,spacings,3,0.75,4,modes(s),metricCols(panel));
        h = errorbar(ax,densities,mu,ci,marker_for(s),'Color',colors(s,:), ...
            'MarkerFaceColor','w','CapSize',5);
        if panel == 1
            legendHandles(s) = h;
        end
    end
    xlabel(ax,'Target-lane density (veh/km)'); ylabel(ax,metricNames{panel});
    text(ax,0.03,0.95,panelLabels{panel},'Units','normalized', ...
        'VerticalAlignment','top','FontSize',12,'FontWeight','bold', ...
        'BackgroundColor','w','Margin',2);
    grid(ax,'on'); box(ax,'on');
end
lg = legend(legendHandles,labels,'Orientation','horizontal','NumColumns',3);
lg.Layout.Tile = 'north';
export_clean(f,fullfile(figDir,'Figure_3.png'));

%% Figure 4: penetration effects at 41.7 veh/km
penetrations = unique(raw(:,3),'stable');
f = figure('Color','w','Position',[100 100 1160 760],'ToolBar','none','MenuBar','none');
tl = tiledlayout(2,2,'Padding','compact','TileSpacing','compact');
for panel = 1:4
    ax = nexttile; hold(ax,'on');
    for s = 1:3
        [mu,ci] = grouped_stats(raw,3,penetrations,2,24,4,modes(s),metricCols(panel));
        errorbar(ax,100*penetrations,mu,ci,marker_for(s),'Color',colors(s,:), ...
            'MarkerFaceColor','w','CapSize',5);
    end
    xlabel(ax,'Target-lane CAV penetration (%)'); ylabel(ax,metricNames{panel});
    text(ax,0.03,0.95,panelLabels{panel},'Units','normalized', ...
        'VerticalAlignment','top','FontSize',12,'FontWeight','bold', ...
        'BackgroundColor','w','Margin',2);
    grid(ax,'on'); box(ax,'on');
    if panel == 1, legend(ax,labels,'Location','best'); end
end
export_clean(f,fullfile(figDir,'Figure_4.png'));

%% Figure 5: five co-benefit metrics relative to safety-priority cooperation
k = unique(vsCoop(:,1),'stable');
pens = unique(vsCoop(:,3),'stable');
mapCols = [5 7 9 11 13];
mapLabels = {'(a)','(b)','(c)','(d)','(e)'};
mapMetricLabels = {'Fuel-intensity saving (%)','Speed-disturbance reduction (%)', ...
    'Acceleration-RMS reduction (%)','Stopped-time reduction (veh s)', ...
    'Mean-speed gain (%)'};
formats = {'%.1f','%.1f','%.1f','%.0f','%.1f'};
f = figure('Color','w','Position',[100 100 1360 900],'ToolBar','none','MenuBar','none');
tl = tiledlayout(2,6,'Padding','compact','TileSpacing','loose');
tileStarts = [1 3 5 8 10];
for panel = 1:5
    Z = summary_grid(vsCoop,k,pens,mapCols(panel));
    plot_joint_map(tl,tileStarts(panel),k,pens,Z,mapLabels{panel},mapMetricLabels{panel},formats{panel});
end
export_clean(f,fullfile(figDir,'Figure_5.png'));

%% Figure 6: explicit comparison against both baselines
nonzeroC = vsCoop(vsCoop(:,3)>0,:);
nonzeroP = vsPassive(vsPassive(:,3)>0,:);
markerSize = 35 + 70*nonzeroC(:,3);
f = figure('Color','w','Position',[100 100 1320 450],'ToolBar','none','MenuBar','none');
tl = tiledlayout(1,3,'Padding','compact','TileSpacing','compact');
ax = nexttile; hold(ax,'on');
scatter(ax,nonzeroC(:,5),nonzeroC(:,13),markerSize,nonzeroC(:,1),'filled', ...
    'MarkerEdgeColor',[0.18 0.18 0.18]);
xline(ax,0,'k:'); yline(ax,0,'k:'); xlabel(ax,'Fuel-intensity saving vs COOP (%)');
 ylabel(ax,'Mean-speed gain (%)');
 text(ax,0.03,0.95,'(a)','Units','normalized','VerticalAlignment','top', ...
     'FontSize',12,'FontWeight','bold','BackgroundColor','w','Margin',2);
grid(ax,'on'); box(ax,'on'); cb=colorbar(ax); cb.Label.String='Density (veh/km)';

ax = nexttile; hold(ax,'on');
scatter(ax,nonzeroP(:,5),nonzeroP(:,13),markerSize,nonzeroP(:,1),'filled', ...
    'MarkerEdgeColor',[0.18 0.18 0.18]);
xline(ax,0,'k:'); yline(ax,0,'k:'); xlabel(ax,'Fuel-intensity saving vs PASSIVE (%)');
 ylabel(ax,'Mean-speed gain (%)');
 text(ax,0.03,0.95,'(b)','Units','normalized','VerticalAlignment','top', ...
     'FontSize',12,'FontWeight','bold','BackgroundColor','w','Margin',2);
grid(ax,'on'); box(ax,'on'); cb=colorbar(ax); cb.Label.String='Density (veh/km)';

ax = nexttile; hold(ax,'on');
scatter(ax,nonzeroC(:,5),nonzeroC(:,15),markerSize,nonzeroC(:,1),'filled', ...
    'MarkerEdgeColor',[0.18 0.18 0.18]);
xline(ax,0,'k:'); yline(ax,0,'k:'); xlabel(ax,'Fuel-intensity saving vs COOP (%)');
 ylabel(ax,'Total-fuel saving vs COOP (%)');
 text(ax,0.03,0.95,'(c)','Units','normalized','VerticalAlignment','top', ...
     'FontSize',12,'FontWeight','bold','BackgroundColor','w','Margin',2);
grid(ax,'on'); box(ax,'on'); cb=colorbar(ax); cb.Label.String='Density (veh/km)';
export_clean(f,fullfile(figDir,'Figure_6.png'));

%% Figure 7: paired 95% confidence intervals in representative cells
selected = [25.000000 1.00; 35.714286 0.50; 41.666667 0.75; 50.000000 1.00];
selectedLabels = {'25.0/100','35.7/50','41.7/75','50.0/100'};
valueCols = [5 7 9 11 13 15];
ciCols = [6 8 10 12 14 16];
yLabels = {'Fuel-intensity saving (%)','Speed-disturbance reduction (%)', ...
    'Acceleration-RMS reduction (%)','Stopped-time reduction (veh s)', ...
    'Mean-speed gain (%)','Total-fuel saving (%)'};
panelLabels = {'(a)','(b)','(c)','(d)','(e)','(f)'};
f = figure('Color','w','Position',[100 100 1360 800],'ToolBar','none','MenuBar','none');
tl = tiledlayout(2,3,'Padding','compact','TileSpacing','compact');
for panel = 1:6
    ax = nexttile; hold(ax,'on');
    [values,cis] = selected_summary(vsCoop,selected,valueCols(panel),ciCols(panel));
    errorbar(ax,1:size(selected,1),values,cis,'o','Color',colors(2,:), ...
        'MarkerFaceColor','w','LineWidth',1.5,'CapSize',7);
    yline(ax,0,'k:');
    xlim(ax,[0.8 4.2]);
    set(ax,'XTick',1:size(selected,1),'XTickLabel',selectedLabels,'XTickLabelRotation',18);
    ylabel(ax,yLabels{panel});
    text(ax,0.03,0.95,panelLabels{panel},'Units','normalized', ...
        'VerticalAlignment','top','FontSize',12,'FontWeight','bold', ...
        'BackgroundColor','w','Margin',2);
    grid(ax,'on'); box(ax,'on');
end
xlabel(tl,'Target-lane density (veh/km) / CAV penetration (%)');
export_clean(f,fullfile(figDir,'Figure_7.png'));

%% Figure 8: safety ablation for the proposed strategy
A = readmatrix(fullfile(summaryDir,'eco_safety_ablation_summary.csv'),'NumHeaderLines',1);
ablationLabels = {'Full safeguards','No speed prediction','No barrier filter','All three disabled'};
x = 1:4;
f = figure('Color','w','Position',[100 100 1320 450],'ToolBar','none','MenuBar','none');
tl = tiledlayout(1,3,'Padding','compact','TileSpacing','compact');
ax = nexttile;
bar(ax,x,log10(A(:,13)+1),'FaceColor',colors(1,:));
set(ax,'XTick',x,'XTickLabel',ablationLabels,'XTickLabelRotation',18);
ylabel(ax,'log_{10}(gap violations + 1)');
text(ax,0.03,0.95,'(a)','Units','normalized','VerticalAlignment','top', ...
    'FontSize',12,'FontWeight','bold','BackgroundColor','w','Margin',2);
grid(ax,'on'); box(ax,'on');
ax = nexttile;
bar(ax,x,A(:,9),'FaceColor',colors(3,:));
set(ax,'XTick',x,'XTickLabel',ablationLabels,'XTickLabelRotation',18);
yline(ax,0,'k:'); ylabel(ax,'Minimum net gap (m)');
text(ax,0.03,0.95,'(b)','Units','normalized','VerticalAlignment','top', ...
    'FontSize',12,'FontWeight','bold','BackgroundColor','w','Margin',2);
grid(ax,'on'); box(ax,'on');
ax = nexttile;
bar(ax,x,A(:,14),'FaceColor',colors(2,:));
set(ax,'XTick',x,'XTickLabel',ablationLabels,'XTickLabelRotation',18);
ylabel(ax,'Mean interventions per run');
text(ax,0.03,0.95,'(c)','Units','normalized','VerticalAlignment','top', ...
    'FontSize',12,'FontWeight','bold','BackgroundColor','w','Margin',2);
grid(ax,'on'); box(ax,'on');
export_clean(f,fullfile(figDir,'Figure_8.png'));

fprintf('Generated eight ECO result figures in %s\n',figDir);

function [mu,ci] = grouped_stats(R,xCol,xValues,fixedCol,fixedValue,modeCol,modeValue,metricCol)
mu = zeros(size(xValues)); ci = zeros(size(xValues));
for i = 1:numel(xValues)
    mask = abs(R(:,xCol)-xValues(i))<1e-6 & abs(R(:,fixedCol)-fixedValue)<1e-9 & R(:,modeCol)==modeValue;
    values = R(mask,metricCol);
    assert(numel(values)==20,'Each plotted operating cell must contain 20 seeds.');
    mu(i) = mean(values); ci(i) = ci95(values);
end
end

function marker = marker_for(index)
markers = {'o-','d-','s-'}; marker = markers{index};
end

function values = cumulative_fuel(v,a,P)
power = max((P.m*a + P.m*P.em.g*P.em.Cr + ...
    0.5*P.em.rho*P.em.Cd*P.em.Af*v.^2).*v,0);
rate = P.em.idle + power/(P.em.eta*P.em.LHV)*1000;
values = cumsum(sum(rate,2)*P.Ts)/P.em.rho_f;
end

function Z = summary_grid(S,k,pens,column)
Z = zeros(numel(pens),numel(k));
for ki = 1:numel(k)
    for pi = 1:numel(pens)
        row = S(abs(S(:,1)-k(ki))<1e-6 & abs(S(:,3)-pens(pi))<1e-9,:);
        assert(size(row,1)==1,'Summary must contain one row per operating cell.');
        Z(pi,ki) = row(1,column);
    end
end
end

function plot_joint_map(tl,tileIndex,k,pens,Z,panelLabel,metricLabel,fmt)
ax = nexttile(tl,tileIndex,[1 2]);
imagesc(ax,1:numel(k),1:numel(pens),Z);
set(ax,'YDir','normal','XTick',1:numel(k),'XTickLabel',compose('%.1f',k), ...
    'YTick',1:numel(pens),'YTickLabel',compose('%d',round(100*pens)));
xlabel(ax,'Density (veh/km)'); ylabel(ax,'CAV penetration (%)');
text(ax,-0.15,1.03,panelLabel,'Units','normalized','VerticalAlignment','bottom', ...
    'FontSize',12,'FontWeight','bold','Clipping','off');
cb = colorbar(ax); cb.Label.String = metricLabel;
box(ax,'on'); apply_diverging_axis(ax,Z(:));
lim = max(abs(Z(:))); if lim<eps, lim=1; end
for r = 1:size(Z,1)
    for c = 1:size(Z,2)
        color = 'k'; if abs(Z(r,c))>0.58*lim, color='w'; end
        displayedValue = Z(r,c);
        if contains(fmt,'%.0f')
            zeroThreshold = 0.5;
        else
            zeroThreshold = 0.05;
        end
        if abs(displayedValue) < zeroThreshold, displayedValue = 0; end
        text(ax,c,r,sprintf(fmt,displayedValue),'HorizontalAlignment','center', ...
            'FontSize',10.5,'FontWeight','bold','Color',color);
    end
end
end

function [values,cis] = selected_summary(S,selected,valueCol,ciCol)
values = zeros(size(selected,1),1); cis = values;
for i = 1:size(selected,1)
    row = S(abs(S(:,1)-selected(i,1))<1e-4 & abs(S(:,3)-selected(i,2))<1e-9,:);
    assert(size(row,1)==1,'Selected summary cell is missing or duplicated.');
    values(i) = row(valueCol); cis(i) = row(ciCol);
end
end

function apply_diverging_axis(ax,values)
lim = max(abs(values(:))); if lim<eps, lim=1; end
clim(ax,[-lim lim]); colormap(ax,diverging_map(256));
end

function cmap = diverging_map(n)
anchors = [0.68 0.20 0.17; 0.97 0.97 0.95; 0.10 0.42 0.30];
x = [0 0.5 1]; xi = linspace(0,1,n); cmap = zeros(n,3);
for c = 1:3, cmap(:,c)=interp1(x,anchors(:,c),xi,'linear'); end
end

function value = ci95(x)
value = tinv(0.975,numel(x)-1)*std(x,0)/sqrt(numel(x));
end

function export_clean(f,path)
axs = findall(f,'Type','axes');
for i = 1:numel(axs)
    axs(i).FontSize = 11.5;
    axs(i).XLabel.FontSize = 12;
    axs(i).YLabel.FontSize = 12;
    try, axs(i).Toolbar.Visible='off'; catch, end
end
legs = findall(f,'Type','Legend');
for i = 1:numel(legs), legs(i).FontSize = 11; end
cbs = findall(f,'Type','ColorBar');
for i = 1:numel(cbs)
    cbs(i).FontSize = 11;
    cbs(i).Label.FontSize = 11;
end
drawnow; exportgraphics(f,path,'Resolution',320,'BackgroundColor','white'); close(f);
end
