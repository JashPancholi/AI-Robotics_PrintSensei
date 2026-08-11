import { useCallback, useEffect, useLayoutEffect, useState } from 'react'

const history = [
  { id: 1, title: 'Binary Search', desc: 'O(log n) · divide & conquer', mode: 'study', time: '09:41' },
  { id: 2, title: 'Arduino Uno', desc: 'Rev3 ATmega328P board', mode: 'inventory', time: '09:28' },
  { id: 3, title: 'Resistor 10kΩ', desc: '10k ohm 1/4W CFR', mode: 'inventory', time: '09:15' },
  { id: 4, title: 'Merge Sort', desc: 'O(n log n) · stable', mode: 'study', time: '08:54' },
  { id: 5, title: 'Raspberry Pi 4', desc: 'Model B 4GB LPDDR4', mode: 'product', time: '08:30' },
]

const modeNames = { study: 'Study', inventory: 'Inventory', product: 'Product', qr: 'QR Code' }
const iconStroke = (color = 'var(--dim)') => ({ stroke: color, fill: 'none', strokeWidth: 1.4, strokeLinecap: 'round', strokeLinejoin: 'round' })

function WifiIcon({ on = false }) {
  const color = on ? 'var(--text)' : 'var(--dim)'
  return <svg width="15" height="15" viewBox="0 0 15 15"><path d="M1.5 5.5C3.5 3.3 5.4 2.5 7.5 2.5s4 .8 6 3" {...iconStroke(color)} /><path d="M3.5 7.8C5 6.4 6.2 5.8 7.5 5.8s2.5.6 4 2" {...iconStroke(color)} /><path d="M5.5 10C6.2 9.3 6.8 9 7.5 9s1.3.3 2 1" {...iconStroke(color)} /><circle cx="7.5" cy="12.5" r=".8" fill={color} /></svg>
}

function PrinterIcon({ on = false }) {
  const color = on ? 'var(--text)' : 'var(--dim)'
  return <svg width="15" height="15" viewBox="0 0 15 15"><path d="M4 5V3.5h7V5" {...iconStroke(color)} /><rect x="2" y="5" width="11" height="6.5" rx="1" {...iconStroke(color)} /><path d="M4 8.5h7M4 10.5h4" {...iconStroke(color)} /></svg>
}

function CameraIcon({ on = false }) {
  const color = on ? 'var(--text)' : 'var(--dim)'
  return <svg width="15" height="15" viewBox="0 0 15 15"><path d="M5.5 3h4l1 1.5H13a1 1 0 0 1 1 1V12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V5.5a1 1 0 0 1 1-1h1.5L4.5 3z" {...iconStroke(color)} /><circle cx="7.5" cy="8.5" r="2.2" {...iconStroke(color)} /></svg>
}

function HistoryIcon() { return <svg width="15" height="15" viewBox="0 0 15 15"><circle cx="7.5" cy="7.5" r="5.5" {...iconStroke()} /><path d="M7.5 4.5v3.2l1.8 1.5" {...iconStroke()} /></svg> }
function SettingsIcon() { return <svg width="15" height="15" viewBox="0 0 15 15"><circle cx="7.5" cy="7.5" r="2" {...iconStroke()} /><path d="M7.5 1.5v2M7.5 11.5v2M1.5 7.5h2M11.5 7.5h2M3.4 3.4l1.4 1.4M10.2 10.2l1.4 1.4M11.6 3.4l-1.4 1.4M4.8 10.2l-1.4 1.4" {...iconStroke()} /></svg> }
function BackIcon() { return <svg width="14" height="14" viewBox="0 0 14 14"><path d="M9 2.5L4.5 7 9 11.5" {...iconStroke()} /></svg> }
function NextIcon() { return <svg width="12" height="12" viewBox="0 0 12 12"><path d="M4.5 2l3 4-3 4" {...iconStroke()} /></svg> }
function RetryIcon() { return <svg width="14" height="14" viewBox="0 0 14 14"><path d="M12 7A5 5 0 1 1 9.5 3" {...iconStroke('var(--sub)')} /><path d="M9.5 3H12.5V6" {...iconStroke('var(--sub)')} /></svg> }

