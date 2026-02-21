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

  const activeStyle = {
    backgroundColor: "#4CAF50",
    color: "white"
  };

  const totalUnrealized = portfolio.reduce(
    (sum, p) => sum + (p.unrealized_pnl || 0),
    0
  );

  const totalRealized = trades.reduce(
    (sum, t) => sum + (t.realized_pnl || 0),
    0
  );

  return (
    <div style={{ padding: 20, fontFamily: "Arial" }}>
      <h1>PaperTrader Dashboard</h1>

      <h2>Status</h2>
      <p><b>Cash:</b> ₹{status.cash}</p>
      <p><b>Running:</b> {String(status.is_running)}</p>
      <p><b>Interval:</b> {status.interval_minutes} min</p>

      <div>
        <button
          onClick={async () => {
            await startTrading();
            await refresh();
          }}
          style={status.is_running ? activeStyle : {}}
        >
          Start
        </button>

        <button
          onClick={async () => {
            await stopTrading();
            await refresh();
          }}
          style={!status.is_running ? activeStyle : {}}
        >
          Stop
        </button>

        <button
          onClick={async () => {
            await resetAccount();
            await refresh();
          }}
        >
          Reset
        </button>
      </div>

      <hr />

      <h2>Set Cash</h2>
      <input
        type="number"
        placeholder="Enter amount"
        value={cashInput}
        onChange={(e) => setCashInput(e.target.value)}
      />
      <button
        onClick={async () => {
          if (cashInput) {
            await setCash(Number(cashInput));
            setCashInput("");
            await refresh();
          }
        }}
      >
        Update
      </button>

      <hr />

      <h2>Strategy</h2>
      <button
        onClick={async () => {
          await setStrategy("random");
          await refresh();
        }}
        style={status.current_strategy === "random" ? activeStyle : {}}
      >
        Random
      </button>

      <button
        onClick={async () => {
          await setStrategy("momentum");
          await refresh();
        }}
        style={status.current_strategy === "momentum" ? activeStyle : {}}
      >
        Momentum
      </button>

      <hr />

      <h2>Interval</h2>
      <button
        onClick={async () => {
          await setInterval(1);
          await refresh();
        }}
        style={status.interval_minutes === 1 ? activeStyle : {}}
      >
        1 Min
      </button>

      <button
        onClick={async () => {
          await setInterval(5);
          await refresh();
        }}
        style={status.interval_minutes === 5 ? activeStyle : {}}
      >
        5 Min
      </button>

      <hr />

      <h2>Equity Curve</h2>
      <LineChart width={800} height={300} data={equity}>
        <CartesianGrid stroke="#ccc" />
        <XAxis dataKey="timestamp" hide />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="total_equity" stroke="#8884d8" />
      </LineChart>

      <hr />

      <h2>
        Portfolio — 
        <span style={{ color: totalUnrealized >= 0 ? "green" : "red" }}>
          ₹{totalUnrealized.toFixed(2)}
        </span>
      </h2>
      <table border="1" cellPadding="8">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Quantity</th>
            <th>Avg Price</th>
            <th>Current Price</th>
            <th>Unrealized PnL</th>
          </tr>
        </thead>
        <tbody>
          {portfolio.map((p, index) => (
            <tr key={index}>
              <td>{p.symbol}</td>
              <td>{p.quantity}</td>
              <td>{p.avg_price?.toFixed(2)}</td>
              <td>{p.current_price?.toFixed(2)}</td>
              <td
                style={{
                  color: p.unrealized_pnl >= 0 ? "green" : "red"
                }}
              >
                {p.unrealized_pnl?.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <hr />

      <h2>
        Trades —  
        <span style={{ color: totalRealized >= 0 ? "green" : "red" }}>
          ₹{totalRealized.toFixed(2)}
        </span>
      </h2>
      <table border="1" cellPadding="8">
        <thead>
          <tr>
            <th>Time</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Qty</th>
            <th>Price</th>
            <th>Realized PnL</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, index) => (
            <tr key={index}>
              <td>{new Date(t.timestamp).toLocaleTimeString()}</td>
              <td>{t.symbol}</td>
              <td style={{ color: t.side === "BUY" ? "green" : "red" }}>
                {t.side}
              </td>
              <td>{t.quantity}</td>
              <td>{t.price?.toFixed(2)}</td>
              <td
                style={{
                  color: t.realized_pnl >= 0 ? "green" : "red"
                }}
              >
                {t.realized_pnl?.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;