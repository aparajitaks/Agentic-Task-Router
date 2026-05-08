/**
 * frontend/src/app/(dashboard)/workflows/components/workflow-graph.tsx
 *
 * WHY IT EXISTS:
 * LangGraph workflows are fundamentally Directed Acyclic Graphs (DAGs) with cycles
 * (ReAct loop). A visual representation helps engineers and recruiters instantly
 * grasp the complexity and status of the autonomous execution.
 *
 * WHAT IT DOES:
 * Uses React Flow to render nodes (agents/tools) and edges (transitions).
 * Supports panning, zooming, and interactive node selection.
 *
 * HOW IT CONNECTS TO BACKEND:
 * In production, it would parse the `intermediate_steps` from the `WorkflowState`
 * API to color nodes dynamically (Green for Success, Red for Error, Blue for Active).
 */

"use client";

import { useCallback } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Bot, Mail, Settings, Wrench } from "lucide-react";

// Initial Node Setup to represent our LangGraph Architecture
const initialNodes = [
  {
    id: "1",
    position: { x: 250, y: 0 },
    data: { 
      label: (
        <div className="flex flex-col items-center p-2">
          <Mail className="h-5 w-5 mb-1 text-blue-500" />
          <span className="font-semibold text-sm">Gmail Ingestion</span>
          <span className="text-xs text-muted-foreground">START</span>
        </div>
      ) 
    },
    className: "border-2 border-blue-500/50 bg-background rounded-lg shadow-md",
  },
  {
    id: "2",
    position: { x: 250, y: 150 },
    data: { 
      label: (
        <div className="flex flex-col items-center p-2">
          <Settings className="h-5 w-5 mb-1 text-purple-500" />
          <span className="font-semibold text-sm">Router Agent</span>
          <span className="text-xs text-muted-foreground">Decision Node</span>
        </div>
      ) 
    },
    className: "border-2 border-purple-500/50 bg-background rounded-lg shadow-md",
  },
  {
    id: "3",
    position: { x: 100, y: 300 },
    data: { 
      label: (
        <div className="flex flex-col items-center p-2">
          <Bot className="h-5 w-5 mb-1 text-emerald-500" />
          <span className="font-semibold text-sm">Summarizer Agent</span>
          <span className="text-xs text-emerald-500">Completed (120ms)</span>
        </div>
      ) 
    },
    className: "border-2 border-emerald-500 bg-emerald-500/10 rounded-lg shadow-md",
  },
  {
    id: "4",
    position: { x: 400, y: 300 },
    data: { 
      label: (
        <div className="flex flex-col items-center p-2">
          <Bot className="h-5 w-5 mb-1 text-amber-500" />
          <span className="font-semibold text-sm">Reply Generator</span>
          <span className="text-xs text-amber-500">Executing...</span>
        </div>
      ) 
    },
    className: "border-2 border-amber-500 bg-amber-500/10 rounded-lg shadow-md animate-pulse",
  },
  {
    id: "5",
    position: { x: 250, y: 450 },
    data: { 
      label: (
        <div className="flex flex-col items-center p-2">
          <Wrench className="h-5 w-5 mb-1 text-indigo-500" />
          <span className="font-semibold text-sm">Tool Node</span>
          <span className="text-xs text-indigo-500">calculator_tool</span>
        </div>
      ) 
    },
    className: "border-2 border-indigo-500 bg-indigo-500/10 rounded-lg shadow-md",
  },
];

const initialEdges = [
  { id: "e1-2", source: "1", target: "2", animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: "e2-3", source: "2", target: "3", label: "Route: summarize", markerEnd: { type: MarkerType.ArrowClosed } },
  { id: "e2-4", source: "2", target: "4", label: "Route: reply", animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: "e4-5", source: "4", target: "5", label: "Call Tool", animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: "e5-4", source: "5", target: "4", label: "Tool Result", animated: true, markerEnd: { type: MarkerType.ArrowClosed }, type: 'step' },
];

export function WorkflowGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="h-[600px] w-full border rounded-xl overflow-hidden bg-dot-pattern">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        className="bg-muted/20"
        colorMode="dark"
      >
        <Controls />
        <MiniMap nodeStrokeColor="#555" nodeColor="#222" maskColor="rgba(0,0,0,0.7)" />
        <Background gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
