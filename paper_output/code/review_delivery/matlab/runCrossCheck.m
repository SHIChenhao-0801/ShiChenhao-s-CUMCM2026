function runSummary = runCrossCheck(outputDirectory)
%RUNCROSSCHECK 用独立 MATLAB 实现核验 A 题 Q1--Q4 的离散模型。
% 在 MATLAB GUI 中调用本函数；函数自身不能证明 GUI 操作或人工审查。
% 单位：秒、米、开尔文、kg 水/kg 干物质；默认 N=40 是跨语言核验网格，
% 不能代替正式 N3200/N6400 生产结果或空间收敛验证。
% 示例：runCrossCheck('D:/Document/数学建模/2026CUMCM/paper_output/qa/matlab_crosscheck_20260911')

    sourcePath = [mfilename('fullpath'), '.m'];
    projectRoot = fileparts(sourcePath);
    for parentIndex = 1:4
        projectRoot = fileparts(projectRoot);
    end
    if nargin < 1 || strlength(string(outputDirectory)) == 0
        runStamp = char(datetime('now', 'Format', 'yyyyMMdd_HHmmss_SSS'));
        outputDirectory = fullfile(projectRoot, 'paper_output', 'qa', ...
            ['matlab_crosscheck_', runStamp]);
    end
    outputDirectory = char(outputDirectory);
    % Java 仅用于路径规范化和 SHA256，不参与模型计算。
    outputFile = java.io.File(outputDirectory);
    projectRootFile = java.io.File(projectRoot);
    outputDirectory = char(outputFile.getCanonicalPath());
    canonicalRoot = char(projectRootFile.getCanonicalPath());
    if ~startsWith(lower(outputDirectory), [lower(canonicalRoot), filesep])
        error('CrossCheck:WorkspaceBoundary', '输出必须位于本次 2026CUMCM 子工作区。');
    end
    summaryPath = fullfile(outputDirectory, 'runSummary.json');
    if isfile(summaryPath)
        error('CrossCheck:ExistingRun', '该目录已有运行记录，请使用新的输出目录以保留证据。');
    end
    if ~isfolder(outputDirectory)
        mkdir(outputDirectory);
    end
    logPath = fullfile(outputDirectory, 'runLog.txt');
    logFileId = fopen(logPath, 'w', 'n', 'UTF-8');
    if logFileId < 0
        error('CrossCheck:LogOpen', '无法创建运行日志。');
    end
    logCleanup = onCleanup(@() fclose(logFileId)); %#ok<NASGU>
    runTimer = tic;
    runSummary = struct('schemaVersion', 1, 'status', 'RUNNING', ...
        'startedAtUtc', utcStamp(), 'finishedAtUtc', '', 'elapsedSec', [], ...
        'matlabVersion', version, 'matlabRelease', version('-release'), ...
        'computer', computer, 'sourcePath', sourcePath, ...
        'sourceSha256', sha256File(sourcePath), 'outputDirectory', outputDirectory, ...
        'guiReproduced', [], 'guiEvidenceStatus', 'external_observation_required', ...
        'humanReviewStatus', 'pending', 'caseResults', {{}}, 'exception', []);
    settings = struct('intervalCount', 40, 'nodeCount', 41, 'relativeTolerance', 1e-10, ...
        'temperatureAbsoluteTolerance', 1e-10, 'moistureAbsoluteTolerance', 1e-12, ...
        'earlyMaxStepSec', 2, 'lateMaxStepSec', 120, 'horizonSec', 240*3600, ...
        'initialTemperatureK', 301.15, 'initialMoisture', 2.55, ...
        'initialRadiusM', 0.02, 'fixedLengthM', 0.25, ...
        'heatTransferCoefficient', 25, 'massTransferCoefficient', 8e-7, ...
        'dryThreshold', 0.15, 'environmentSwitchSec', 14400, ...
        'tailTemperatureK', 323.15, 'tailEquilibriumMoisture', 0.05, ...
        'solver', 'ode15s_default_NDF', 'jacobianMode', 'JPattern_finite_difference', ...
        'waterFaceScheme', 'Kirchhoff', 'heatFaceScheme', 'harmonic', ...
        'coefficientFloor', 1e-12, 'latentHeatIncluded', false);
    runSummary.settings = settings;
    writeJson(summaryPath, runSummary);
    logLine(logFileId, 'START %s | MATLAB %s | output=%s', ...
        runSummary.startedAtUtc, version, outputDirectory);
    try
        environmentPath = fullfile(projectRoot, 'paper_output', 'data_cleaned', 'A_environment_observed.csv');
        radiusPath = fullfile(projectRoot, 'paper_output', 'data_cleaned', 'A_radius_observed.csv');
        inputData.environment = readtable(environmentPath, 'VariableNamingRule', 'preserve');
        inputData.radius = readtable(radiusPath, 'VariableNamingRule', 'preserve');
        validateInputs(inputData);
        runSummary.inputs = {fileRecord(environmentPath), fileRecord(radiusPath)};
        caseNames = {'Q1', 'Q23', 'Q4'};
        for caseIndex = 1:numel(caseNames)
            caseName = caseNames{caseIndex};
            logLine(logFileId, 'CASE_START %s at %s', caseName, utcStamp());
            caseTimer = tic;
            caseResult = solveSingleCase(caseName, inputData, settings, logFileId);
            caseResult.elapsedSec = toc(caseTimer);
            caseResult.finishedAtUtc = utcStamp();
            casePath = fullfile(outputDirectory, [caseName, '_crossCheck.json']);
            writeJson(casePath, caseResult);
            sampleTable = makeSampleTable(caseResult);
            writetable(sampleTable, fullfile(outputDirectory, [caseName, '_samples.csv']));
            if strcmp(caseName, 'Q23')
                % Q2 与 Q3 共用从 t=0 的附录3轨迹，导出同源但分问的查阅入口。
                sampleTable.question(:) = "Q2";
                writetable(sampleTable, fullfile(outputDirectory, 'Q2_samples.csv'));
                sampleTable.question(:) = "Q3";
                writetable(sampleTable, fullfile(outputDirectory, 'Q3_samples.csv'));
            end
            runSummary.caseResults{end+1} = caseResult;
            writeJson(summaryPath, runSummary);
            logLine(logFileId, 'CASE_END %s | elapsed=%.6f s | event=%.12g s | massResidual=%.3g', ...
                caseName, caseResult.elapsedSec, scalarOrNaN(caseResult.eventSec), ...
                caseResult.diagnostics.maxMassBalanceAbs);
        end
        if ~strcmp(runSummary.sourceSha256, sha256File(sourcePath))
            error('CrossCheck:SourceChanged', '源码在运行中改变，本轮不能作为固定版本证据。');
        end
        for inputIndex = 1:numel(runSummary.inputs)
            record = runSummary.inputs{inputIndex};
            if ~strcmp(record.sha256, sha256File(record.path))
                error('CrossCheck:InputChanged', '输入在运行中改变：%s', record.path);
            end
        end
        runSummary.status = 'COMPLETED_NUMERICAL_CHECKS';
        runSummary.finishedAtUtc = utcStamp();
        runSummary.elapsedSec = toc(runTimer);
        writeJson(summaryPath, runSummary);
        logLine(logFileId, 'FINISH %s | elapsed=%.6f s | humanReview=pending', ...
            runSummary.finishedAtUtc, runSummary.elapsedSec);
    catch runError
        runSummary.status = 'FAILED';
        runSummary.finishedAtUtc = utcStamp();
        runSummary.elapsedSec = toc(runTimer);
        runSummary.exception = struct('identifier', runError.identifier, ...
            'message', runError.message, 'report', getReport(runError, 'extended', 'hyperlinks', 'off'));
        writeJson(summaryPath, runSummary);
        logLine(logFileId, 'FAILED %s\n%s', runSummary.finishedAtUtc, runSummary.exception.report);
        rethrow(runError);
    end
