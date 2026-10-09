import { z } from 'zod'

const trigram = z.enum(['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'])
const element = z.enum(['木', '火', '土', '金', '水'])
const role = z.enum(['original_hexagram', 'moving_line', 'mutual_hexagram', 'changed_hexagram'])
const hexagram = z.object({
  id: z.number().int().min(1).max(64), name: z.string(), full_name: z.string(),
  lines: z.array(z.union([z.literal(0), z.literal(1)])).length(6), binary: z.string().regex(/^[01]{6}$/),
  upper_trigram: trigram, lower_trigram: trigram,
}).strict()
const state = z.object({ trigram, element, state: z.enum(['wang', 'shuai', 'neutral']), state_label: z.enum(['旺', '衰', '平']) }).strict()
const auxiliary = z.object({ upper: state, lower: state }).strict()
export const catalogSchema = z.object({
  api_version: z.literal('meihua_service_adapter_v1'), timezone: z.literal('Asia/Shanghai'),
  entries: z.array(hexagram.extend({ line_names: z.array(z.string()).length(6) })).length(64),
}).strict()
export const resultSchema = z.object({
  api_version: z.literal('meihua_service_adapter_v1'), input_mode: z.enum(['manual_hexagram', 'time_cast']),
  question_text: z.string(), question_applied_to_calculation: z.literal(false), cast_at: z.string(),
  timezone: z.literal('Asia/Shanghai'), line_order: z.literal('bottom_up'),
  original_hexagram: hexagram, mutual_hexagram: hexagram, changed_hexagram: hexagram,
  moving_line: z.object({ position: z.number().int().min(1).max(6), name: z.string(), polarity: z.union([z.literal(0), z.literal(1)]) }).strict(),
  body_use: z.object({ rule_version: z.literal('moving_trigram_is_yong_v1'), body_trigram: trigram, yong_trigram: trigram,
    body_element: element, yong_element: element, relation_text: z.string(),
    relation: z.enum(['body_generates_yong', 'yong_generates_body', 'body_controls_yong', 'yong_controls_body', 'same_element']),
  }).strict(),
  strength: z.object({ rule_version: z.literal('meihua_strength_v1'), timezone: z.literal('Asia/Shanghai'),
    solar_term_month_branch: z.string(), ruling_element: element, active_solar_term: z.string(), active_solar_term_time: z.string(),
    next_solar_term: z.string(), next_solar_term_time: z.string(), strength_boundary_time: z.string(), next_month_boundary_time: z.string(),
    body: state, yong: state, mutual: auxiliary, changed: auxiliary, auxiliary_weight: z.literal('auxiliary_strength'), solar_term_source: z.string(),
  }).strict(),
  time_calculation: z.object({ lunar_year: z.number().int(), lunar_month: z.number().int(), lunar_day: z.number().int(), is_leap_month: z.boolean(),
    lunar_datetime: z.string(), year_branch: z.string(), year_branch_number: z.number().int(), hour_branch: z.string(), hour_branch_number: z.number().int(),
    upper_total: z.number().int(), upper_remainder: z.number().int(), lower_total: z.number().int(), lower_remainder: z.number().int(),
    moving_total: z.number().int(), moving_remainder: z.number().int(), day_boundary_mode: z.literal('midnight'),
  }).strict().nullable(),
  versions: z.object({ production_version: z.literal('1.2.0'), casting_version: z.enum(['manual_hexagram_v1', 'traditional_meihua_datetime_v1']),
    analysis_version: z.literal('meihua_analysis_v1'), interpretation_version: z.literal('meihua_interpretation_v1'),
    body_use_version: z.literal('moving_trigram_is_yong_v1'), strength_version: z.literal('meihua_strength_v1'),
    source_corpus_version: z.literal('canonical_meihua_corpus_v1'), semantic_frame_version: z.literal('verified_semantic_frame_v1'),
  }).strict(),
  interpretation_units: z.array(z.object({ type: z.string(), statement: z.string(),
    evidence: z.array(z.object({ type: z.string(), rule_version: z.string() }).strict()).min(1),
  }).strict()),
  standard_meanings: z.array(z.object({ role, text: z.string(), status: z.enum(['SEMANTIC_APPROVED', 'structure_fallback']), source_evidence_ids: z.array(z.string()) }).strict()).length(4),
  source_references: z.array(z.object({ evidence_id: z.string(), role, section_type: z.string(), text: z.string(),
    source_title: z.string(), edition: z.string(), url: z.string().url().startsWith('https://'), volume: z.string(), location: z.string(),
    original_pages: z.null(), verification_status: z.enum(['verified', 'machine_verified']), variant_present: z.boolean(),
  }).strict()),
  ai_used: z.literal(false), history_saved: z.literal(false),
}).strict()

export type Catalog = z.infer<typeof catalogSchema>
export type MeihuaResult = z.infer<typeof resultSchema>
export const ROLE_LABELS = { original_hexagram: '本卦', moving_line: '动爻', mutual_hexagram: '互卦', changed_hexagram: '变卦' }
