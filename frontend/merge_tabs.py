import re

with open(r'E:\University\Year 3 - 3\DA3\frontend\src\pages\Workspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Tab 4 and Tab 5 with a single Tab in the navigation
nav_old = """{ id: 'selection', label: '4. Lựa chọn', icon: Sliders },
          { id: 'evaluation', label: '5. Đánh giá AI', icon: Sparkles }"""
nav_new = """{ id: 'ai_pipeline', label: '4. Lựa chọn & Đánh giá AI', icon: Sparkles }"""
content = content.replace(nav_old, nav_new)

# Replace the render blocks
render_old = """        {workspaceTab === 'selection' && (
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
        )}"""
        
render_new = """        {workspaceTab === 'ai_pipeline' && (
          <div className="space-y-12">
            {/* Phân vùng 1: Cấu hình AI */}
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-indigo-50/30 border border-indigo-100/50 -z-10"></div>
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
            </div>
            
            {/* Đường phân cách */}
            <div className="flex items-center justify-center relative mt-8 mb-4">
              <div className="w-full h-px bg-gradient-to-r from-transparent via-indigo-200 to-transparent"></div>
              <div className="absolute bg-slate-50 px-4 text-indigo-400 text-xs font-black uppercase tracking-widest flex items-center gap-2">
                <Sparkles size={14} /> KẾT QUẢ MÔ PHỎNG AI
              </div>
            </div>

            {/* Phân vùng 2: Đánh giá AI */}
            <div className="relative pt-4">
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
            </div>
          </div>
        )}"""

content = content.replace(render_old, render_new)

# Update the state logic where setWorkspaceTab('evaluation') was used
content = content.replace("setWorkspaceTab('evaluation')", "setWorkspaceTab('ai_pipeline')")

with open(r'E:\University\Year 3 - 3\DA3\frontend\src\pages\Workspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Merged tabs successfully!')
