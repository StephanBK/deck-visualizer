import { useRef, useState } from "react";
import { transcribeAudio } from "../api.js";

// Record the client conversation, have Gemini pull out what they said they
// want, and let the rep review/edit the notes before they influence a render.
// The parent owns notes + useNotes so the values survive screen changes.
export default function RecorderPanel({ projectId, notes, onNotes, useNotes, onUseNotes }) {
  const [state, setState] = useState("idle"); // idle | recording | processing | review | error
  const [error, setError] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [showTranscript, setShowTranscript] = useState(false);
  const recRef = useRef(null);
  const chunksRef = useRef([]);

  const supported = !!(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);

  async function start() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // iPad Safari records AAC in an MP4 container; webm covers the rest.
      const mime = ["audio/mp4", "audio/webm"].find((m) => MediaRecorder.isTypeSupported(m));
      const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      chunksRef.current = [];
      rec.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setState("processing");
        try {
          const blob = new Blob(chunksRef.current, { type: rec.mimeType || "audio/mp4" });
          const result = await transcribeAudio(blob, projectId);
          setTranscript(result.transcript);
          onNotes(result.preferences?.length ? result.preferences.join("; ") : result.summary);
          onUseNotes(true);
          setState("review");
        } catch (e) {
          setError(e.message);
          setState("error");
        }
      };
      rec.start();
      recRef.current = rec;
      setState("recording");
    } catch {
      setError("Microphone unavailable — check camera & microphone permissions.");
      setState("error");
    }
  }

  if (!supported) return null;

  return (
    <div className="recorder">
      <div className="recorder-head">
        <div className="toggle-text">
          <div className="toggle-name">🎙 Client conversation</div>
          <div className="toggle-desc">
            {state === "recording"
              ? "Recording — tap stop when you're done."
              : "Record the chat; what the client asks for can flow into the visualization."}
          </div>
        </div>
        {state === "recording" ? (
          <button className="rec-btn stop" onClick={() => recRef.current?.stop()}>
            <span className="rec-pulse" /> Stop
          </button>
        ) : (
          <button className="rec-btn" disabled={state === "processing"} onClick={start}>
            {state === "processing" ? "Listening back…" : state === "review" ? "● Re-record" : "● Record"}
          </button>
        )}
      </div>
      {state !== "review" && (
        <p className="rec-consent">Ask the client's OK before recording.</p>
      )}
      {state === "error" && <p className="rec-error">{error}</p>}

      {state === "review" && (
        <div className="rec-review">
          <label className="custom-prompt-label">
            What the client wants <span className="optional">edit freely</span>
          </label>
          <textarea
            className="custom-prompt"
            rows={3}
            maxLength={800}
            value={notes}
            onChange={(e) => onNotes(e.target.value)}
          />
          <div className="toggle-row rec-use-row">
            <div className="toggle-text">
              <div className="toggle-name">Use in visualization</div>
              <div className="toggle-desc">Feed these notes into every render</div>
            </div>
            <label className="switch">
              <input type="checkbox" checked={useNotes} onChange={(e) => onUseNotes(e.target.checked)} />
              <span className="track" />
            </label>
          </div>
          {transcript && (
            <button className="rec-transcript-toggle" onClick={() => setShowTranscript((s) => !s)}>
              {showTranscript ? "Hide transcript" : "Show transcript"}
            </button>
          )}
          {showTranscript && <p className="rec-transcript">{transcript}</p>}
        </div>
      )}
    </div>
  );
}