function SuccessIcon() {
  return <svg width="40" height="40" viewBox="0 0 40 40"><circle cx="20" cy="20" r="18" {...iconStroke('var(--led-green)')} /><path d="M11 20l6.5 6.5 12-13" {...iconStroke('var(--led-green)')} strokeWidth="2" /></svg>
}

function VoiceIcon() {
  return <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><rect x="7" y="2" width="8" height="11" rx="4" stroke="var(--sub)" strokeWidth="1.4" /><path d="M4 11c0 3.9 3.1 7 7 7s7-3.1 7-7" stroke="var(--sub)" strokeWidth="1.4" strokeLinecap="round" /><line x1="11" y1="18" x2="11" y2="21" stroke="var(--sub)" strokeWidth="1.4" strokeLinecap="round" /></svg>
}

function CameraVoiceIcon() {
  return <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><rect x="1.5" y="5" width="12" height="9" rx="1.2" stroke="var(--sub)" strokeWidth="1.4" /><path d="M13.5 9l5-3v8l-5-3" stroke="var(--sub)" strokeWidth="1.4" strokeLinejoin="round" /><circle cx="7.5" cy="9.5" r="2" stroke="var(--sub)" strokeWidth="1.4" /></svg>
}

function TextIcon() {
  return <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><rect x="2" y="6" width="18" height="10" rx="1.5" stroke="var(--sub)" strokeWidth="1.4" /><path d="M6 10h1M10 10h1M14 10h1M7 13h8" stroke="var(--sub)" strokeWidth="1.4" strokeLinecap="round" /></svg>
}

function StudyIcon() { return <svg width="22" height="22" viewBox="0 0 22 22"><rect x="3" y="3" width="16" height="16" rx="1.5" {...iconStroke('var(--sub)')} /><path d="M6 7.5h10M6 11h10M6 14.5h6" {...iconStroke('var(--sub)')} /></svg> }
function InventoryIcon() { return <svg width="22" height="22" viewBox="0 0 22 22"><path d="M11 3L3 7v8l8 4 8-4V7L11 3z" {...iconStroke('var(--sub)')} /><path d="M3 7l8 4 8-4M11 11v8" {...iconStroke('var(--sub)')} /></svg> }
function ProductIcon() { return <svg width="22" height="22" viewBox="0 0 22 22"><rect x="3" y="3" width="16" height="16" rx="1.5" {...iconStroke('var(--sub)')} /><path d="M6 8h10M6 11.5h6M14.5 14l2 2" {...iconStroke('var(--sub)')} /><circle cx="14" cy="13.5" r="2.5" {...iconStroke('var(--sub)')} /></svg> }

function QrIcon() {
  return <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><rect x="3" y="3" width="6" height="6" rx=".5" stroke="var(--sub)" strokeWidth="1.4" /><rect x="4.5" y="4.5" width="3" height="3" fill="var(--sub)" /><rect x="13" y="3" width="6" height="6" rx=".5" stroke="var(--sub)" strokeWidth="1.4" /><rect x="14.5" y="4.5" width="3" height="3" fill="var(--sub)" /><rect x="3" y="13" width="6" height="6" rx=".5" stroke="var(--sub)" strokeWidth="1.4" /><rect x="4.5" y="14.5" width="3" height="3" fill="var(--sub)" /><rect x="13" y="13" width="2.5" height="2.5" fill="var(--sub)" /><rect x="16.5" y="13" width="2.5" height="2.5" fill="var(--sub)" /><rect x="13" y="16.5" width="2.5" height="2.5" fill="var(--sub)" /><rect x="16.5" y="16.5" width="2.5" height="2.5" fill="var(--sub)" /></svg>
}

function StatusDot({ color, pulse = false }) { return <div className={pulse ? 'status-dot pulse' : 'status-dot'} style={{ background: color ?? 'transparent' }} /> }

function Bar({ children }) { return <div className="top-bar">{children}</div> }
function IconButton({ onClick, className = '', children, label }) { return <button type="button" aria-label={label} onClick={onClick} className={`icon-button ${className}`}>{children}</button> }