end

function caseResult = solveSingleCase(caseName, inputData, settings, logFileId)
    caseStartedAtUtc = utcStamp();
    nodeCount = settings.nodeCount;
    materialX = linspace(0, 1, nodeCount)';
    deltaX = 1/settings.intervalCount;
    faceX = [0; (materialX(1:end-1)+materialX(2:end))/2; 1];
    cellWeights = diff(faceX.^2)/2;
    internalFaceX = faceX(2:end-1);
    stateCount = 2*nodeCount+1;
    initialState = zeros(stateCount, 1);
    initialState(1:2:end-1) = settings.initialTemperatureK;
    initialState(2:2:end-1) = settings.initialMoisture;
    absoluteTolerance = repmat(settings.moistureAbsoluteTolerance, stateCount, 1);
    absoluteTolerance(1:2:end-1) = settings.temperatureAbsoluteTolerance;
    jacobianPattern = makeJacobianPattern(nodeCount);
    baseOptions = odeset('RelTol', settings.relativeTolerance, 'AbsTol', absoluteTolerance, ...
        'JPattern', jacobianPattern, 'Vectorized', 'off', 'Stats', 'off');
    if strcmp(caseName, 'Q1')
        horizonSec = 1800;
        dryDensityInitial = 820/(1+settings.initialMoisture);
    elseif strcmp(caseName, 'Q4')
        horizonSec = settings.horizonSec;
        dryDensityInitial = (760+90*settings.initialMoisture)/(1+settings.initialMoisture);
    else
        horizonSec = settings.horizonSec;
        dryDensityInitial = (650+128*settings.initialMoisture)/(1+settings.initialMoisture);
    end
    dryMassKg = dryDensityInitial*pi*settings.initialRadiusM^2*settings.fixedLengthM;
    endPoints = unique([0, min(settings.environmentSwitchSec, horizonSec), horizonSec]);
    solutions = {};
    warningRecords = {};
    eventSec = [];
    rhsEvaluations = 0;
    for segmentIndex = 1:numel(endPoints)-1
        leftSec = endPoints(segmentIndex);
        rightSec = endPoints(segmentIndex+1);
        if leftSec < settings.environmentSwitchSec
            maxStepSec = settings.earlyMaxStepSec;
        else
            maxStepSec = settings.lateMaxStepSec;
        end
        segmentOptions = odeset(baseOptions, 'MaxStep', maxStepSec);
        if ~strcmp(caseName, 'Q1')
            segmentOptions = odeset(segmentOptions, 'Events', @dryEvent);
        end
        lastwarn('');
        segment = ode15s(@balanceRhs, [leftSec, rightSec], initialState, segmentOptions);
        [warningText, warningId] = lastwarn;
        recordWarning(warningText, warningId, leftSec, rightSec);
        solutions{end+1} = segment;
        hasEvent = isfield(segment, 'xe') && ~isempty(segment.xe);
        if hasEvent
            eventSec = segment.xe(end);
            initialState = segment.ye(:, end);
            tailEndSec = ceil(eventSec)+1;
            % 真正续算到事件后的整数秒；禁止靠插值外推声称严格达标。
            tailOptions = odeset(baseOptions, 'MaxStep', 1, 'Events', []);
            lastwarn('');
            tail = ode15s(@balanceRhs, [eventSec, tailEndSec], initialState, tailOptions);
            [warningText, warningId] = lastwarn;
            recordWarning(warningText, warningId, eventSec, tailEndSec);
            assertReached(tail, tailEndSec);
            solutions{end+1} = tail;
            break;
        end
        assertReached(segment, rightSec);
        initialState = segment.y(:, end);
    end
    if ~strcmp(caseName, 'Q1') && isempty(eventSec)
        error('CrossCheck:NoDryEvent', '%s 在240小时内没有找到干燥事件。', caseName);
    end
    endSec = solutions{end}.x(end);
    rawSampleTimes = [0, 1800, 10800];
    rawSampleTimes = rawSampleTimes(rawSampleTimes <= endSec);
    sampleTimesSec = unique([rawSampleTimes, eventSec, endSec]);
    sampleStates = evaluatePieces(solutions, sampleTimesSec);
    sampleX = [0, 0.25, 0.5, 0.75, 1];
    temperatureK = interp1(materialX, sampleStates(1:2:end-1, :), sampleX, 'linear')';
    moisture = interp1(materialX, sampleStates(2:2:end-1, :), sampleX, 'linear')';
    sampleRadiusM = zeros(size(sampleTimesSec));
    sampleTypes = strings(size(sampleTimesSec));
    for sampleIndex = 1:numel(sampleTimesSec)
        sampleRadiusM(sampleIndex) = radiusAt(sampleTimesSec(sampleIndex));
        if sampleTimesSec(sampleIndex) == 0
            sampleTypes(sampleIndex) = "initial";
        elseif ~isempty(eventSec) && sampleTimesSec(sampleIndex) == eventSec
            sampleTypes(sampleIndex) = "criticalEvent";
        elseif ~isempty(eventSec) && sampleTimesSec(sampleIndex) == endSec
            sampleTypes(sampleIndex) = "postEventIntegerSecond";
        else
            sampleTypes(sampleIndex) = "fixedTime";
        end
    end
    diagnostic = struct('minMoisture', Inf, 'maxMoisture', -Inf, ...
        'minTemperatureK', Inf, 'maxTemperatureK', -Inf, 'minDiffusivity', Inf, ...
        'positiveProperties', true, 'maxMassBalanceAbs', 0, ...
        'maxRadialMoistureIncrease', -Inf, 'acceptedTimePoints', 0);
    for pieceIndex = 1:numel(solutions)
        acceptedStates = solutions{pieceIndex}.y;
        acceptedTemperature = acceptedStates(1:2:end-1, :);
        acceptedMoisture = acceptedStates(2:2:end-1, :);
        [density, heatCapacity, conductivity, diffusivity] = materialProperties(acceptedTemperature, acceptedMoisture, caseName);
        diagnostic.minMoisture = min(diagnostic.minMoisture, min(acceptedMoisture, [], 'all'));
        diagnostic.maxMoisture = max(diagnostic.maxMoisture, max(acceptedMoisture, [], 'all'));
        diagnostic.minTemperatureK = min(diagnostic.minTemperatureK, min(acceptedTemperature, [], 'all'));
        diagnostic.maxTemperatureK = max(diagnostic.maxTemperatureK, max(acceptedTemperature, [], 'all'));
        diagnostic.minDiffusivity = min(diagnostic.minDiffusivity, min(diffusivity, [], 'all'));
        diagnostic.positiveProperties = diagnostic.positiveProperties && ...
            all(density > 0 & heatCapacity > 0 & conductivity > 0 & diffusivity > 0, 'all');
        massResidual = 2*cellWeights'*acceptedMoisture+acceptedStates(end, :)-settings.initialMoisture;
        diagnostic.maxMassBalanceAbs = max(diagnostic.maxMassBalanceAbs, max(abs(massResidual)));
        diagnostic.maxRadialMoistureIncrease = max(diagnostic.maxRadialMoistureIncrease, ...
            max(diff(acceptedMoisture, 1, 1), [], 'all'));
        diagnostic.acceptedTimePoints = diagnostic.acceptedTimePoints+numel(solutions{pieceIndex}.x);
    end
    finalState = evaluatePieces(solutions, endSec);
    diagnostic.finalMaxMoisture = max(finalState(2:2:end-1));
    diagnostic.strictlyDryAtEnd = diagnostic.finalMaxMoisture < settings.dryThreshold;
    diagnostic.rhsEvaluations = rhsEvaluations;
    diagnostic.radiusExtrapolationUsed = strcmp(caseName, 'Q4') && endSec > inputData.radius.time_s(end);
    diagnostic.checkScope = 'accepted ode15s states; not a continuous exact-solution error bound';
    if diagnostic.minMoisture < -1e-8 || ~diagnostic.positiveProperties
        error('CrossCheck:PhysicalRange', '%s 的接受状态违反物性正值或水分范围。', caseName);
    end
    if diagnostic.maxMassBalanceAbs > 1e-6
        error('CrossCheck:MassBalance', '%s 的离散干基质量守恒残差超限。', caseName);
    end
    if ~strcmp(caseName, 'Q1') && ~diagnostic.strictlyDryAtEnd
        error('CrossCheck:StrictDryness', '%s 的事件后原精度maxC没有严格小于0.15。', caseName);
    end
    caseResult = struct('question', caseName, 'startedAtUtc', caseStartedAtUtc, ...
        'intervalCount', settings.intervalCount, 'eventSec', eventSec, ...
        'eventHours', eventSec/3600, 'endSec', endSec, 'dryMassKg', dryMassKg, ...
        'endTimeConvention', 'ceil(eventSec)+1; actual integration, not earliest integer-second claim', ...
        'sampleTimesSec', sampleTimesSec, 'sampleTypes', sampleTypes, 'sampleMaterialX', sampleX, ...
        'sampleRadiusM', sampleRadiusM, 'temperatureK', temperatureK, ...
        'temperatureC', temperatureK-273.15, 'moistureDryBasis', moisture, ...
        'fullMaterialX', materialX', 'fullStateBySample', sampleStates', ...
        'stateOrder', 'T0,C0,T1,C1,...,TN,CN,cumulativeDryBasisLoss', ...
        'meanMoisture', 2*cellWeights'*sampleStates(2:2:end-1, :), ...
        'cumulativeLoss', sampleStates(end, :), 'diagnostics', diagnostic, ...
        'warnings', {warningRecords}, 'warningCapture', 'last warning per segment; not all warning messages', ...
        'humanReviewStatus', 'pending');

    function derivative = balanceRhs(timeSec, state)
        rhsEvaluations = rhsEvaluations+1;
        temperature = state(1:2:end-1);
        waterContent = state(2:2:end-1);
        [density, heatCapacity, conductivity, ~] = materialProperties(temperature, waterContent, caseName);
        radiusM = radiusAt(timeSec);
        [airTemperatureK, equilibriumMoisture] = environmentAt(timeSec);
        heatFlux = zeros(nodeCount+1, 1);
        waterFlux = zeros(nodeCount+1, 1);
        faceConductivity = 2*conductivity(1:end-1).*conductivity(2:end) ./ ...
            max(conductivity(1:end-1)+conductivity(2:end), realmin);
        heatFlux(2:end-1) = internalFaceX.*faceConductivity.*diff(temperature)/deltaX;
        if strcmp(caseName, 'Q1')
            moistureExponent = 0.89;
            diffusionPrefactor = 7e-9;
            thermalFactor = ones(nodeCount-1, 1);
        elseif strcmp(caseName, 'Q4')
            moistureExponent = 0.30;
            diffusionPrefactor = 4.2e-4;
            thermalFactor = exp(-3850./((temperature(1:end-1)+temperature(2:end))/2));
        else
            moistureExponent = 0.45;
            diffusionPrefactor = 2.4e-3;
            thermalFactor = exp(-3850./((temperature(1:end-1)+temperature(2:end))/2));
        end
        positiveMoisture = max(waterContent, settings.coefficientFloor);
        % E1(z)=expint(z)=-Ei(-z)，不是 Python scipy.special.expi 的同名替代。
        kirchhoffPotential = positiveMoisture.*exp(-moistureExponent./positiveMoisture) ...
            -moistureExponent*expint(moistureExponent./positiveMoisture);
        potentialDifference = diff(kirchhoffPotential);
        meanFaceMoisture = (positiveMoisture(1:end-1)+positiveMoisture(2:end))/2;
        moistureDifference = diff(positiveMoisture);
        closePair = abs(moistureDifference) < 1e-7*max(meanFaceMoisture, 1e-3);
        potentialDifference(closePair) = exp(-moistureExponent./meanFaceMoisture(closePair)) ...
            .*moistureDifference(closePair);
        % 温度因子在面上求值，不放入势函数再差分，以免引入虚构Soret项。
        waterFlux(2:end-1) = internalFaceX.*diffusionPrefactor.*thermalFactor.*potentialDifference/deltaX;
        waterFlux(end) = -settings.massTransferCoefficient*radiusM*(waterContent(end)-equilibriumMoisture);
        heatFlux(end) = -settings.heatTransferCoefficient*radiusM*(temperature(end)-airTemperatureK);
        derivative = zeros(stateCount, 1);
        derivative(1:2:end-1) = diff(heatFlux)./(radiusM^2*cellWeights.*density.*heatCapacity);
        % Q4网格随材料同比收缩；固定长度并另守恒干物质，故无附加网格平流。
        derivative(2:2:end-1) = diff(waterFlux)./(radiusM^2*cellWeights);
        derivative(end) = 2*settings.massTransferCoefficient/radiusM*(waterContent(end)-equilibriumMoisture);
    end

    function radiusM = radiusAt(timeSec)
        if strcmp(caseName, 'Q4')
            boundedTimeSec = min(max(timeSec, inputData.radius.time_s(1)), inputData.radius.time_s(end));
            radiusM = interp1(inputData.radius.time_s, inputData.radius.radius_m, boundedTimeSec, 'linear');
        else
            radiusM = settings.initialRadiusM;
        end
    end

    function [airTemperatureK, equilibriumMoisture] = environmentAt(timeSec)
        % 4h以后50摄氏度/0.05为闭合假设；不是额外实测数据。
        if timeSec > inputData.environment.time_s(end)
            airTemperatureK = settings.tailTemperatureK;
            equilibriumMoisture = settings.tailEquilibriumMoisture;
        else
            boundedTimeSec = max(timeSec, inputData.environment.time_s(1));
            airTemperatureK = interp1(inputData.environment.time_s, inputData.environment.temperature_K, boundedTimeSec, 'linear');
            equilibriumMoisture = interp1(inputData.environment.time_s, inputData.environment.air_moisture_kg_per_kg, boundedTimeSec, 'linear');
        end
    end

    function [eventValue, isTerminal, direction] = dryEvent(~, state)
        eventValue = max(state(2:2:end-1))-settings.dryThreshold;
        isTerminal = 1;
        direction = -1;
    end

    function recordWarning(warningText, warningId, leftSec, rightSec)
        if ~isempty(warningText)
            warningRecords{end+1} = struct('identifier', warningId, 'message', warningText, ...
                'segmentStartSec', leftSec, 'segmentTargetSec', rightSec);
            logLine(logFileId, 'WARNING %s [%s] %s', caseName, warningId, warningText);
        end
    end
