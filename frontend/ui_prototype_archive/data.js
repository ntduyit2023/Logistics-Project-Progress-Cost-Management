const ppcTasks = {
  "A": { "name": "Architectural decisions", "duration": 4, "predecessors": [], "resources": {"Design_Comp": 1, "Design_Mech": 1} },
  "B": { "name": "Hardware specifications", "duration": 6, "predecessors": ["A"], "resources": {"Design_Comp": 1, "Design_Mech": 1, "Dev_Mech": 1, "Assembly_Mech": 1} },
  "C": { "name": "Software specifications", "duration": 7, "predecessors": ["A"], "resources": {"Design_Comp": 1, "Dev_Comp": 1, "Assembly_Comp": 1} },
  "D": { "name": "Conveyor design", "duration": 8, "predecessors": ["B"], "resources": {"Design_Mech": 1, "Dev_Mech": 1} },
  "E": { "name": "Hardware design", "duration": 6, "predecessors": ["B"], "resources": {"Design_Comp": 1, "Design_Mech": 1, "Dev_Mech": 1} },
  "F": { "name": "Software design", "duration": 12, "predecessors": ["C"], "resources": {"Design_Comp": 1, "Dev_Comp": 1} },
  "G": { "name": "Operating system documentation", "duration": 10, "predecessors": ["C"], "resources": {"Dev_Comp": 1, "Documentation": 1} },
  "H": { "name": "Hardware detail drawings", "duration": 8, "predecessors": ["E", "F"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1, "Documentation": 1} },
  "I": { "name": "Software programming", "duration": 16, "predecessors": ["G"], "resources": {"Design_Comp": 1, "Documentation": 1} },
  "J": { "name": "Software verification/testing", "duration": 12, "predecessors": ["I"], "resources": {"Dev_Comp": 1, "Assembly_Comp": 1, "Documentation": 1} },
  "K": { "name": "Conveyor detailed drawings", "duration": 7, "predecessors": ["D"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1, "Documentation": 1} },
  "L": { "name": "Drawing verification/Minor integration", "duration": 9, "predecessors": ["H", "K"], "resources": {"Dev_Comp": 1, "Assembly_Comp": 1, "Assembly_Mech": 1} },
  "M": { "name": "Prototype development", "duration": 4, "predecessors": ["H"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1} },
  "N": { "name": "Prototype installation", "duration": 7, "predecessors": ["J", "M"], "resources": {"Assembly_Comp": 1, "Assembly_Mech": 1} },
  "O": { "name": "Hardware order/delivery", "duration": 7, "predecessors": ["L"], "resources": {"Dev_Mech": 1, "Purchase": 1} },
  "P": { "name": "System Interface", "duration": 5, "predecessors": ["L"], "resources": {"Dev_Mech": 1, "Assembly_Mech": 1} },
  "Q": { "name": "Hardware assembly", "duration": 4, "predecessors": ["O", "P"], "resources": {"Assembly_Comp": 1, "Assembly_Mech": 1} },
  "R": { "name": "Hardware/software Integration", "duration": 5, "predecessors": ["N", "Q"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1, "Assembly_Comp": 1, "Assembly_Mech": 1} },
  "S": { "name": "Hardware/software documentation", "duration": 2, "predecessors": ["R"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1, "Documentation": 1} },
  "T": { "name": "System verification", "duration": 3, "predecessors": ["R"], "resources": {"Dev_Mech": 1, "Assembly_Comp": 1, "Assembly_Mech": 1} },
  "U": { "name": "Acceptance test", "duration": 2, "predecessors": ["S", "T"], "resources": {"Assembly_Comp": 1, "Assembly_Mech": 1} }
};

// Known critical path from Case Study analysis
const criticalPathNodes = ['A', 'C', 'G', 'I', 'J', 'N', 'R', 'T', 'U'];

const graphElements = [];

// Convert JSON tasks into Cytoscape Nodes
for (const [id, task] of Object.entries(ppcTasks)) {
  graphElements.push({
    data: {
      id: id,
      label: `${id}\n(${task.duration}d)`,
      fullName: task.name,
      duration: task.duration,
      resources: task.resources,
      isCritical: criticalPathNodes.includes(id)
    },
    classes: criticalPathNodes.includes(id) ? 'critical-node' : 'normal-node'
  });
}

// Convert Predecessors into Cytoscape Edges
for (const [id, task] of Object.entries(ppcTasks)) {
  for (const pred of task.predecessors) {
    // If both source and target are critical, edge is critical
    const isCriticalEdge = criticalPathNodes.includes(id) && criticalPathNodes.includes(pred);
    
    // NOTE: Edge goes FROM pred TO id
    graphElements.push({
      data: {
        id: `edge-${pred}-${id}`,
        source: pred,
        target: id
      },
      classes: isCriticalEdge ? 'critical-edge' : 'normal-edge'
    });
  }
}