function Home({ onStart, onSettings, onHistory }) {
  return <div className="screen">
    <Bar>
      <div className="status-icons"><WifiIcon on /><PrinterIcon on /><CameraIcon /></div>
      <span className="mono status-copy" />
      <div className="bar-actions"><IconButton label="History" onClick={onHistory}><HistoryIcon /></IconButton><IconButton label="Settings" onClick={onSettings}><SettingsIcon /></IconButton></div>
    </Bar>
    <div className="center-body home-body">
      <StatusDot pulse />
      <div className="ready-copy"><div className="ready-title">Ready</div><div className="ready-subtitle" /></div>
      <button className="primary-button start-button" onClick={onStart}>Tap to Start</button>
    </div>
    <div className="home-footer"><span className="mono" /></div>
  </div>
}

const modes = [
  { id: 'study', label: 'Study', Icon: StudyIcon },
  { id: 'inventory', label: 'Inventory', Icon: InventoryIcon },
  { id: 'product', label: 'Product', Icon: ProductIcon },
  { id: 'qr', label: 'QR Code', Icon: QrIcon },
]

function ModeSelect({ onSelect, onBack, onSettings }) {
  return <div className="screen"><Bar><IconButton label="Back" onClick={onBack}><BackIcon /></IconButton><span className="bar-title title-after-back">Select Mode</span></Bar>
    <div className="mode-grid">
      {modes.map(({ id, label, Icon }) => <button className="tile-button" key={id} onClick={() => onSelect(id)}><Icon /><span>{label}</span></button>)}
      <div className="empty-tile" />
      <button className="tile-button settings-tile" onClick={onSettings}><SettingsIcon /><span>Settings</span></button>
    </div>
  </div>
}

const methods = [
  { id: 'voice', label: 'Voice', sub: 'Speak your label', Icon: VoiceIcon },
  { id: 'camera+voice', label: 'Camera + Voice', sub: 'Scan then describe', Icon: CameraVoiceIcon },
  { id: 'text', label: 'Text', sub: 'Type manually', Icon: TextIcon },
]

function InputMethod({ mode, onSelect, onBack }) {
  return <div className="screen"><Bar><IconButton label="Back" onClick={onBack}><BackIcon /></IconButton><span className="bar-title title-after-back">Input Method</span><span className="bar-meta">{modeNames[mode]}</span></Bar>
    <div className="method-grid">{methods.map(({ id, label, sub, Icon }) => <button className="method-tile" key={id} onClick={() => onSelect(id)}><Icon /><span className="method-title">{label}</span><span className="method-subtitle">{sub}</span></button>)}</div>
  </div>
}

function CameraCapture({ onCaptured, onBack }) {
  const [captured, setCaptured] = useState(false)
  const capture = () => { setCaptured(true); window.setTimeout(onCaptured, 700) }
  return <div className="screen"><Bar><StatusDot color="var(--led-blue)" pulse /><span className="bar-title status-title">Camera</span><span className="step-copy">· step 1 of 2</span><IconButton label="Close" className="close-button" onClick={onBack}>×</IconButton></Bar>
    <div className="center-body camera-body"><div className="camera-frame"><i className="corner top left" /><i className="corner top right" /><i className="corner bottom left" /><i className="corner bottom right" /><span className={captured ? 'capture-done' : 'camera-prompt'}>{captured ? 'Captured ✓' : 'Aim at subject'}</span></div>
      <button className={`primary-button capture-button ${captured ? 'is-captured' : ''}`} disabled={captured} onClick={capture}>{captured ? 'Captured' : 'Capture Photo'}</button>
    </div>
  </div>
}

