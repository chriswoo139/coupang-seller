import { startTransition, useDeferredValue, useEffect, useState } from "react";
import AppShell from "./components/AppShell";
import SectionCard from "./components/SectionCard";
import StatCard from "./components/StatCard";
import {
  createProfitCalculation,
  fetchCompetitorAnalysis,
  fetchListingAssets,
  fetchOpenApiStatus,
  fetchProfitHistory,
  fetchScoredCompetitors,
} from "./lib/api";

const packOptions = [1, 2, 3, 6];

function formatKrw(value) {
  return `${Number(value || 0).toLocaleString()} KRW`;
}

function recommendationTone(score) {
  if (Number(score) >= 80) return "good";
  if (Number(score) >= 68) return "warm";
  if (Number(score) >= 55) return "muted";
  return "alert";
}

function buildSummary(competitors, profitHistory) {
  const total = competitors.length;
  const highOpportunity = competitors.filter((item) => Number(item.product_opportunity_score) >= 75).length;
  const avgPrice = total ? competitors.reduce((sum, item) => sum + Number(item.price || 0), 0) / total : 0;
  const avgScore = total
    ? competitors.reduce((sum, item) => sum + Number(item.product_opportunity_score || 0), 0) / total
    : 0;
  const avgMargin =
    profitHistory.length > 0
      ? profitHistory.reduce((sum, item) => sum + Number(item.margin_rate || 0), 0) / profitHistory.length
      : 0;

  return {
    total,
    highOpportunity,
    avgPrice,
    avgScore,
    avgMargin,
    productTypes: new Set(competitors.map((item) => item.product_type)).size,
  };
}

function buildProfitPayload(formState, selectedCompetitor) {
  return {
    competitor_id: selectedCompetitor ? Number(selectedCompetitor.id) : null,
    scenario_name: formState.scenario_name,
    product_name: selectedCompetitor ? selectedCompetitor.product_name : formState.product_name,
    purchase_cost_rmb: Number(formState.purchase_cost_rmb),
    package_cost_rmb: Number(formState.package_cost_rmb),
    china_domestic_shipping_rmb: Number(formState.china_domestic_shipping_rmb),
    international_shipping_rmb: Number(formState.international_shipping_rmb),
    exchange_rate: Number(formState.exchange_rate),
    coupang_price_krw: Number(formState.coupang_price_krw),
    coupang_fee_rate: Number(formState.coupang_fee_rate),
    fulfillment_fee_krw: Number(formState.fulfillment_fee_krw),
    ad_cost_per_order_krw: Number(formState.ad_cost_per_order_krw),
    return_loss_rate: Number(formState.return_loss_rate),
    other_cost_krw: Number(formState.other_cost_krw),
    package_count: Number(formState.package_count),
  };
}

