import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useParams } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, BookOpen, History, House, Menu, Settings2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { BRAND } from '@/config/brand'
import { MODULES, type ModuleInfo } from '@/config/modules'
import './preview.css'
import MeihuaPage from './MeihuaPage'

interface PublicConfig { provider_name: string; model_name: string; mode: string; real_ai_enabled: boolean; production_connected: boolean }
interface HistoryResponse { total: number; mode: string; items: unknown[] }
interface AIStatus { provider_name: string; model_name: string; configuration_status: string; configured: boolean; reading_enabled: boolean }

function usePreviewData<T>(path: string) {
  const [data, setData] = useState<T | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    const controller = new AbortController()
    fetch(path, { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error('unavailable')
      return response.json() as Promise<T>
    }).then(setData).catch(() => { if (!controller.signal.aborted) setFailed(true) })
    return () => controller.abort()
  }, [path])
  return { data, failed }
}

function ServiceNotice({ failed }: { failed: boolean }) {
  return failed ? <p className="notice" role="alert">本地后端暂不可用，请检查后端是否已启动。</p> : null
}

function BrandLockup() {
  return <Link to="/" className="brand" aria-label={`${BRAND.name}首页`}>
    <img src={BRAND.assets.logo} width="48" height="48" alt="" />
    <span className="brand-words"><strong>{BRAND.name}</strong><span>{BRAND.englishName}</span></span>
  </Link>
}

function Home({ modules }: { modules: readonly ModuleInfo[] }) {
  return <>
    <section className="hero">
      <div className="hero-copy">
        <span className="eyebrow">{BRAND.name} · 个人研习工作台</span>
        <h1>{BRAND.tagline}</h1>
        <p>{BRAND.description}</p>
        <Button asChild className="hero-button"><Link to="/modules/meihua">开始梅花易数 <ArrowRight size={17} /></Link></Button>
        <span className="small-note">确定性起卦与基础解释已接入，个性化 AI 问事正文尚未启用。</span>
      </div>
      <div className="hero-note" aria-label="平台理念">
        <div className="note-heading"><BookOpen size={19} /><span>让每一次观察，都有来处</span></div>
        <p>从一个具体问题出发，<br />在象与理之间，留下可回看的记录。</p>
        <div className="note-rule" />
        <span>有据可循 <i /> 保留边界 <i /> 不作必然预测</span>
      </div>
    </section>
    <section className="module-section" aria-label="占筮模块">
      <div className="section-heading"><div><span className="eyebrow">探索工具</span><h2>从你关心的事情开始</h2></div><span className="section-note">独立模块 · 逐步接入</span></div>
      <div className="module-grid">{modules.map((module, index) => {
        const Icon = module.icon
        return <Link key={module.id} to={`/modules/${module.id}`} data-testid={`module-${module.id}`} className={`module-card ${index === 0 ? 'featured' : ''}`}>
          <div className="module-top"><span className="module-icon"><Icon size={23} strokeWidth={1.6} /></span><span className="tag">{module.id === 'meihua' ? '已接入' : '开发中'}</span></div>
          <h3>{module.name}</h3><p>{module.description}</p>
          <div className="module-bottom"><span>{index === 0 ? '确定性计算 · 基础解释' : '独立模块 · 入口预留'}</span><ArrowUpRight size={18} /></div>
        </Link>
      })}</div>
    </section>
    <div className="workspace-note"><span className="status-dot" /><p>网页与原系统独立运行。确定性模块只读复用冻结规则与资料，AI 问事正文和生产历史尚未接入。</p></div>
  </>
}

function ModulePage({ modules }: { modules: readonly ModuleInfo[] }) {
  const { moduleId } = useParams()
  const module = modules.find(item => item.id === moduleId)
  if (!module) return <section className="page-panel"><h1>入口不存在</h1><Link to="/">返回首页</Link></section>
  if (module.id === 'meihua') return <MeihuaPage />
  const Icon = module.icon
  return <section className="page-panel">
    <span className="eyebrow">探索工具 / 模块预览</span>
    <div className="page-heading"><Icon size={29} strokeWidth={1.6} /><h1>{module.name}</h1><span className="tag">开发中</span></div>
    <p>{module.description}</p>
    <p className="notice">该模块仅预留入口，尚未实现占筮或解释能力。</p>
    <div className="page-actions"><Button disabled>尚未接入，暂不可开始</Button><Link className="back-link" to="/">返回首页 <ArrowRight size={15} /></Link></div>
  </section>
}

function SettingsPage() {
  const { data, failed } = usePreviewData<PublicConfig>('/api/v1/config')
  const { data: ai, failed: aiFailed } = usePreviewData<AIStatus>('/api/v1/ai/status')
  return <section className="page-panel"><span className="eyebrow">工作台 / 运行设置</span><h1>设置</h1><ServiceNotice failed={failed || aiFailed} />
    <p>DeepSeek 由 Python 后端管理。确定性起卦已接入；个性化 AI 问事正文与生产历史尚未接入。</p>
    {data && <dl className="settings-list"><div><dt>运行模式</dt><dd>本地预览</dd></div><div><dt>Provider</dt><dd>{data.provider_name}</dd></div><div><dt>Model</dt><dd>{data.model_name}</dd></div>{ai && <div><dt>API 配置状态</dt><dd data-testid="api-configuration-status">{ai.configuration_status}</dd></div>}<div><dt>正式 AI 解卦</dt><dd>{data.real_ai_enabled ? '已启用' : '未启用'}</dd></div><div><dt>生产系统</dt><dd>{data.production_connected ? '已连接' : '未连接'}</dd></div></dl>}
    <p className="notice">“已配置”表示服务器发现有效格式的配置，不代表本次已调用或认证成功。刷新本页不会调用模型。密钥只保存在服务器环境中，本页不提供密钥输入或保存功能。</p>
  </section>
}