function Capture({ mode, inputMethod, onCapture, onBack }) {
  const [recordState, setRecordState] = useState('idle')
  const [text, setText] = useState('')
  const isText = inputMethod === 'text'
  const finishRecording = () => { if (recordState !== 'holding') return; setRecordState('done'); window.setTimeout(onCapture, 600) }
  return <div className="screen"><Bar><StatusDot color="var(--led-blue)" pulse /><span className="bar-title status-title">{modeNames[mode]}</span>{inputMethod === 'camera+voice' && <span className="step-copy">· step 2 of 2</span>}<IconButton label="Close" className="close-button" onClick={onBack}>×</IconButton></Bar>
    {isText ? <div className="center-body text-body"><textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Describe what to label…" /><button className="primary-button continue-button" disabled={!text.trim()} onClick={() => text.trim() && onCapture()}>Continue</button></div>
      : <div className="center-body voice-body"><div className="voice-visual"><svg width="26" height="30" viewBox="0 0 26 30" fill="none"><rect x="7" y="2" width="12" height="16" rx="6" stroke={recordState === 'holding' ? 'var(--led-blue)' : 'var(--dim)'} strokeWidth="1.4" /><path d="M3 15c0 5.5 4.5 9 10 9s10-3.5 10-9" stroke={recordState === 'holding' ? 'var(--led-blue)' : 'var(--dim)'} strokeWidth="1.4" strokeLinecap="round" /><line x1="13" y1="24" x2="13" y2="29" stroke={recordState === 'holding' ? 'var(--led-blue)' : 'var(--dim)'} strokeWidth="1.4" strokeLinecap="round" /></svg>
          <div className={recordState === 'holding' ? 'wave waveform' : 'waveform'}>{[6, 12, 20, 26, 20, 12, 6].map((height, index) => <span key={index} style={{ height: recordState === 'holding' ? height : 4 }} />)}</div></div>
        <button className={`primary-button record-button ${recordState}`} onPointerDown={() => setRecordState('holding')} onPointerUp={finishRecording} onPointerCancel={finishRecording} onPointerLeave={finishRecording}>{recordState === 'done' ? 'Captured' : recordState === 'holding' ? 'Recording…' : 'Hold to Record'}</button>
      </div>}
  </div>
}

function Processing({ onCancel }) {
  return <div className="screen"><Bar><StatusDot color="var(--led-purple)" pulse /><span className="bar-title status-title">Processing</span></Bar><div className="center-body processing-body"><svg width="36" height="36" viewBox="0 0 36 36" fill="none" className="spin"><circle cx="18" cy="18" r="14" stroke="var(--border)" strokeWidth="3" /><path d="M18 4a14 14 0 0 1 14 14" stroke="var(--led-purple)" strokeWidth="3" strokeLinecap="round" /></svg><div className="processing-copy"><div>Generating label</div><span>AI is creating content…</span></div><div className="progress-track processing-progress"><div className="fill-anim" /></div><button className="ghost-button" onClick={onCancel}>Cancel</button></div></div>
}

const previews = {
  study: { title: 'Binary Search', desc: 'O(log n) · divide & conquer algorithm for sorted arrays' },
  inventory: { title: 'Resistor 10kΩ', desc: '10k ohm 1/4W CFR · brown-black-orange' },
  product: { title: 'RPi Module', desc: 'Raspberry Pi Compute Module 4 · 4GB' },
  qr: { title: 'printsensei.local', desc: 'Local network resource link' },
}

function Preview({ mode, onEdit, onPrint }) {
  const { title, desc } = previews[mode]
  const date = new Date().toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }).toUpperCase()
  return <div className="screen"><Bar><span className="bar-title">Preview</span><span className="bar-meta">{modeNames[mode]}</span></Bar><div className="center-body preview-body"><div className="label-preview"><div className="label-main"><div className="label-copy"><div className="label-title">{title}</div><div className="label-desc">{desc}</div></div><div className="qr-box"><QrIcon /></div></div><div className="label-footer mono">PRINTSENSEI · {date} · 62×29MM</div></div></div><div className="preview-actions"><button className="ghost-button" onClick={onEdit}>Edit</button><button className="primary-button" onClick={onPrint}>Print</button></div></div>
}