export default function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [competitors, setCompetitors] = useState([]);
  const [profitHistory, setProfitHistory] = useState([]);
  const [openApiStatus, setOpenApiStatus] = useState(null);
  const [search, setSearch] = useState("");
  const [productType, setProductType] = useState("全部");
  const [selectedCompetitorId, setSelectedCompetitorId] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [listingAssets, setListingAssets] = useState(null);
  const [profitResult, setProfitResult] = useState(null);
  const [profitSubmitting, setProfitSubmitting] = useState(false);
  const [profitForm, setProfitForm] = useState({
    scenario_name: "React 控制台测算方案",
    product_name: "",
    purchase_cost_rmb: 2.8,
    package_cost_rmb: 0.6,
    china_domestic_shipping_rmb: 0.5,
    international_shipping_rmb: 1.3,
    exchange_rate: 190,
    coupang_price_krw: 8900,
    coupang_fee_rate: 0.11,
    fulfillment_fee_krw: 1200,
    ad_cost_per_order_krw: 1000,
    return_loss_rate: 0.03,
    other_cost_krw: 500,
    package_count: 3,
  });

  const deferredSearch = useDeferredValue(search);
  const selectedCompetitor =
    competitors.find((item) => Number(item.id) === Number(selectedCompetitorId)) ?? null;

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        const [competitorData, profitData, statusData] = await Promise.all([
          fetchScoredCompetitors(),
          fetchProfitHistory(),
          fetchOpenApiStatus(),
        ]);
        if (!active) return;
        startTransition(() => {
          setCompetitors(competitorData);
          setProfitHistory(profitData);
          setOpenApiStatus(statusData);
          if (competitorData.length > 0) {
            setSelectedCompetitorId(Number(competitorData[0].id));
          }
        });
      } catch (loadError) {
        if (!active) return;
        setError(loadError.message || "数据加载失败。");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDetailPanels() {
      if (!selectedCompetitorId) {
        setAnalysis(null);
        setListingAssets(null);
        return;
      }

      try {
        const [analysisData, listingData] = await Promise.all([
          fetchCompetitorAnalysis(selectedCompetitorId),
          fetchListingAssets(selectedCompetitorId),
        ]);
        if (!active) return;
        startTransition(() => {
          setAnalysis(analysisData);
          setListingAssets(listingData);
          setProfitForm((current) => ({
            ...current,
            product_name: listingData.competitor.product_name || current.product_name,
            scenario_name: `${listingData.competitor.product_name || "竞品"} 测算方案`,
            coupang_price_krw: Number(listingData.competitor.price || current.coupang_price_krw),
            package_count: Number(listingData.competitor.package_count || current.package_count),
          }));
        });
      } catch (detailError) {
        if (!active) return;
        setError(detailError.message || "竞品详情加载失败。");
      }
    }

    loadDetailPanels();
    return () => {
      active = false;
    };
  }, [selectedCompetitorId]);

  const summary = buildSummary(competitors, profitHistory);
  const visibleCompetitors = competitors.filter((item) => {
    const matchesType = productType === "全部" || item.product_type === productType;
    const keyword = `${item.product_name} ${item.product_type} ${item.main_keyword}`.toLowerCase();
    return matchesType && keyword.includes(deferredSearch.trim().toLowerCase());
  });
  const topProducts = [...competitors]
    .sort((left, right) => Number(right.product_opportunity_score || 0) - Number(left.product_opportunity_score || 0))
    .slice(0, 5);
  const productTypes = ["全部", ...new Set(competitors.map((item) => item.product_type).filter(Boolean))];

  async function handleProfitSubmit(event) {
    event.preventDefault();
    setProfitSubmitting(true);
    setError("");
    try {
      const payload = buildProfitPayload(profitForm, selectedCompetitor);
      const response = await createProfitCalculation(payload);
      startTransition(() => {
        setProfitResult(response);
        setProfitHistory((current) => [
          {
            id: response.record_id,
            scenario_name: payload.scenario_name,
            product_name: payload.product_name,
            package_count: payload.package_count,
            coupang_price_krw: payload.coupang_price_krw,
            net_profit_krw: response.result.net_profit_krw,
            margin_rate: response.result.margin_rate,
            break_even_roas: response.result.break_even_roas,
            created_at: new Date().toLocaleString(),
          },
          ...current,
        ].slice(0, 20));
      });
    } catch (submitError) {
      setError(submitError.message || "利润测算失败。");
    } finally {
      setProfitSubmitting(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <SectionCard title="正在加载工作台" subtitle="正在连接本地 FastAPI 后端。">
          <div className="loading-panel">
            <div className="pulse" />
            <p>正在获取竞品评分、利润历史和 Open API 准备状态。</p>
          </div>
        </SectionCard>
      </AppShell>
    );
  }

  return (
    <AppShell>
      {error ? (
        <div className="error-banner">
          <strong>提示</strong>
          <span>{error}</span>
        </div>
      ) : null}

      <section className="stat-grid">
        <StatCard label="竞品数量" value={summary.total} note="通过 FastAPI 从 SQLite 读取。" />
        <StatCard label="产品类型数" value={summary.productTypes} tone="warm" note="当前数据库中的类目聚类数量。" />
        <StatCard label="高机会产品" value={summary.highOpportunity} tone="good" note="机会分 75 分以上的产品数。" />
        <StatCard label="平均售价" value={formatKrw(summary.avgPrice.toFixed(0))} note="当前竞品的平均销售价格。" />
        <StatCard label="平均机会分" value={summary.avgScore.toFixed(1)} tone="good" note="综合选品机会评分。" />
        <StatCard label="平均已保存利润率" value={`${(summary.avgMargin * 100).toFixed(1)}%`} tone="warm" note="来自最近保存的利润测算记录。" />
      </section>

      <SectionCard title="机会看板" subtitle="按当前机会分排序的优先候选产品。">
        <div className="top-product-list">
          {topProducts.map((item) => (
            <button
              key={item.id}
              className={`top-product ${Number(selectedCompetitorId) === Number(item.id) ? "is-active" : ""}`}
              onClick={() => setSelectedCompetitorId(Number(item.id))}
              type="button"
            >
              <div>
                <strong>{item.product_name}</strong>
                <span>{item.product_type}</span>
              </div>
              <div className="top-product-side">
                <span className={`pill pill--${recommendationTone(item.product_opportunity_score)}`}>
                  {item.recommendation}
                </span>
                <strong>{Number(item.product_opportunity_score).toFixed(1)}</strong>
              </div>
            </button>
          ))}
        </div>
      </SectionCard>

      <div className="two-column">
        <SectionCard
          title="竞品浏览器"
          subtitle="筛选研究数据并查看单品评分。"
          actions={
            <>
              <input
                className="control"
                placeholder="搜索产品名或关键词"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <select className="control" value={productType} onChange={(event) => setProductType(event.target.value)}>
                {productTypes.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </>
          }
        >
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>产品</th>
                  <th>类型</th>
                  <th>售价</th>
                  <th>需求分</th>
                  <th>竞争分</th>
                  <th>机会分</th>
                </tr>
              </thead>
              <tbody>
                {visibleCompetitors.map((item) => (
                  <tr
                    key={item.id}
                    className={Number(selectedCompetitorId) === Number(item.id) ? "row-active" : ""}
                    onClick={() => setSelectedCompetitorId(Number(item.id))}
                  >
                    <td>
                      <strong>{item.product_name}</strong>
                      <span>{item.main_keyword}</span>
                    </td>
                    <td>{item.product_type}</td>
                    <td>{formatKrw(item.price)}</td>
                    <td>{Number(item.demand_score).toFixed(1)}</td>
                    <td>{Number(item.competition_score).toFixed(1)}</td>
                    <td>{Number(item.product_opportunity_score).toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard title="当前产品洞察" subtitle="快速查看竞品分析与差异化机会。">
          {analysis ? (
            <div className="analysis-stack">
              <div className="mini-metric-grid">
                <div>
                  <span>同类竞品数</span>
                  <strong>{analysis.peer_count}</strong>
                </div>
                <div>
                  <span>建议售价区间</span>
                  <strong>{analysis.price_analysis.recommended_price_range}</strong>
                </div>
                <div>
                  <span>价格战风险</span>
                  <strong>{analysis.price_analysis.price_war_risk}</strong>
                </div>
              </div>

              <div className="detail-panel">
                <h3>{analysis.competitor.product_name}</h3>
                <p>
                  {analysis.competitor.product_type} · {analysis.competitor.main_keyword}
                </p>
                <div className="score-line">
                  <span>机会分 {Number(analysis.competitor.product_opportunity_score).toFixed(1)}</span>
                  <span>需求分 {Number(analysis.competitor.demand_score).toFixed(1)}</span>
                  <span>竞争分 {Number(analysis.competitor.competition_score).toFixed(1)}</span>
                </div>
              </div>

              <div className="opportunity-list">
                {analysis.top_5_opportunities.map((item) => (
                  <div key={item} className="opportunity-item">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="placeholder">请选择一个竞品以加载分析结果。</p>
          )}
        </SectionCard>
      </div>

      <div className="two-column">
        <SectionCard title="利润测算工作台" subtitle="将测算方案绑定到竞品，并保存到 SQLite 历史记录。">
          <form className="profit-form" onSubmit={handleProfitSubmit}>
            <div className="control-grid">
              <label>
                <span>方案名称</span>
                <input
                  className="control"
                  value={profitForm.scenario_name}
                  onChange={(event) =>
                    setProfitForm((current) => ({ ...current, scenario_name: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>采购成本 RMB</span>
                <input
                  className="control"
                  type="number"
                  step="0.1"
                  value={profitForm.purchase_cost_rmb}
                  onChange={(event) =>
                    setProfitForm((current) => ({ ...current, purchase_cost_rmb: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>包装成本 RMB</span>
                <input
                  className="control"
                  type="number"
                  step="0.1"
                  value={profitForm.package_cost_rmb}
                  onChange={(event) =>
                    setProfitForm((current) => ({ ...current, package_cost_rmb: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>国内运费 RMB</span>
                <input
                  className="control"
                  type="number"
                  step="0.1"
                  value={profitForm.china_domestic_shipping_rmb}
                  onChange={(event) =>
                    setProfitForm((current) => ({
                      ...current,
                      china_domestic_shipping_rmb: event.target.value,
                    }))
                  }
                />
              </label>
              <label>
                <span>国际物流 RMB</span>
                <input
                  className="control"
                  type="number"
                  step="0.1"
                  value={profitForm.international_shipping_rmb}
                  onChange={(event) =>
                    setProfitForm((current) => ({
                      ...current,
                      international_shipping_rmb: event.target.value,
                    }))
                  }
                />
              </label>
              <label>
                <span>Coupang 售价 KRW</span>
                <input
                  className="control"
                  type="number"
                  step="100"
                  value={profitForm.coupang_price_krw}
                  onChange={(event) =>
                    setProfitForm((current) => ({ ...current, coupang_price_krw: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>履约费用 KRW</span>
                <input
                  className="control"
                  type="number"
                  step="50"
                  value={profitForm.fulfillment_fee_krw}
                  onChange={(event) =>
                    setProfitForm((current) => ({ ...current, fulfillment_fee_krw: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>广告成本 KRW</span>
                <input
                  className="control"
                  type="number"
                  step="100"
                  value={profitForm.ad_cost_per_order_krw}
                  onChange={(event) =>
                    setProfitForm((current) => ({ ...current, ad_cost_per_order_krw: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>件数</span>
                <select
                  className="control"
                  value={profitForm.package_count}
                  onChange={(event) =>
                    setProfitForm((current) => ({ ...current, package_count: event.target.value }))
                  }
                >
                  {packOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button className="primary-button" disabled={profitSubmitting} type="submit">
              {profitSubmitting ? "计算中..." : "计算并保存"}
            </button>
          </form>

          {profitResult ? (
            <div className="profit-result">
              <div className="mini-metric-grid">
                <div>
                  <span>总成本</span>
                  <strong>{formatKrw(profitResult.result.total_cost_krw)}</strong>
                </div>
                <div>
                  <span>净利润</span>
                  <strong>{formatKrw(profitResult.result.net_profit_krw)}</strong>
                </div>
                <div>
                  <span>利润率</span>
                  <strong>{(Number(profitResult.result.margin_rate) * 100).toFixed(1)}%</strong>
                </div>
                <div>
                  <span>盈亏平衡 ROAS</span>
                  <strong>{profitResult.result.break_even_roas}</strong>
                </div>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>件数</th>
                      <th>总成本</th>
                      <th>净利润</th>
                      <th>利润率</th>
                      <th>广告上限</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profitResult.scenarios.map((scenario) => (
                      <tr key={scenario.package_count}>
                        <td>{scenario.package_count}</td>
                        <td>{formatKrw(scenario.total_cost_krw)}</td>
                        <td>{formatKrw(scenario.net_profit_krw)}</td>
                        <td>{(Number(scenario.margin_rate) * 100).toFixed(1)}%</td>
                        <td>{formatKrw(scenario.max_allowed_ad_cost)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </SectionCard>

        <SectionCard title="上架资料工作台" subtitle="根据所选竞品生成标题方向、关键词建议与详情页结构。">
          {listingAssets ? (
            <div className="listing-grid">
              <div className="listing-block">
                <h3>标题方向</h3>
                <ul>
                  {listingAssets.titles.map((title) => (
                    <li key={title}>{title}</li>
                  ))}
                </ul>
              </div>
              <div className="listing-block">
                <h3>手动广告关键词</h3>
                <p>{listingAssets.keywords.manual_ad_keywords.join(", ")}</p>
                <h3>否定关键词</h3>
                <p>{listingAssets.keywords.negative_keywords.join(", ")}</p>
              </div>
              <div className="listing-block listing-block--full">
                <h3>详情页结构建议</h3>
                <div className="detail-grid">
                  <div>
                    <strong>主图</strong>
                    <p>{listingAssets.detail_structure.main_image}</p>
                  </div>
                  <div>
                    <strong>第 2 张图</strong>
                    <p>{listingAssets.detail_structure.image_2}</p>
                  </div>
                  <div>
                    <strong>第 3 张图</strong>
                    <p>{listingAssets.detail_structure.image_3}</p>
                  </div>
                  <div>
                    <strong>第 4 张图</strong>
                    <p>{listingAssets.detail_structure.image_4}</p>
                  </div>
                  <div>
                    <strong>第 5 张图</strong>
                    <p>{listingAssets.detail_structure.image_5}</p>
                  </div>
                  <div>
                    <strong>洗护说明</strong>
                    <p>{listingAssets.detail_structure.wash_care_note}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="placeholder">请选择一个竞品以生成上架资料。</p>
          )}
        </SectionCard>
      </div>

      <div className="two-column">
        <SectionCard title="利润历史记录" subtitle="显示最近由 Streamlit 与 React 客户端保存的测算记录。">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>方案</th>
                  <th>产品</th>
                  <th>件数</th>
                  <th>净利润</th>
                  <th>利润率</th>
                </tr>
              </thead>
              <tbody>
                {profitHistory.map((item) => (
                  <tr key={`${item.id}-${item.created_at}`}>
                    <td>{item.scenario_name}</td>
                    <td>{item.product_name || "-"}</td>
                    <td>{item.package_count}</td>
                    <td>{formatKrw(item.net_profit_krw)}</td>
                    <td>{(Number(item.margin_rate) * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard title="Open API 准备状态" subtitle="查看官方 Coupang Open API 的自有店铺接入状态。">
          {openApiStatus ? (
            <div className="api-status-card">
              <div className="mini-metric-grid">
                <div>
                  <span>市场</span>
                  <strong>{openApiStatus.market}</strong>
                </div>
                <div>
                  <span>Access Key</span>
                  <strong>{openApiStatus.access_key_configured ? "已就绪" : "未配置"}</strong>
                </div>
                <div>
                  <span>Secret Key</span>
                  <strong>{openApiStatus.secret_key_configured ? "已就绪" : "未配置"}</strong>
                </div>
                <div>
                  <span>Vendor ID</span>
                  <strong>{openApiStatus.vendor_id_configured ? "已就绪" : "未配置"}</strong>
                </div>
              </div>
              <p>{openApiStatus.usage_boundary}</p>
            </div>
          ) : (
            <p className="placeholder">当前无法获取 Open API 状态。</p>
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}
