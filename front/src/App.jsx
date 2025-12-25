import { useMemo, useState } from "react";
import Snowfall from "react-snowfall";
import "./App.css";
import { useCallback } from "react";

const API_BASE =
  import.meta.env.VITE_BACKEND_URL ||
  import.meta.env.VITE_API_BASE ||
  "";

const initialStationTypes = [
  { id: 1, coverageArea: "10.0", handoverMin: "12", handoverMax: "18" },
  { id: 2, coverageArea: "15.0", handoverMin: "10", handoverMax: "16" },
  { id: 3, coverageArea: "20.0", handoverMin: "11", handoverMax: "17" },
];

const initialHandovers = [
  { stationTypeId: 1, value: "14" },
  { stationTypeId: 2, value: "12" },
  { stationTypeId: 3, value: "15" },
];

const initialDistricts = [
  { id: "admir", area: "50.0", k: "1.21", stations: "1,2,2,3" },
];

const sampleJson = JSON.stringify(
  {
    pi: 3.141592653589793,
    stationTypes: [
      { id: 1, coverageArea: 10.0, handoverMin: 12, handoverMax: 18 },
      { id: 2, coverageArea: 15.0, handoverMin: 10, handoverMax: 16 },
      { id: 3, coverageArea: 20.0, handoverMin: 11, handoverMax: 17 },
    ],
    handovers: [
      { stationTypeId: 1, value: 14 },
      { stationTypeId: 2, value: 12 },
      { stationTypeId: 3, value: 15 },
    ],
    districts: [{ id: "admir", area: 50.0, k: 1.21, stations: [1, 2, 2, 3] }],
  },
  null,
  2
);

function toNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function parseStations(value) {
  return value
    .split(",")
    .map((part) => Number(part.trim()))
    .filter((n) => Number.isFinite(n));
}

