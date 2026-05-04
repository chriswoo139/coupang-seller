export default function AppShell({ children }) {
  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyeline">Coupang 选品研究控制台</p>
          <h1>在一个本地工作台里完成竞品分析、利润测算与上架策略。</h1>
          <p className="hero-text">面向韩国 Coupang 女性内衣、洗护配件、文胸配件等类目的本地研究工具。</p>
        </div>
        <div className="hero-panel">
          <div className="hero-chip">第三阶段</div>
          <div className="hero-metric-grid">
            <div>
              <span>后端</span>
              <strong>FastAPI</strong>
            </div>
            <div>
              <span>前端</span>
              <strong>React + Vite</strong>
            </div>
            <div>
              <span>数据库</span>
              <strong>SQLite</strong>
            </div>
            <div>
              <span>模式</span>
              <strong>本地优先</strong>
            </div>
          </div>
        </div>
      </header>
      <main className="content-grid">{children}</main>
    </div>
  );
}
