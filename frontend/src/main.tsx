import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const metrics = [['Enterprise risk score', '72 / 100', 'High / modelled'], ['Expected annual loss', 'INR 84.6 Lakh', 'Synthetic demo estimate'], ['95% Cyber VaR', 'INR 2.18 Crore', 'One-year scenario estimate'], ['Control effectiveness', '61%', 'Evidence-weighted coverage']];
const drivers = [['Customer Payments DB', 'Critical CVE exposure', 'INR 18.4 Lakh EAL'], ['Identity Services', 'Privileged MFA gaps', 'INR 14.1 Lakh EAL'], ['Cloud Workload Group', 'Public storage configuration', 'INR 10.8 Lakh EAL']];
const API = 'http://localhost:8000';

function App() {
  const [result, setResult] = useState('');
  async function execute(path: string, body: object) {
    setResult('Calculating with verified backend inputs...');
    try { const response = await fetch(`${API}${path}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)}); const data = await response.json(); setResult(JSON.stringify(data, null, 2)); }
    catch { setResult('The API is unavailable. Start the FastAPI service before running this action.'); }
  }
  return <main><header><div><span className="eyebrow">SENTINELLEDGER / CISO WORKSPACE</span><h1>Cyber risk, expressed in business terms.</h1></div><span>Demo Financial Services Enterprise</span></header><p className="fresh">Demo data refreshed moments ago / Risk Model 1.0.0 / All values are modelled estimates</p><section className="metrics">{metrics.map(([label, value, note]) => <article key={label}><p>{label}</p><strong>{value}</strong><small>{note}</small></article>)}</section><section className="grid"><article className="panel chart"><div><h2>Financial risk trajectory</h2><p>Expected annual loss (INR)</p></div><div className="bars">{[38,52,46,64,57,73,69,84].map((height, i) => <i key={i} style={{height: `${height}%`}} />)}</div><footer>Jan <span>Mar</span><span>May</span><span>Jul</span> Sep</footer></article><article className="panel"><h2>Decision queue</h2><p>Highest modelled risk contributors</p>{drivers.map(([asset, risk, eal]) => <div className="driver" key={asset}><b>{asset}</b><span>{risk}</span><em>{eal}</em></div>)}</article></section><section className="actions"><article><span>RECOMMENDED NEXT STEP</span><h2>Roll out privileged MFA</h2><p>Run a scenario with transparent coverage assumptions.</p><button onClick={() => execute('/api/v1/scenarios/mfa', {before_eal:8460000, rollout_cost:1200000, current_privileged_coverage:.2, target_privileged_coverage:1})}>Run what-if scenario</button></article><article><span>INVESTMENT OPTIMISER</span><h2>Allocate INR 1 Crore</h2><p>Choose the highest risk-reduction portfolio within budget.</p><button onClick={() => execute('/api/v1/optimization', {budget:10000000})}>Optimise portfolio</button></article><article><span>AUDIT EVIDENCE</span><h2>Assessment integrity</h2><p>Finalise a real local hash-chain record.</p><button onClick={() => execute('/api/v1/audit', {assessment_id:'demo-september',model_version:'1.0.0',eal:8460000})}>Finalise assessment</button></article></section>{result && <pre className="result">{result}</pre>}</main>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