function Printing({ onDone }) {
  useEffect(() => { const timer = window.setTimeout(onDone, 3200); return () => window.clearTimeout(timer) }, [onDone])
  return <div className="screen"><Bar><StatusDot color="var(--led-green)" pulse /><span className="bar-title status-title">Printing</span></Bar><div className="center-body printing-body"><SuccessIcon /><div className="printed-copy"><div>Label printed</div><span>Returning to home…</span></div><div className="progress-track print-progress"><div className="drain-anim" /></div></div></div>
}

function Settings({ onBack }) {
  const rows = [
    { icon: <WifiIcon on />, label: 'Wi-Fi', value: 'PrintNet_5G' },
    { icon: <PrinterIcon on />, label: 'Printer', value: 'Brother QL-800' },
    { icon: <CameraIcon on />, label: 'Camera', value: 'Pi Camera v2' },
  ]
  return <div className="screen"><Bar><IconButton label="Back" onClick={onBack}><BackIcon /></IconButton><span className="bar-title title-after-back">Settings</span></Bar><div className="settings-list scroll-hidden">{rows.map((row) => <button className="settings-row" key={row.label}>{row.icon}<span>{row.label}</span><small>{row.value}</small><NextIcon /></button>)}<div className="brightness"><div><span>Brightness</span><small>80%</small></div><div className="brightness-track"><div className="brightness-fill" /><i /></div></div><button className="settings-row about-row"><span>About</span><small className="mono">v1.0.0 · RPi 4B</small><NextIcon /></button></div></div>
}

function History({ onBack, onReprint }) {
  return <div className="screen"><Bar><IconButton label="Back" onClick={onBack}><BackIcon /></IconButton><span className="bar-title title-after-back">History</span><span className="history-count">{history.length} labels</span></Bar><div className="history-list scroll-hidden">{history.map((item) => <div className="history-row" key={item.id}><div className="history-copy"><div>{item.title}</div><span>{item.desc}</span></div><span className="mono history-time">{item.time}</span><IconButton label={`Reprint ${item.title}`} onClick={() => onReprint(item)}><RetryIcon /></IconButton></div>)}</div></div>
}

function useDisplayScale() {
  const [scale, setScale] = useState(1)
  useLayoutEffect(() => {
    const update = () => setScale(Math.min(window.innerWidth / 320, window.innerHeight / 240))
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])
  return scale
}

export default function App() {
  const [screen, setScreen] = useState('home')
  const [mode, setMode] = useState('study')
  const [inputMethod, setInputMethod] = useState('voice')
  const scale = useDisplayScale()
  const go = useCallback((next) => setScreen(next), [])

  useEffect(() => {
    if (screen !== 'processing') return undefined
    const timer = window.setTimeout(() => go('preview'), 2600)
    return () => window.clearTimeout(timer)
  }, [screen, go])

  const selectMethod = (method) => { setInputMethod(method); go(method === 'camera+voice' ? 'camera-capture' : 'capture') }
  const renderScreen = () => {
    switch (screen) {
      case 'mode-select': return <ModeSelect onSelect={(value) => { setMode(value); go('input-method') }} onBack={() => go('home')} onSettings={() => go('settings')} />
      case 'input-method': return <InputMethod mode={mode} onSelect={selectMethod} onBack={() => go('mode-select')} />
      case 'camera-capture': return <CameraCapture onCaptured={() => go('capture')} onBack={() => go('input-method')} />
      case 'capture': return <Capture mode={mode} inputMethod={inputMethod} onCapture={() => go('processing')} onBack={() => go('input-method')} />
      case 'processing': return <Processing onCancel={() => go('home')} />
      case 'preview': return <Preview mode={mode} onEdit={() => go('capture')} onPrint={() => go('printing')} />
      case 'printing': return <Printing onDone={() => go('home')} />
      case 'settings': return <Settings onBack={() => go('home')} />
      case 'history': return <History onBack={() => go('home')} onReprint={(item) => { setMode(item.mode); go('printing') }} />
      default: return <Home onStart={() => go('mode-select')} onSettings={() => go('settings')} onHistory={() => go('history')} />
    }
  }

  return <main className="lcd-viewport"><div className="lcd-screen" style={{ transform: `scale(${scale})` }}>{renderScreen()}</div></main>
}
