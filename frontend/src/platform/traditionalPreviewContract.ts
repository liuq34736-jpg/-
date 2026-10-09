import { z } from 'zod'
import { resultSchema } from './meihuaContract'

const quote = z.object({ evidence_id: z.string(), quote: z.string() }).strict()
const condition = z.object({ id: z.string(), kind: z.string(), text: z.string(), source_evidence_ids: z.array(z.string()),
  source_quotes: z.array(quote).min(1), satisfaction: z.literal('unknown') }).strict()
const branch = condition.extend({ direction: z.enum(['favorable', 'adverse', 'undetermined']), condition_ids: z.array(z.string()) }).strict()
const factor = z.object({ id: z.string(), text: z.string(), layer: z.enum(['primary', 'qualifier', 'reviewed_line', 'auxiliary']),
  scope: z.string(), rule_ids: z.array(z.string()), condition_ids: z.array(z.string()), source_evidence_ids: z.array(z.string()) }).strict()
const notice = z.object({ type: z.string(), text: z.string(), rule_id: z.string() }).strict()
const auxiliary = z.object({ role: z.enum(['mutual_hexagram', 'changed_hexagram']), name: z.string(), note: z.string(),
  items: z.array(z.object({ side: z.enum(['lower', 'upper']), trigram: z.enum(['乾', '兑', '离', '震', '巽', '坎', '艮', '坤']),
    element: z.enum(['木', '火', '土', '金', '水']), state_label: z.enum(['旺', '衰', '平']), relation_to_original_body: z.string(),
    status: z.enum(['reference_only', 'context_only', 'auxiliary_factor']) }).strict()) }).strict()
const rule = z.object({ rule_id: z.string(), basis: z.string(), summary: z.string(), source_ids: z.array(z.string()) }).strict()
const ruleSource = z.object({ source_id: z.string(), title: z.string(), edition: z.string(), volume: z.string(), location: z.string(),
  pdf_pages: z.array(z.number().int()), printed_pages: z.array(z.string()), url: z.string().url().startsWith('https://'),
  excerpt: z.string(), limits: z.string(), review_method: z.string() }).strict()
const provenance = z.object({ rule_version: z.string(), review_scope: z.literal('offline_individual_condition_review'),
  human_verified: z.literal(false), is_production_signature: z.literal(false) }).strict()

export const judgementSchema = z.object({
  preview_version: z.literal('traditional_judgement_web_preview_v1'), policy_version: z.literal('traditional_condition_synthesis_v1'),
  registry_version: z.literal('day6ab_readonly_registry_v1'),
  review_status: z.enum(['bounded', 'branch_unresolved', 'unreviewed', 'not_eligible', 'evidence_unavailable']),
  eligible_for_condition_review: z.boolean(), finite_synthesis_available: z.boolean(),
  direction: z.enum(['favorable', 'adverse', 'mixed']).nullable(), label: z.string(), summary: z.string(),
  scope: z.enum(['bounded_reviewed_synthesis', 'conditional_branches_only', 'structure_only']),
  body_use_baseline: z.enum(['favorable', 'adverse']).nullable(), conditions: z.array(condition), branches: z.array(branch),
  branch_relationship: z.enum(['alternative_not_simultaneous', 'joint_source_constraints']).nullable(), scope_limits: z.array(condition),
  favorable_factors: z.array(factor), adverse_factors: z.array(factor), strength_modifiers: z.array(factor),
  auxiliary_analysis: z.array(auxiliary), conflicts: z.array(notice), auxiliary_divergences: z.array(notice), uncertainties: z.array(notice),
  rules: z.array(rule), rule_sources: z.array(ruleSource), classical_sources: resultSchema.shape.source_references,
  review_provenance: provenance.nullable(), real_world_conditions: z.literal('unknown'),
  question_used_to_satisfy_conditions: z.literal(false), is_final_event_outcome: z.literal(false),
  ai_used: z.literal(false), history_written: z.literal(false),
}).strict().superRefine((value, context) => {
  const reviewed = value.review_status === 'bounded' || value.review_status === 'branch_unresolved'
  const expectedScope = value.review_status === 'bounded' ? 'bounded_reviewed_synthesis' : value.review_status === 'branch_unresolved' ? 'conditional_branches_only' : 'structure_only'
  if (value.eligible_for_condition_review !== reviewed || value.finite_synthesis_available !== (value.review_status === 'bounded') ||
    (value.direction !== null) !== (value.review_status === 'bounded') || value.scope !== expectedScope ||
    reviewed !== (value.review_provenance !== null) || reviewed !== Boolean(value.conditions.length && value.branches.length)) {
    context.addIssue({ code: z.ZodIssueCode.custom, message: 'invalid preview scope' })
  }
  const ids = new Set(value.conditions.map(item => item.id))
  const refs = new Map(value.classical_sources.map(item => [item.evidence_id, item.text]))
  if (ids.size !== value.conditions.length || value.branches.some(item => !item.condition_ids.length || item.condition_ids.some(id => !ids.has(id))) ||
    [...value.conditions, ...value.branches, ...value.scope_limits].some(item => !item.source_evidence_ids.length ||
      item.source_quotes.some(q => !item.source_evidence_ids.includes(q.evidence_id) || !refs.get(q.evidence_id)?.includes(q.quote)))) {
    context.addIssue({ code: z.ZodIssueCode.custom, message: 'invalid evidence binding' })
  }
})

export const previewSchema = z.object({ preview_api_version: z.literal('traditional_preview_api_v1'),
  reading: resultSchema, judgement: judgementSchema }).strict()
export type JudgementPreview = z.infer<typeof judgementSchema>
