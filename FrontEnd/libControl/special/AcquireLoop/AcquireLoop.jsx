/**
 * Header: AcquireLoop.jsx
 * Purpose: Hold a query open — re-fire a sibling's nab on an interval.
 * Description: The CONTINUOUS half of acquire; ACQUIRE SINGLE is an ordinary actuator.
 *
 * Version: 26.08.08.1
 * Change Log:
 * - 2026-08-08: Initial version — DMM acquisition.
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

    React.useEffect(() => {
        if (!isOn || !trigger || !target) return;
        // Both edges, exactly as the button reports them: YAK acts on the
        // truthy one and ignores the release (mqtt.rs), so the pair reads as
        // one press per tick rather than two.
        const tick = () => { trigger(target, true); trigger(target, false); };
        tick();
        const id = setInterval(tick, intervalMs);
        return () => clearInterval(id);
    }, [isOn, trigger, target, intervalMs]);

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
