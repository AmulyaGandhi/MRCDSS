import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { assistantChat, type AssistantContext, type AssistantPageContext } from '../api/assistant';

type Message = {
  role: 'user' | 'assistant';
  text: string;
  sources?: string[];
  grounded?: boolean;
  error?: boolean;
};

const ROUTE_PAGE_CONTEXT: Array<{ prefix: string; page: AssistantPageContext }> = [
  { prefix: '/risk-analysis', page: 'risk_analysis' },
  { prefix: '/planning', page: 'planning_priorities' },
  { prefix: '/methodology', page: 'methodology' },
  { prefix: '/about', page: 'about' },
  { prefix: '/districts', page: 'district_explorer' },
  { prefix: '/', page: 'overview' },
];

function pageContextFor(pathname: string): AssistantPageContext {
  for (const { prefix, page } of ROUTE_PAGE_CONTEXT) {
    if (pathname.startsWith(prefix)) return page;
  }
  return 'overview';
}

const GENERIC_QUESTIONS = [
  'What is the risk classification of Warangal?',
  'How many districts are High Risk?',
  'Which indicators matter most (SHAP)?',
  'How were the risk classes generated?',
];

const PAGE_QUESTIONS: Record<AssistantPageContext, string[]> = {
  overview: GENERIC_QUESTIONS,
  district_explorer: [
    'Show me the high priority districts',
    'What is the risk of Warangal?',
    'Explain the DSS priority system',
    'What does recent HMIS show?',
  ],
  risk_analysis: [
    'Which model was selected and why?',
    'How were the risk classes generated?',
    'Explain the SHAP values',
    'How many districts are High Risk?',
  ],
  planning_priorities: [
    'What should planners focus on?',
    'Show me the planning rules',
    'Which districts show repeated High Priority observations?',
    'How does the DSS map planning focus?',
  ],
  methodology: [
    'How were the risk classes generated?',
    'Why was Dataset 3 not used to retrain?',
    'Which model was selected?',
    'Explain the SHAP methodology',
  ],
  about: [
    'What is MRCDSS?',
    'How does the Decision Support System work?',
    'Why was Dataset 3 not used to retrain?',
    'What indicators are used?',
  ],
};

export const ASSISTANT_DISTRICT_EVENT = 'mrcdss:assistant:district';

export default function Assistant() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [context, setContext] = useState<AssistantContext | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const pageContext = pageContextFor(location.pathname);
  const focusName = context?.district
    ? `${context.district}${context.state ? ` (${context.state})` : ''}`
    : null;

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail ?? null;
      if (detail === null) {
        setContext(null);
        return;
      }
      setContext({ state: detail.state ?? null, district: detail.district ?? null, matched: true, risk_class: detail.risk_class ?? null });
    };
    window.addEventListener(ASSISTANT_DISTRICT_EVENT, handler);
    return () => window.removeEventListener(ASSISTANT_DISTRICT_EVENT, handler);
  }, []);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, busy]);

  const suggested = useCallback(() => {
    if (context?.district) {
      return [
        `What is the risk of ${context.district}?`,
        `What are the planning priorities for ${context.district}?`,
        `Which indicators contributed to ${context.district}'s classification?`,
        `What is the latest HMIS evidence for ${context.district}?`,
      ];
    }
    return PAGE_QUESTIONS[pageContext] ?? GENERIC_QUESTIONS;
  }, [context, pageContext]);

  const send = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || busy) return;
      const userMessage: Message = { role: 'user', text };
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setBusy(true);
      const history = messages.slice(-8).map(({ role, text }) => ({ role, text }));
      try {
        const response = await assistantChat({
          message: text,
          state: context?.state,
          district: context?.district,
          page_context: pageContext,
          history,
          scope: context,
        });
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', text: response.answer, sources: response.sources, grounded: response.grounded },
        ]);
        if (response.context?.district) {
          setContext(response.context);
        }
      } catch (err) {
        const detail = err instanceof Error ? err.message : String(err);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text:
              "I couldn't reach the assistant service right now. " +
              `(Error: ${detail}) Check that the MRCDSS backend is running at the API base URL used by this app.`,
            error: true,
          },
        ]);
      } finally {
        setBusy(false);
      }
    },
    [busy, context, messages, pageContext],
  );

  const suggestion = (q: string) => send(q);

  return (
    <>
      <button
        type="button"
        className="mrc-asst-launcher"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="mrc-asst-launcher-caret" aria-hidden="true">✦</span>
        <span>{focusName ? `Ask Disha about ${focusName}` : 'Ask Disha'}</span>
      </button>

      {open && (
        <aside className="mrc-asst-panel" role="dialog" aria-label="Disha - MRCDSS Decision Assistant">
          <div className="mrc-asst-head">
            <div>
              <div className="mrc-asst-title">✦ Disha</div>
              <div className="mrc-asst-subtitle">MRCDSS Decision Assistant</div>
            </div>
            <button type="button" className="mrc-asst-close" aria-label="Close assistant" onClick={() => setOpen(false)}>
              ×
            </button>
          </div>

          <div className="mrc-asst-list" ref={listRef}>
            {messages.length === 0 && !busy ? (
              <div className="mrc-asst-empty">
                <p className="mrc-asst-greeting">
                  {focusName
                    ? `Hi, I'm Disha, focused on ${focusName}. What would you like to know?`
                    : "Hi, I'm Disha, the MRCDSS Decision Assistant. Select a district on the map or ask a question and I'll answer using the MRCDSS evidence."}
                </p>
                <div className="mrc-asst-suggestions">
                  {suggested().map((q) => (
                    <button key={q} type="button" className="mrc-asst-chip" onClick={() => suggestion(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => (
                <div key={i} className={`mrc-asst-row ${m.role}`}>
                  <div className="mrc-asst-bubble">
                    <span className="mrc-asst-meta">{m.role === 'user' ? 'You' : 'Disha'}</span>
                    <p className="mrc-asst-text">{m.text}</p>
                    {m.role === 'assistant' && (m.sources && m.sources.length > 0) && (
                      <div className="mrc-asst-sources">
                        {m.sources.map((s) => (
                          <span key={s} className="mrc-asst-source-chip">{s}</span>
                        ))}
                      </div>
                    )}
                    {m.role === 'assistant' && !m.error && (
                      <div className="mrc-asst-footnote">
                        {m.grounded ? 'Grounded in MRCDSS evidence' : 'Not available in MRCDSS'}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {busy && (
              <div className="mrc-asst-row assistant">
                <div className="mrc-asst-bubble">
                  <span className="mrc-asst-meta">Disha</span>
                  <p className="mrc-asst-text">Thinking…</p>
                </div>
              </div>
            )}
          </div>

          <div className="mrc-asst-input-row">
            <input
              ref={inputRef}
              type="text"
              className="mrc-asst-input"
              placeholder="Ask Disha…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') send(input);
              }}
              disabled={busy}
            />
            <button type="button" className="mrc-asst-send" onClick={() => send(input)} disabled={busy || !input.trim()}>
              Send
            </button>
          </div>
        </aside>
      )}
    </>
  );
}