function HistoryPage() {
  const { data, failed } = usePreviewData<HistoryResponse>('/api/v1/history')
  return <section className="page-panel"><span className="eyebrow">工作台 / 留下记录，便于回看</span><h1>历史</h1><ServiceNotice failed={failed} />
    {data && <div className="empty-state"><span className="empty-icon"><History size={29} strokeWidth={1.4} /></span><h2>这里还没有网页记录</h2><p>当前为独立预览历史，共 {data.total} 条。<br />原系统历史未读取、未迁移，也未修改。</p><Link to="/">回到首页 <ArrowRight size={15} /></Link></div>}
    <p className="small-note">后续将通过现有受控历史服务接入，并保留当时的审核结果和快照。</p>
  </section>
}

export default function PlatformPreview() {
  const { failed } = usePreviewData<unknown[]>('/api/v1/modules')
  const [mobile, setMobile] = useState(() => window.matchMedia('(max-width: 900px)').matches)
  const [menuOpen, setMenuOpen] = useState(false)
  const sidebarRef = useRef<HTMLElement>(null)
  const menuRef = useRef<HTMLButtonElement>(null)
  const location = useLocation()

  useEffect(() => {
    const query = window.matchMedia('(max-width: 900px)')
    const changed = () => { setMobile(query.matches); setMenuOpen(false) }
    query.addEventListener('change', changed)
    return () => query.removeEventListener('change', changed)
  }, [])
  useEffect(() => { setMenuOpen(false) }, [location.pathname])
  useEffect(() => {
    if (!mobile || !menuOpen) return
    const menuButton = menuRef.current
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    sidebarRef.current?.querySelector<HTMLButtonElement>('button')?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false)
      if (event.key !== 'Tab') return
      const controls = sidebarRef.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])')
      if (!controls?.length) return
      const first = controls[0]
      const last = controls[controls.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKeyDown)
      menuButton?.focus()
    }
  }, [mobile, menuOpen])

  const title = location.pathname === '/history' ? '历史记录' : location.pathname === '/settings' ? '运行设置'
    : MODULES.find(module => location.pathname === `/modules/${module.id}`)?.name ?? '总览'
  return <div className="platform-shell">
    {mobile && <header className="mobile-header"><BrandLockup /><button ref={menuRef} className="menu-toggle" aria-label="打开导航" aria-expanded={menuOpen} aria-controls="platform-sidebar" onClick={() => setMenuOpen(true)}><Menu size={23} /></button></header>}
    {mobile && menuOpen && <div className="nav-backdrop" onClick={() => setMenuOpen(false)} aria-hidden="true" />}
    {(!mobile || menuOpen) && <aside id="platform-sidebar" ref={sidebarRef} className={`platform-sidebar ${mobile ? 'is-mobile' : ''}`} role={mobile ? 'dialog' : undefined} aria-modal={mobile ? true : undefined} aria-label="功能导航">
      {mobile && <button className="drawer-close" aria-label="关闭导航" onClick={() => setMenuOpen(false)}><X size={22} /></button>}
      <BrandLockup />
      <p className="sidebar-tagline">{BRAND.tagline}</p>
      <nav aria-label="主导航" onClick={() => setMenuOpen(false)}>
        <div className="nav-section"><span className="nav-label">工作台</span><NavLink to="/" end><House size={18} strokeWidth={1.6} /><span>首页</span></NavLink><NavLink to="/history"><History size={18} strokeWidth={1.6} /><span>历史</span></NavLink></div>
        <div className="nav-section module-nav"><span className="nav-label">探索工具</span>{MODULES.map(module => {
          const Icon = module.icon
          return <NavLink key={module.id} to={`/modules/${module.id}`}><Icon size={18} strokeWidth={1.6} /><span>{module.name}</span><small>{module.id === 'meihua' ? '已接入' : '开发中'}</small></NavLink>
        })}</div>
        <div className="nav-section settings-nav"><NavLink to="/settings"><Settings2 size={18} strokeWidth={1.6} /><span>设置</span></NavLink></div>
      </nav>
      <div className="sidebar-bottom"><span className="status-dot" />仅在本机运行<span>LOCAL WORKSPACE</span></div>
    </aside>}
    <div className="workspace">
      <header className="workspace-header"><div><span>工作台</span><span className="breadcrumb-divider">/</span><strong>{title}</strong></div><span className="preview-badge"><span className="status-dot" />本地预览</span></header>
      <div className="workspace-body">
        <main id="main-content"><ServiceNotice failed={failed} /><Routes>
          <Route path="/" element={<Home modules={MODULES} />} />
          <Route path="/modules/:moduleId" element={<ModulePage modules={MODULES} />} />
          <Route path="/settings" element={<SettingsPage />} /><Route path="/history" element={<HistoryPage />} />
          <Route path="*" element={<section className="page-panel"><h1>入口不存在</h1><Link to="/">返回首页</Link></section>} />
        </Routes></main>
        <footer><span>{BRAND.englishName} · 只作有依据的观察</span><span>参考项目 © 2023 dreamhunter2333 · MIT</span></footer>
      </div>
    </div>
  </div>
}