function App() {
  const [pi, setPi] = useState("3.141592653589793");
  const [stationTypes, setStationTypes] = useState(initialStationTypes);
  const [handovers, setHandovers] = useState(initialHandovers);
  const [districts, setDistricts] = useState(initialDistricts);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [theme, setTheme] = useState("theme-guideline");
  const [inputMode, setInputMode] = useState("form");
  const [jsonInput, setJsonInput] = useState(sampleJson);
  const [dragOverJson, setDragOverJson] = useState(false);

  const handleJsonFile = useCallback(
    async (file) => {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith(".json")) {
        setError("Поддерживаются только .json файлы");
        return;
      }
      try {
        const text = await file.text();
        setJsonInput(text);
        setError("");
      } catch (err) {
        setError("Не удалось прочитать файл, ошибка");
      }
    },
    [setJsonInput]
  );

  const totalStations = useMemo(
    () =>
      districts.reduce(
        (acc, d) => acc + parseStations(d.stations).length,
        0
      ),
    [districts]
  );

  const handleStationTypeChange = (index, field, value) => {
    setStationTypes((prev) =>
      prev.map((item, idx) =>
        idx === index ? { ...item, [field]: value } : item
      )
    );
  };

  const handleHandoverChange = (index, field, value) => {
    setHandovers((prev) =>
      prev.map((item, idx) =>
        idx === index ? { ...item, [field]: value } : item
      )
    );
  };

  const handleDistrictChange = (index, field, value) => {
    setDistricts((prev) =>
      prev.map((item, idx) =>
        idx === index ? { ...item, [field]: value } : item
      )
    );
  };

  const addStationType = () => {
    setStationTypes((prev) => [
      ...prev,
      { id: prev.length + 1, coverageArea: "10", handoverMin: "10", handoverMax: "18" },
    ]);
  };

  const addHandover = () => {
    setHandovers((prev) => [
      ...prev,
      { stationTypeId: prev.length + 1, value: "12" },
    ]);
  };

  const addDistrict = () => {
    setDistricts((prev) => [
      ...prev,
      { id: `d${prev.length + 1}`, area: "40.0", k: "1.0", stations: "1,1,1" },
    ]);
  };

  const buildPayloadFromForm = () => ({
    pi: toNumber(pi, Math.PI),
    stationTypes: stationTypes.map((st) => ({
      id: toNumber(st.id),
      coverageArea: toNumber(st.coverageArea),
      handoverMin: toNumber(st.handoverMin),
      handoverMax: toNumber(st.handoverMax),
    })),
    handovers: handovers.map((h) => ({
      stationTypeId: toNumber(h.stationTypeId),
      value: toNumber(h.value),
    })),
    districts: districts.map((d) => ({
      id: d.id,
      area: toNumber(d.area),
      k: toNumber(d.k),
      stations: parseStations(d.stations),
    })),
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    let payload;
    try {
      if (inputMode === "json") {
        payload = JSON.parse(jsonInput);
      } else {
        payload = buildPayloadFromForm();
      }

      const response = await fetch(`${API_BASE}/api/v1/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail)
        );
      }
      setResult(data);
    } catch (err) {
      setError(err.message || "Ошибка запроса");
    } finally {
      setLoading(false);
    }
  };
  const toggleTheme = () => {
    setTheme((prev) => (prev === "theme-modern" ? "theme-guideline" : "theme-modern"));
  };

  return (
    <div className={`page ${theme}`}>
      {theme === "theme-modern" && (
        <Snowfall
          snowflakeCount={80}
          style={{
            position: "fixed",
            width: "100vw",
            height: "100vh",
            pointerEvents: "none",
            zIndex: 0,
          }}
        />
      )}
      <div className="backdrop" />
      <header className="hero">
        <div className="logo-block">
          <img src="/hat-xmas-svgrepo-com.svg" alt="Логотип" className="logo" />
          <div>
            <p className="eyebrow">FastAPI · Handover · L/C/N</p>
            <h1>Расчет базовых станций</h1>
            <p className="lede">
              Введите параметры типов станций, handover и районов, чтобы получить
              расчет количества базовых станций через API `/api/v1/calculate`.
            </p>
            <div className="meta">
              <span>Станций в запросе: {totalStations}</span>
              <span>API base: {API_BASE || "текущий хост"}</span>
            </div>
          </div>
        </div>
        <div className="cta">
          <button className="ghost" type="button" onClick={() => addDistrict()}>
            Добавить район
          </button>
          <button className="ghost" type="button" onClick={() => addStationType()}>
            Добавить тип станции
          </button>
        </div>
        <div className="mode-switch">
          <button
            type="button"
            className={`chip ${inputMode === "form" ? "active" : ""}`}
            onClick={() => setInputMode("form")}
          >
            Формы
          </button>
          <button
            type="button"
            className={`chip ${inputMode === "json" ? "active" : ""}`}
            onClick={() => setInputMode("json")}
          >
            JSON
          </button>
        </div>
        <div className="theme-switch">
          <button
            type="button"
            className="toggle"
            onClick={toggleTheme}
            aria-label="Переключить тему"
          >
            <span className="toggle-track">
              <span className={`toggle-thumb ${theme === "theme-guideline" ? "on" : ""}`} />
            </span>
            <span className="toggle-label">Тема</span>
          </button>
        </div>
      </header>

      <form className="panel" onSubmit={handleSubmit}>
        {inputMode === "json" ? (
          <section
            className="card span2"
            onDragOver={(e) => {
              e.preventDefault();
              setDragOverJson(true);
            }}
            onDragLeave={() => setDragOverJson(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOverJson(false);
              const file = e.dataTransfer.files?.[0];
              handleJsonFile(file);
            }}
            onDragEnter={() => setDragOverJson(true)}
          >
            <div className="card-header">
              <h2>JSON запрос</h2>
            </div>
            {dragOverJson && <div className="drop-overlay">+</div>}
            <textarea
              className="json-area"
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              spellCheck={false}
            />
            <div className="json-actions">
              <label className="ghost file-btn">
                Загрузить .json
                <input
                  type="file"
                  accept=".json,application/json"
                  onChange={(e) => handleJsonFile(e.target.files?.[0])}
                  hidden
                />
              </label>
            </div>
            <p className="muted">Формат как в README (POST /api/v1/calculate). Можно перетащить .json файл.</p>
          </section>
        ) : (
          <div className="grid">
            <section className="card">
              <div className="card-header">
                <h2>Константы</h2>
              </div>
              <label className="field">
                <span>π</span>
                <input
                  type="number"
                  step="any"
                  value={pi}
                  onChange={(e) => setPi(e.target.value)}
                />
              </label>
            </section>

            <section className="card">
              <div className="card-header">
                <h2>Типы станций</h2>
                <button type="button" onClick={addStationType}>
                  +
                </button>
              </div>
              {stationTypes.map((st, idx) => (
                <div className="card-row" key={`st-${idx}`}>
                  <label className="field">
                    <span>ID</span>
                    <input
                      type="number"
                      value={st.id}
                      onChange={(e) =>
                        handleStationTypeChange(idx, "id", e.target.value)
                      }
                    />
                  </label>
                  <label className="field">
                    <span>Площадь покрытия (S)</span>
                    <input
                      type="number"
                      step="any"
                      value={st.coverageArea}
                      onChange={(e) =>
                        handleStationTypeChange(idx, "coverageArea", e.target.value)
                      }
                    />
                  </label>
                  <label className="field">
                    <span>H min</span>
                    <input
                      type="number"
                      value={st.handoverMin}
                      onChange={(e) =>
                        handleStationTypeChange(idx, "handoverMin", e.target.value)
                      }
                    />
                  </label>
                  <label className="field">
                    <span>H max</span>
                    <input
                      type="number"
                      value={st.handoverMax}
                      onChange={(e) =>
                        handleStationTypeChange(idx, "handoverMax", e.target.value)
                      }
                    />
                  </label>
                </div>
              ))}
            </section>

            <section className="card">
              <div className="card-header">
                <h2>Handover</h2>
                <button type="button" onClick={addHandover}>
                  +
                </button>
              </div>
              {handovers.map((h, idx) => (
                <div className="card-row" key={`ho-${idx}`}>
                  <label className="field">
                    <span>ID типа станции</span>
                    <input
                      type="number"
                      value={h.stationTypeId}
                      onChange={(e) =>
                        handleHandoverChange(idx, "stationTypeId", e.target.value)
                      }
                    />
                  </label>
                  <label className="field">
                    <span>Значение H</span>
                    <input
                      type="number"
                      value={h.value}
                      onChange={(e) =>
                        handleHandoverChange(idx, "value", e.target.value)
                      }
                    />
                  </label>
                </div>
              ))}
            </section>

            <section className="card span2">
              <div className="card-header">
                <h2>Районы</h2>
                <button type="button" onClick={addDistrict}>
                  +
                </button>
              </div>
              {districts.map((d, idx) => (
                <div className="card-row district-row" key={`d-${idx}`}>
                  <label className="field">
                    <span>ID</span>
                    <input
                      value={d.id}
                      onChange={(e) =>
                        handleDistrictChange(idx, "id", e.target.value)
                      }
                    />
                  </label>
                  <label className="field">
                    <span>Площадь района (s)</span>
                    <input
                      type="number"
                      step="any"
                      value={d.area}
                      onChange={(e) =>
                        handleDistrictChange(idx, "area", e.target.value)
                      }
                    />
                  </label>
                  <label className="field">
                    <span>Коэффициент застройки (K)</span>
                    <input
                      type="number"
                      step="any"
                      value={d.k}
                      onChange={(e) =>
                        handleDistrictChange(idx, "k", e.target.value)
                      }
                    />
                  </label>
                  <label className="field">
                    <span>ID станций (через запятую)</span>
                    <input
                      value={d.stations}
                      onChange={(e) =>
                        handleDistrictChange(idx, "stations", e.target.value)
                      }
                    />
                  </label>
                </div>
              ))}
            </section>
          </div>
        )}

        <div className="actions">
          <button type="submit" className="primary" disabled={loading}>
            {loading ? "Считаем..." : "Выполнить расчет"}
          </button>
          {error && <span className="error">Ошибка: {error}</span>}
        </div>
      </form>

      {result && (
        <section className="result">
          <div className="result-card">
            <div className="card-header">
              <h3>Результат</h3>
              <span className="pill">totalN: {result.totalN}</span>
            </div>
            <div className="table">
              <div className="table-head">
                <span>Район</span>
                <span>n</span>
                <span>handoverAvg</span>
                <span>Корректировка</span>
              </div>
              {result.districtResults?.map((d) => (
                <div className="table-row" key={d.districtId}>
                  <span>{d.districtId}</span>
                  <span>{d.n}</span>
                  <span>{d.handoverAvg}</span>
                  <span className={d.handoverAdjusted ? "tag danger" : "tag ok"}>
                    {d.handoverAdjusted ? "1.4 применено" : "OK"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

export default App;
