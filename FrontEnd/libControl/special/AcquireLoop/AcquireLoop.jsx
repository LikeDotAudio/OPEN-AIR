/**
 * Header: AcquireLoop.jsx
 * Purpose: Hold a query open — re-fire a sibling's nab on an interval.
 * Description: The CONTINUOUS half of acquire; ACQUIRE SINGLE is an ordinary actuator.
 *
 * Version: 26.08.08.2
 * Change Log:
 * - 2026-08-08: Initial version — DMM acquisition.
 * - 2026-08-08: Best-effort pacing. With `yak_awaits` the loop waits for the
 *               reply rather than a guessed interval, so a scope polls as fast
 *               as it can hand over four channels and no faster.
 */

// A meter reads once per press, and a trend chart of one point is a dot. What
// was missing is not another command — `:READ?` is already bound to the ACQUIRE
// button — but something to keep asking.
//
// So this drives the button rather than the instrument: it publishes to a
// SIBLING control's topic, the one that already carries the nab handler. One
// command, one binding, one place it can be wrong. The loop owns only the
// cadence.
//
// It never fires on mount, and it stops on unmount: an interval that outlives
// the tab it was started on is an instrument being polled by a page nobody is
// looking at.
const AcquireLoop = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const [on, setOn] = useMqtt
        ? window.useMqttState(topic, value !== undefined ? value : false, nodeJson)
        : [value, onChange, 'En'];
    const trigger = window.useMqttTrigger ? window.useMqttTrigger() : null;
    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};

    const intervalMs = Math.max(100, Number(config?.interval_ms) || 1000);
    const targetField = config?.fires || 'Acquire_Single';

    // The sibling sits beside this control under the same block, so its topic is
    // this one's with the leaf swapped. Derived, not authored: a second spelling
    // of the same topic is a second thing to keep in step.
    const target = React.useMemo(() => {
        const parts = String(topic || '').split('/');
        if (parts.length < 2) return '';
        parts[parts.length - 1] = targetField;
        return parts.join('/');
    }, [topic, targetField]);

    const isOn = !(on === undefined || on === null || on === false
        || String(on).trim() === '' || String(on) === '0' || String(on).toLowerCase() === 'false');

    // BEST EFFORT MEANS ASKING AGAIN WHEN THE LAST ANSWER LANDS.
    //
    // A fixed interval has to be guessed, and the guess is wrong in both
    // directions: a meter answers `:READ?` in milliseconds, a scope takes 1.4
    // seconds to hand over four channels of samples. Too fast and requests pile
    // up behind an instrument that is already busy; too slow and the display
    // lags a bench that has moved on.
    //
    // `yak_awaits` names a reading the capture produces, so the loop can watch
    // for the reply instead of counting. Fire, wait for that topic to change,
    // fire again — the cadence is then whatever the instrument can actually
    // sustain, and it needs nobody to tune it. `interval_ms` becomes the FLOOR
    // between requests rather than the period.
    //
    // `timeout_ms` is the guard: a query that never answers must not wedge the
    // loop for the rest of the session, so after it the loop stops waiting and
    // tries again.
    const awaits = nodeJson && (nodeJson.yak_awaits_topic || config?.yak_awaits_topic);
    const timeoutMs = Math.max(500, Number(config?.timeout_ms) || 10000);
    const pending = React.useRef(false);
    const firedAt = React.useRef(0);
    const lastAnswer = React.useRef(undefined);

    // The answer landed — whatever the loop was waiting for is here.
    const answer = awaits ? messages[awaits] : undefined;
    React.useEffect(() => {
        if (answer === undefined) return;
        if (lastAnswer.current !== undefined && answer !== lastAnswer.current) {
            pending.current = false;
        }
        lastAnswer.current = answer;
    }, [answer]);

    React.useEffect(() => {
        if (!isOn || !trigger || !target) return;
        // Both edges, exactly as the button reports them: YAK acts on the
        // truthy one and ignores the release (mqtt.rs), so the pair reads as
        // one press per tick rather than two.
        const fire = () => {
            pending.current = !!awaits;
            firedAt.current = Date.now();
            trigger(target, true);
            trigger(target, false);
        };
        fire();
        const id = setInterval(() => {
            if (pending.current && (Date.now() - firedAt.current) < timeoutMs) return;
            fire();
        }, awaits ? Math.max(50, Number(config?.interval_ms) || 100) : intervalMs);
        return () => { clearInterval(id); pending.current = false; };
    }, [isOn, trigger, target, intervalMs, awaits, timeoutMs]);

    // The face is an ordinary toggle — same widget every other latching control
    // on the bench uses, so it looks like what it is.
    if (window.ButtonToggle) {
        return (
            <window.ButtonToggle
                value={on}
                onChange={setOn}
                config={config}
                topic={topic}
                nodeJson={nodeJson}
            />
        );
    }
    return <button onClick={() => setOn(!isOn)}>{isOn ? 'ACQUIRING' : 'CONTINUOUS'}</button>;
};

window.AcquireLoop = AcquireLoop;