end

function [density, heatCapacity, conductivity, diffusivity] = materialProperties(temperatureK, waterContent, caseName)
    if any(~isfinite(temperatureK) | temperatureK <= 0, 'all') || any(~isfinite(waterContent), 'all')
        error('CrossCheck:InvalidState', '遇到非有限状态或非正绝对温度。');
    end
    % 仅对Newton探测点的系数作正延拓，不截断积分状态。
    positiveMoisture = max(waterContent, 1e-12);
    wetFraction = positiveMoisture./(1+positiveMoisture);
    switch caseName
        case 'Q1'
            density = 820*ones(size(waterContent));
            heatCapacity = 2600*ones(size(waterContent));
            conductivity = 0.36*ones(size(waterContent));
            diffusivity = 7e-9*exp(-0.89./positiveMoisture);
        case 'Q23'
            density = 650+128*positiveMoisture;
            heatCapacity = 1450+2736*wetFraction;
            conductivity = 0.21+0.38*wetFraction;
            diffusivity = 2.4e-3*exp(-0.45./positiveMoisture-3850./temperatureK);
        case 'Q4'
            density = 760+90*positiveMoisture;
            heatCapacity = 1850+2150*wetFraction;
            conductivity = 0.12+0.20*wetFraction;
            diffusivity = 4.2e-4*exp(-0.30./positiveMoisture-3850./temperatureK);
        otherwise
            error('CrossCheck:Question', '不支持的问题名：%s', caseName);
    end
