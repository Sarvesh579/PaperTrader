import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const getStatus = () => API.get("/status");
export const getPortfolio = () => API.get("/portfolio");
export const getTrades = () => API.get("/trades");
export const getEquity = () => API.get("/equity");
export const refreshPrices = () => API.get("/refresh_prices");

export const startTrading = () => API.post("/start");
export const stopTrading = () => API.post("/stop");
export const resetAccount = () => API.post("/reset");
export const setCash = (amount) => API.post(`/set_cash/${amount}`);
export const setStrategy = (name) => API.post(`/set_strategy/${name}`);
export const setInterval = (minutes) => API.post(`/set_interval/${minutes}`);