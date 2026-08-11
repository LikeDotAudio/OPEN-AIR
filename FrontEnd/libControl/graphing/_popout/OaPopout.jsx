/**
 * Header: OaPopout.jsx
 * Purpose: Detach a graph into a full-window overlay or its own browser window.
 * Description: One host wrapper, shared by every graph widget, that MOVES the
 *              live element instead of copying a picture of it.
 *
 * Version: 26.08.08.2
 * Change Log:
 * - 2026-08-08: Placement re-asserted every render, so no ordinary re-render can
 *               pull the graph back into the tab while it is detached.
 * - 2026-08-08: Initial version — replaces DynamicGraph's private pop-out, which
 *               wrote a snapshot into the new window and left the tab drawing a
 *               second copy of the same chart.
 */

// A POPPED-OUT GRAPH IS THE SAME GRAPH, NOT A PICTURE OF ONE.
//
// The old pop-out serialised the chart's option into a fresh document and
// re-initialised echarts there. Two things followed from that, both of which
// this replaces:
//
//   - The detached window froze. It held whatever the option said at the moment
//     the button was pressed, so the next capture — a new trace, a new span —
//     updated the tab and nothing else. There was no live wiring to update,
//     because the copy had no connection to React or the bus at all.
//   - The tab kept drawing too. Two charts of the same data, one of them stale,
//     side by side and only one of them right.
//
// So nothing is copied. The widget's own DOM node is APPENDED into the other
// container — overlay or new window — and moved back when it returns. There is
// one echarts instance, one React subtree, one set of MQTT subscriptions, and
// they are the ones that were already live: a new dataset lands in the detached
// window for the same reason it landed in the tab, with no syncing code in
// between. The tab is then empty by construction, not by a second code path.
//
// The holder is the only child of its slot, and the slot never gains a sibling,
// so React is never asked to insert a node relative to one that has walked off:
// React only ever reconciles INSIDE the holder, which travels with it.
//
// KNOWN LIMIT: React 18 delegates events at the app's root container, in THIS
// document. A React onClick inside the detached window therefore does not fire.
// echarts draws its own listeners on the element, so zoom, drag, tooltip and the
// dataZoom slider all work; a React-authored button in a detached graph will not.
// The window's own chrome (the RETURN TO TAB button) is plain DOM for that
// reason.
(() => {
    const esc = (s) => String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // The detached document is a bare about:blank: it inherits nothing. Widgets
    // that style themselves by class (widget-wrapper, the dark scrollbars) would
    // arrive unstyled, so the tab's stylesheets ride along.
    const inheritedStyles = () => Array.from(
        document.querySelectorAll('style, link[rel="stylesheet"]'),
    ).map((n) => n.outerHTML).join('\n');

    const WINDOW_CSS = `
        html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden;
                     background:#0a0a0a; color:#fff; display:flex; flex-direction:column;
                     font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        #oa-bar { flex:0 0 auto; height:40px; display:flex; align-items:center;
                  justify-content:space-between; padding:0 16px; background:#111;
                  border-bottom:1px solid #333; }
        #oa-title { color:#FF9900; font-weight:bold; font-size:15px; }
        #oa-back { background:#FF9900; border:none; color:#000; border-radius:4px;
                   padding:6px 14px; font-size:12px; font-weight:bold; cursor:pointer; }
        #oa-mount { flex:1 1 auto; min-height:0; display:flex; flex-direction:column;
                    padding:10px; box-sizing:border-box; }
        #oa-mount > * { flex:1 1 auto; min-height:0; width:100%; }
    `;

    const BTN = {
        borderRadius: '4px', padding: '2px 8px', cursor: 'pointer', fontSize: '11px',
        fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px',
    };

    const Host = ({ title, children }) => {
        // 'inline' | 'full' (overlay in this document) | 'window' (its own window)
        const [mode, setMode] = React.useState('inline');
        const [mount, setMount] = React.useState(null);   // #oa-mount in the popup
        const slotRef = React.useRef(null);
        const holderRef = React.useRef(null);
        const overlayRef = React.useRef(null);
        const winRef = React.useRef(null);
        // The slot collapses once its content walks out; remembering the height
        // keeps the block — and everything laid out below it — from jumping.
        const parkedH = React.useRef(0);

        // Widgets resize off the window event (DynamicGraph also watches its own
        // box, but a ResizeObserver made here does not fire for an element that
        // now lives in another document). A move is a resize, so say so.
        //
        // Said once per frame at most: this event reaches EVERY widget on the
        // panel, and dragging the detached window's edge emits them faster than
        // a canvas can redraw. The trailing repeat catches the layout settling
        // after a move, which the first shout is too early to see.
        const pending = React.useRef(false);
        const nudge = React.useCallback((settle) => {
            const fire = () => { try { window.dispatchEvent(new Event('resize')); } catch (e) {} };
            if (!pending.current) {
                pending.current = true;
                window.requestAnimationFrame(() => { pending.current = false; fire(); });
            }
            if (settle !== false) setTimeout(fire, 140);
        }, []);
        const nudgeSoon = React.useCallback(() => nudge(false), [nudge]);

        // Bring the element home. Called BEFORE the state change that would tear
        // down whatever it is sitting in, so it is never removed with its host.
        const park = React.useCallback(() => {
            const h = holderRef.current, s = slotRef.current;
            if (h && s && h.parentNode !== s) s.appendChild(h);
        }, []);

        // Placement is re-asserted after EVERY render, not just when the mode
        // changes. Host re-renders whenever a value on the panel moves, and a
        // render is React's chance to put a node back where its JSX says it
        // lives — which for the holder is the slot, in the tab. Checking once
        // per mode change would let a single such render leave the graph
        // drawing in the tab while the detached window sat holding nothing.
        // The parent check makes the usual case a no-op, so this costs a
        // comparison per render and moves nothing.
        React.useLayoutEffect(() => {
            const h = holderRef.current;
            if (!h) return;
            const target = mode === 'window' ? mount
                         : mode === 'full' ? overlayRef.current
                         : slotRef.current;
            if (!target || h.parentNode === target) return;
            if (mode !== 'inline') parkedH.current = h.offsetHeight || parkedH.current;
            target.appendChild(h);
            nudge();
        });

        // A move is a resize (see nudge), and so is arriving somewhere new.
        React.useLayoutEffect(() => { nudge(); }, [mode, mount, nudge]);

        const closeWindow = React.useCallback(() => {
            const w = winRef.current;
            park();
            winRef.current = null;
            setMount(null);
            setMode('inline');
            if (w && !w.closed) { try { w.close(); } catch (e) {} }
        }, [park]);

        const openWindow = () => {
            const w = window.open('', '', 'width=1200,height=800,menubar=no,toolbar=no,location=no,status=no');
            if (!w) return;   // blocked; the FULL WINDOW overlay still works
            w.document.open();
            w.document.write(
                `<!DOCTYPE html><html><head><meta charset="utf-8">`
                + `<title>${esc(title || 'Graph')}</title>`
                + `${inheritedStyles()}<style>${WINDOW_CSS}</style></head>`
                + `<body><div id="oa-bar"><span id="oa-title"></span>`
                + `<button id="oa-back">&#8595; RETURN TO TAB</button></div>`
                + `<div id="oa-mount"></div></body></html>`,
            );
            w.document.close();
            // textContent, not markup: a label is authored JSON and may hold anything.
            w.document.getElementById('oa-title').textContent = title || 'Graph';
            w.document.getElementById('oa-back').addEventListener('click', closeWindow);
            w.addEventListener('resize', nudgeSoon);
            w.addEventListener('pagehide', () => { park(); winRef.current = null; setMount(null); setMode('inline'); });
            winRef.current = w;
            setMount(w.document.getElementById('oa-mount'));
            setMode('window');
        };

        // pagehide is not guaranteed on every close path, and a graph that never
        // comes home is a blank panel with no way back. Poll for the window
        // having gone while it is supposed to be open.
        React.useEffect(() => {
            if (mode !== 'window') return;
            const id = setInterval(() => {
                if (!winRef.current || winRef.current.closed) {
                    park(); winRef.current = null; setMount(null); setMode('inline');
                }
            }, 500);
            return () => clearInterval(id);
        }, [mode, park]);

        // A detached window outlives the tab that opened it, holding a graph wired
        // to a bus connection that has gone. Take it with us — on navigation and
        // on unmount (a panel switch), returning the element first either way.
        React.useEffect(() => {
            const bye = () => { const w = winRef.current; if (w && !w.closed) { try { w.close(); } catch (e) {} } };
            window.addEventListener('beforeunload', bye);
            return () => {
                window.removeEventListener('beforeunload', bye);
                park();
                bye();
            };
        }, [park]);

        const detached = mode !== 'inline';

        return (
            <div style={{ position: 'relative', display: 'flex', flexDirection: 'column',
                          flex: '1 1 auto', minHeight: 0, width: '100%' }}>
                <div
                    ref={slotRef}
                    style={{ display: 'flex', flexDirection: 'column', flex: '1 1 auto',
                             minHeight: 0, width: '100%',
                             ...(detached ? { minHeight: `${parkedH.current || 120}px` } : {}) }}
                >
                    {/* data-oa-detached is the one thing a widget can ask about:
                        a chart sized to a panel row should fill the window it was
                        sent to, and only the holder knows which of the two it is
                        currently living in. */}
                    <div style={{ display: 'flex', flexDirection: 'column', flex: '1 1 auto',
                                  minHeight: 0, width: '100%' }}
                         data-oa-detached={detached ? '1' : '0'}
                         ref={holderRef}>
                        {children}
                    </div>
                </div>

                {detached && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex',
                                  alignItems: 'center', justifyContent: 'center',
                                  flexDirection: 'column', gap: '10px', color: '#666',
                                  fontSize: '12px', letterSpacing: '1px', pointerEvents: 'none' }}>
                        <div>{mode === 'window' ? 'SHOWING IN A DETACHED WINDOW' : 'SHOWING FULL WINDOW'}</div>
                    </div>
                )}

                <div style={{ position: 'absolute', top: 6, right: 10, zIndex: 10,
                              display: 'flex', gap: '6px' }}>
                    {mode === 'window' ? (
                        <button
                            onClick={closeWindow}
                            title="Bring the graph back into this tab"
                            style={{ ...BTN, background: 'rgba(255, 153, 0, 0.2)',
                                     border: '1px solid #FF9900', color: '#FF9900' }}
                        >
                            <span>&#8595;</span> RETURN TO TAB
                        </button>
                    ) : (
                        <React.Fragment>
                            <button
                                onClick={() => (mode === 'full' ? (park(), setMode('inline')) : setMode('full'))}
                                title="Full Window View"
                                style={{ ...BTN, background: 'rgba(255, 153, 0, 0.2)',
                                         border: '1px solid #FF9900', color: '#FF9900' }}
                            >
                                <span>&#10530;</span> {mode === 'full' ? 'EXIT FULL WINDOW' : 'FULL WINDOW'}
                            </button>
                            <button
                                onClick={openWindow}
                                title="Pop to New Window / Tab"
                                style={{ ...BTN, background: 'rgba(51, 161, 253, 0.2)',
                                         border: '1px solid #33A1FD', color: '#33A1FD' }}
                            >
                                <span>&#10113;</span> POP TO NEW WINDOW
                            </button>
                        </React.Fragment>
                    )}
                </div>

                {mode === 'full' && (
                    <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
                                  backgroundColor: 'rgba(0, 0, 0, 0.92)', zIndex: 99999,
                                  display: 'flex', flexDirection: 'column', padding: '20px',
                                  boxSizing: 'border-box' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between',
                                      alignItems: 'center', marginBottom: '10px' }}>
                            <div style={{ color: '#FF9900', fontSize: '18px', fontWeight: 'bold' }}>
                                {title} (Full Window)
                            </div>
                            <button
                                onClick={() => { park(); setMode('inline'); }}
                                style={{ background: '#FF9900', border: 'none', color: '#000',
                                         borderRadius: '4px', padding: '6px 16px', cursor: 'pointer',
                                         fontSize: '13px', fontWeight: 'bold' }}
                            >
                                ✕ Close
                            </button>
                        </div>
                        <div ref={overlayRef}
                             style={{ flex: '1 1 auto', minHeight: 0, width: '100%',
                                      display: 'flex', flexDirection: 'column' }} />
                    </div>
                )}
            </div>
        );
    };

    window.OaPopout = { Host };
})();