end

function jacobianPattern = makeJacobianPattern(nodeCount)
    stateCount = 2*nodeCount+1;
    jacobianPattern = sparse(stateCount, stateCount);
    for nodeIndex = 1:nodeCount
        rowIndices = 2*nodeIndex-1:2*nodeIndex;
        for neighborIndex = max(1, nodeIndex-1):min(nodeCount, nodeIndex+1)
            columnIndices = 2*neighborIndex-1:2*neighborIndex;
            jacobianPattern(rowIndices, columnIndices) = 1;
        end
    end
    jacobianPattern(end, 2*nodeCount) = 1;
end

function sampleStates = evaluatePieces(solutions, queryTimesSec)
    sampleStates = zeros(size(solutions{1}.y, 1), numel(queryTimesSec));
    for queryIndex = 1:numel(queryTimesSec)
        queryTimeSec = queryTimesSec(queryIndex);
        foundPiece = false;
        for pieceIndex = 1:numel(solutions)
            piece = solutions{pieceIndex};
            if queryTimeSec >= piece.x(1) && queryTimeSec <= piece.x(end)
                sampleStates(:, queryIndex) = deval(piece, queryTimeSec);
                foundPiece = true;
                break;
            end
        end
        if ~foundPiece
            error('CrossCheck:DenseDomain', '请求的时刻 %.17g 不在已积分分段内。', queryTimeSec);
        end
    end
