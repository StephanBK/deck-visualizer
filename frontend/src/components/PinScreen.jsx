import { useState } from "react";
import { verifyPin } from "../api.js";

export default function PinScreen({ onSuccess }) {
  const [pin, setPin] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!pin.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      if (await verifyPin(pin.trim())) {
        localStorage.setItem("appPin", pin.trim());
        onSuccess();
      } else {
        setError("Wrong PIN — try again.");
        setPin("");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="pin-screen">
      <div className="pin-card">
        <h1>
          Home <em>Visualizer</em>
        </h1>
        <p>Enter the team PIN to continue.</p>
        <form onSubmit={submit}>
          <input
            type="password"
            inputMode="numeric"
            autoComplete="off"
            autoFocus
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="••••"
          />
          <button className="generate-btn" type="submit" disabled={!pin.trim() || busy}>
            {busy ? "Checking…" : "Unlock"}
          </button>
        </form>
        {error && <div className="error-banner">{error}</div>}
      </div>
    </div>
  );
}
