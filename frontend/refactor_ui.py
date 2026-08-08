import re

with open(r'E:\University\Year 3 - 3\DA3\frontend\src\pages\Workspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = r'\{/\* Main Navigation Tabs \(Trang 1 vs Trang 2\) \*/\}'
end_marker = r'\{isTaskModalOpen && \('

match = re.search(f'({start_marker}.*?)({end_marker})', content, re.DOTALL)
if match:
    old_ui = match.group(1)
    
    new_ui = """      {/* Main Navigation Tabs (5 Tabs) */}
      <div className="flex border-b border-slate-200 bg-white rounded-xl shadow-sm mb-6 overflow-hidden">
        {[
          { id: 'overview', label: '1. Tổng quan', icon: Layers },
          { id: 'analysis', label: '2. Phân tích', icon: Activity },
          { id: 'assignment', label: '3. Phân công', icon: GitCommit },
          { id: 'selection', label: '4. Lựa chọn', icon: Sliders },
          { id: 'evaluation', label: '5. Đánh giá AI', icon: Sparkles }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setWorkspaceTab(tab.id as any)}
            className={`flex-1 py-3.5 px-2 sm:px-6 font-bold text-[10px] sm:text-sm border-b-2 transition-all flex items-center justify-center gap-1 sm:gap-2 ${
              workspaceTab === tab.id
                ? 'border-indigo-600 text-indigo-600 bg-indigo-50/50'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mb-8">
        {workspaceTab === 'overview' && (
          <OverviewTab 
            tasks={tasks}
            dependencies={dependencies}
            displayMakespan={displayMakespan}
            displayCost={displayCost}
            projectData={projectData}
          />
        )}
        {workspaceTab === 'analysis' && (
          <AnalysisTab 
            combinedData={combinedData}
            bellCurveData={bellCurveData}
            optionCost={optionCost}
          />
        )}
        {workspaceTab === 'assignment' && (
          <AssignmentTab 
            tasks={tasks}
            dependencies={dependencies}
            projectData={projectData}
            projectId={projectId}
            optionLabel={optionLabel}
            selectedOptionModes={selectedOptionModes}
            currentOption={currentOption}
            criticalityIndices={criticalityIndices}
            ganttData={ganttData}
            maxEndHour={maxEndHour}
            api={api}
            setEditingTask={setEditingTask}
            setIsTaskModalOpen={setIsTaskModalOpen}
          />
        )}
        {workspaceTab === 'selection' && (
          <SelectionTab 
            glpoTargetDate={glpoTargetDate}
            setGlpoTargetDate={setGlpoTargetDate}
            glpoTargetHour={glpoTargetHour}
            setGlpoTargetHour={setGlpoTargetHour}
            glpoPenaltyPerDay={glpoPenaltyPerDay}
            setGlpoPenaltyPerDay={setGlpoPenaltyPerDay}
            glpoBonusPerDay={glpoBonusPerDay}
            setGlpoBonusPerDay={setGlpoBonusPerDay}
            glpoMcIterations={glpoMcIterations}
            setGlpoMcIterations={setGlpoMcIterations}
            glpoParetoCount={glpoParetoCount}
            setGlpoParetoCount={setGlpoParetoCount}
            glpoParetoSort={glpoParetoSort}
            setGlpoParetoSort={setGlpoParetoSort}
            handleRunAI={handleRunAI}
            isGlpoLoading={isGlpoLoading}
            projectData={projectData}
          />
        )}
        {workspaceTab === 'evaluation' && (
          <EvaluationTab 
            allParetoOptions={allParetoOptions}
            paretoChartType={paretoChartType}
            setParetoChartType={setParetoChartType}
            paretoBarData={paretoBarData}
            selectedGlpoOptionIndex={selectedGlpoOptionIndex}
            setSelectedGlpoOptionIndex={setSelectedGlpoOptionIndex}
            isGlpoLoading={isGlpoLoading}
            isApplyingOption={isApplyingOption}
            handleRestoreBaseline={handleRestoreBaseline}
            handleApplyParetoOption={handleApplyParetoOption}
            handleRunAI={handleRunAI}
          />
        )}
      </div>

      """
    
    new_content = content.replace(old_ui, new_ui)
    with open(r'E:\University\Year 3 - 3\DA3\frontend\src\pages\Workspace.tsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Replaced UI successfully!')
else:
    print('Markers not found!')
