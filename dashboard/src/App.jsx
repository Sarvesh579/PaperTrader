import { useEffect, useState } from "react";
import {
  getStatus,
  getPortfolio,
  getTrades,
  getEquity,
  refreshPrices,
  startTrading,
  stopTrading,
  resetAccount,
  setCash,
  setStrategy,
  setInterval
} from "./api";
import "./App.css";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

function App() {
  const [status, setStatusData] = useState({});
  const [portfolio, setPortfolioData] = useState([]);
  const [trades, setTradesData] = useState([]);
  const [equity, setEquityData] = useState([]);
  const [cashInput, setCashInput] = useState("");

  const refresh = async () => {
    await refreshPrices();
    const s = await getStatus();
    const p = await getPortfolio();
    const t = await getTrades();
    const e = await getEquity();

    setStatusData(s.data);
    setPortfolioData(p.data);
    setTradesData(t.data);
    setEquityData(e.data);
  };

  useEffect(() => {
    let isMounted = true;
    const poll = async () => {
      if (!isMounted) return;
      await refresh();
      setTimeout(poll, 3000); // refresh every 3 seconds
    };
    poll();
    return () => {
      isMounted = false;
    };
  }, []);

  const totalUnrealized = portfolio.reduce(
    (sum, p) => sum + (p.unrealized_pnl || 0),
    0
  );

  const totalRealized = trades.reduce(
    (sum, t) => sum + (t.realized_pnl || 0),
    0
  );

  const pnlPercent =
    status.cash
      ? ((totalUnrealized + totalRealized) / status.cash) * 100
      : 0;

  return (
    <div className="app-container">
      {/* LEFT COLUMN */}
      <div className="left-column">
        <h1>PaperTrader</h1>
        
        <div className="section">
          <h2>
            Portfolio — 
            <span className={totalUnrealized >= 0 ? "pnl-positive" : "pnl-negative"}>
              ₹{totalUnrealized.toFixed(2)}
            </span>
          </h2>

          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Qty</th>
                <th>Avg</th>
                <th>Current</th>
                <th>PnL</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((p, i) => (
                <tr key={i}>
                  <td>{p.symbol}</td>
                  <td>{p.quantity}</td>
                  <td>{p.avg_price?.toFixed(2)}</td>
                  <td>{p.current_price?.toFixed(2)}</td>
                  <td className={ p.unrealized_pnl >= 0 ? "pnl-positive" : "pnl-negative"}>
                    {p.unrealized_pnl?.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="section">
          <h2 style={{ marginTop: 30 }}>
            Trades — 
            <span className={totalRealized >= 0 ? "pnl-positive" : "pnl-negative"}>
              ₹{totalRealized.toFixed(2)}
            </span>
          </h2>

        {/* Scrollable older trades */}
        <div className="trade-scroll">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Side</th>
                <th>Qty</th>
                <th>Price</th>
                <th>PnL</th>
              </tr>
            </thead>
            <tbody>
              { trades.map((t, i) => (
                <tr key={i}>
                  <td>{new Date(t.timestamp).toLocaleTimeString()}</td>
                  <td>{t.side}</td>
                  <td>{t.quantity}</td>
                  <td>{t.price?.toFixed(2)}</td>
                  <td className={t.realized_pnl >= 0  ? "pnl-positive" : "pnl-negative"}>
                    {t.realized_pnl?.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      </div>

      {/* RIGHT COLUMN */}
      <div className="right-column">
        <h2>Controls</h2>

        <p><b>Cash:</b> ₹{status.cash}</p>
        <p>
          <b>PnL %:</b>{" "}
          <span className={ pnlPercent >= 0 ? "pnl-positive" : "pnl-negative"}>
            {pnlPercent.toFixed(2)}%
          </span>
        </p>

        <button
          onClick={async () => { await startTrading(); refresh(); }}
          className={status.is_running ? "active" : ""}
        >
          Start
        </button>

        <button
          onClick={async () => { await stopTrading(); refresh(); }}
          className={!status.is_running ? "active" : ""}
        >
          Stop
        </button>

        <button onClick={async () => { await resetAccount(); refresh(); }}>
          Reset
        </button>

        <hr />

        <input
          type="number"
          placeholder="Set Cash"
          value={cashInput}
          onChange={(e) => setCashInput(e.target.value)}
        />
        <button
          onClick={async () => {
            await setCash(Number(cashInput));
            setCashInput("");
            refresh();
          }}
        >
          Update
        </button>

        <hr />

        <button
          onClick={async () => { await setStrategy("random"); refresh(); }}
          className={status.current_strategy === "random" ? "active" : ""}
        >
          Random
        </button>

        <button
          onClick={async () => { await setStrategy("momentum"); refresh(); }}
          className={status.current_strategy === "momentum" ? "active" : ""}
        >
          Momentum
        </button>

        <hr />

        <button
          onClick={async () => { await setInterval(1); refresh(); }}
          className={status.interval_minutes === 1 ? "active" : ""}
        >
          1 Min
        </button>

        <button
          onClick={async () => { await setInterval(5); refresh(); }}
          className={status.interval_minutes === 5 ? "active" : ""}
        >
          5 Min
        </button>

        <hr />

        <h3>Equity Curve</h3>
        <LineChart width={400} height={200} data={equity}>
          <CartesianGrid stroke="#666" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(t) =>
              new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            }
          />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="total_equity" stroke="#8884d8" />
        </LineChart>
      </div>
    </div>
  );
}

export default App;