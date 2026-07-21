import { API_BASE_URL } from './config'
import type { Citation } from '../types/chat'

export interface QueryResponse {
  answer: string
  citations: Citation[]
  confidence: number
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

export async function queryKnowledgeBase(question: string): Promise<QueryResponse> {
  return postJson<QueryResponse>('/query', { question })
}

// --- Thin agentic slices ---------------------------------------------------

export interface RcaHistoryItem {
  doc_id: string
  title: string
  doc_type: string
  date: string | null
}

export interface RcaResponse {
  equipment_tag: string
  root_cause_summary: string
  history: RcaHistoryItem[]
  citations: Citation[]
  confidence: number
}

export async function fetchRca(equipmentTag: string): Promise<RcaResponse> {
  return getJson<RcaResponse>(`/rca/${encodeURIComponent(equipmentTag)}`)
}

export interface ComplianceGap {
  requirement: string
  finding: string
  severity: 'high' | 'medium' | 'low'
}

export interface ComplianceResponse {
  procedure_id: string
  regulation_id: string
  gaps: ComplianceGap[]
  summary: string
  compliant: boolean | null
}

export async function checkCompliance(
  procedureId: string,
  regulationId: string,
): Promise<ComplianceResponse> {
  return postJson<ComplianceResponse>('/compliance/check', {
    procedure_id: procedureId,
    regulation_id: regulationId,
  })
}

export interface SimilarIncident {
  doc_id: string
  title: string
  similarity: number
  snippet: string
}

export interface LessonsResponse {
  source_doc_id: string
  matches: SimilarIncident[]
  error?: string
}

export async function fetchSimilarIncidents(docId: string): Promise<LessonsResponse> {
  return getJson<LessonsResponse>(`/lessons/similar/${encodeURIComponent(docId)}`)
}

export interface GraphNode {
  id: string
  name: string
  type: string
  color: string
}

export interface GraphLink {
  source: string
  target: string
  type: string
}

export interface GraphResponse {
  center: string
  nodes: GraphNode[]
  links: GraphLink[]
}

export async function fetchGraph(equipmentTag: string): Promise<GraphResponse> {
  return getJson<GraphResponse>(`/graph/${encodeURIComponent(equipmentTag)}`)
}
