import {
  BookOpen, Compass, Fingerprint, Layers3, Moon, PanelTop, PenLine, Users,
  type LucideIcon,
} from 'lucide-react'

export interface ModuleInfo {
  id: string
  name: string
  description: string
  icon: LucideIcon
}

// UI entrance registry. These previews do not activate a service or a reading.
// Liuyao is a new visual placeholder only; the backend contract is unchanged.
export const MODULES: readonly ModuleInfo[] = [
  { id: 'meihua', name: '梅花易数', description: '从一件事开始，观察卦象、变化与体用关系。', icon: BookOpen },
  { id: 'bazi', name: '八字', description: '四柱与时序的独立研习空间。', icon: Compass },
  { id: 'liuyao', name: '六爻', description: '以六爻结构展开的独立分析模块。', icon: Layers3 },
  { id: 'tarot', name: '塔罗', description: '通过牌面与牌阵，梳理问题的不同侧面。', icon: PanelTop },
  { id: 'name', name: '姓名分析', description: '了解姓名的文字、音韵与文化意涵。', icon: Fingerprint },
  { id: 'dream', name: '解梦', description: '记录梦境，整理其中的意象与感受。', icon: Moon },
  { id: 'new_name', name: '起名', description: '在文字与寓意之间，寻找合适的名字。', icon: PenLine },
  { id: 'relationship', name: '姻缘', description: '围绕关系，保留一个独立的观察入口。', icon: Users },
]