end

function sampleTable = makeSampleTable(caseResult)
    sampleCount = numel(caseResult.sampleTimesSec);
    radialCount = numel(caseResult.sampleMaterialX);
    question = repmat(string(caseResult.question), sampleCount*radialCount, 1);
    sampleType = repelem(caseResult.sampleTypes(:), radialCount);
    timeSec = repelem(caseResult.sampleTimesSec(:), radialCount);
    materialX = repmat(caseResult.sampleMaterialX(:), sampleCount, 1);
    currentRadiusM = repelem(caseResult.sampleRadiusM(:), radialCount);
    radiusM = currentRadiusM.*materialX;
    temperatureK = reshape(caseResult.temperatureK', [], 1);
    temperatureC = temperatureK-273.15;
    moistureDryBasis = reshape(caseResult.moistureDryBasis', [], 1);
    sampleTable = table(question, sampleType, timeSec, materialX, radiusM, currentRadiusM, ...
        temperatureK, temperatureC, moistureDryBasis);
end

function validateInputs(inputData)
    environmentColumns = {'time_s', 'temperature_K', 'air_moisture_kg_per_kg'};
    radiusColumns = {'time_s', 'radius_m'};
    if ~all(ismember(environmentColumns, inputData.environment.Properties.VariableNames)) || ...
            ~all(ismember(radiusColumns, inputData.radius.Properties.VariableNames))
        error('CrossCheck:InputColumns', '清洗CSV字段不符合正式输入接口。');
    end
    environmentValues = inputData.environment{:, environmentColumns};
    radiusValues = inputData.radius{:, radiusColumns};
    if any(~isfinite(environmentValues), 'all') || any(~isfinite(radiusValues), 'all') || ...
            any(diff(environmentValues(:, 1)) <= 0) || any(diff(radiusValues(:, 1)) <= 0) || ...
            environmentValues(1, 1) ~= 0 || radiusValues(1, 1) ~= 0 || ...
            environmentValues(end, 1) ~= 14400 || radiusValues(end, 1) ~= 259200 || ...
            any(environmentValues(:, 2) <= 0) || any(environmentValues(:, 3) < 0) || ...
            any(radiusValues(:, 2) <= 0) || abs(radiusValues(1, 2)-0.02) > 1e-14
        error('CrossCheck:InputAudit', '时间、数值范围或初始半径审计未通过。');
    end
end

function assertReached(solution, requestedEndSec)
    if abs(solution.x(end)-requestedEndSec) > 1e-7
        error('CrossCheck:SolverStopped', 'ode15s 实际终点 %.17g 未到请求终点 %.17g。', solution.x(end), requestedEndSec);
    end
    if any(~isfinite(solution.y), 'all')
        error('CrossCheck:NonfiniteSolution', 'ode15s 返回非有限接受状态。');
    end
end

function record = fileRecord(filePath)
    fileInfo = dir(filePath);
    record = struct('path', filePath, 'bytes', fileInfo.bytes, 'sha256', sha256File(filePath));
end

function hashText = sha256File(filePath)
    fileId = fopen(filePath, 'r');
    if fileId < 0
        error('CrossCheck:HashRead', '无法读取待哈希文件：%s', filePath);
    end
    fileCleanup = onCleanup(@() fclose(fileId)); %#ok<NASGU>
    fileBytes = fread(fileId, Inf, '*uint8');
    digest = java.security.MessageDigest.getInstance('SHA-256');
    digest.update(typecast(fileBytes, 'int8'));
    digestBytes = typecast(digest.digest(), 'uint8');
    hashText = lower(reshape(dec2hex(digestBytes, 2)', 1, []));
end

function writeJson(filePath, value)
    fileId = fopen(filePath, 'w', 'n', 'UTF-8');
    if fileId < 0
        error('CrossCheck:JsonWrite', '无法写入JSON：%s', filePath);
    end
    fileCleanup = onCleanup(@() fclose(fileId)); %#ok<NASGU>
    fprintf(fileId, '%s\n', jsonencode(value, 'PrettyPrint', true));
end

function logLine(fileId, messageFormat, varargin)
    logText = sprintf(messageFormat, varargin{:});
    fprintf('%s\n', logText);
    fprintf(fileId, '%s\n', logText);
end

function timeText = utcStamp()
    timeText = char(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ss.SSS''Z'''));
end

function value = scalarOrNaN(optionalValue)
    if isempty(optionalValue)
        value = NaN;
    else
        value = optionalValue;
    end
end
