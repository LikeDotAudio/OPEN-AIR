/**
 * Header: LinkGang.jsx
 * Purpose: Relay one master control's value to every enlisted device strip.
 * Description: The LINK page's fan-out. Renders nothing.
 *
 * Version: 26.08.08.2
 * Change Log:
 * - 2026-08-08: Initial version — generator LINK tab.
 * - 2026-08-08: Honour a per-device VETO set on the instrument's own page
 *               (`link_veto_topics`), so a module can refuse the link from
 *               where the operator is actually working on it.
 */

// A yak_handler names ONE target, and YAK caches ONE handler per topic
// (mqtt.rs: `topic_configs.insert`). So a single master fader cannot command
// four generators however it is authored: whichever device published its
// config last would be the only one that moved.
//
// What the LINK page does instead is push the master's value into each
// device's OWN control topic — the strips repeat_unit already composed onto
// this page, each bound to its own device by prepare(). Those are ordinary
// bound controls: they were going to command their instrument the moment a
// value reached them. The master just decides when, and to whom.
//
//   <station>/Master_Control/Amplitude   ── the operator moves this
//   <station>/Unit_1/Amplitude           ── relayed here (if Unit_1 is linked)
//   <station>/Unit_2/Amplitude           ── and here
//
// Membership is per unit and per page: `Unit_<n>/Link` is a plain toggle with
// no handler of its own, so unlinking a generator is a UI act that touches no
// instrument. A device that is not enlisted is not written to at all — the
// point of a link page is that it can be switched off without first putting
// every follower back where it was.
const LinkGang = ({ config, topic }) => {
    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};
    const trigger = window.useMqttTrigger ? window.useMqttTrigger() : null;

    const masterGroup = config?.master_group || 'Master_Control';
    const memberPrefix = config?.member_prefix || 'Unit_';
    const enlistField = config?.enlist || 'Link';
    const pairs = Array.isArray(config?.gang) ? config.gang : [];

    // TWO WAYS TO BE OUT, and they answer different questions.
    //
    // `Unit_<n>/Link` is this PAGE's switch: which strips the master is driving
    // right now. `link_veto_topics` is the DEVICE's, set on the instrument's own
    // page and stamped here by the builder — "whatever the link page thinks,
    // leave this one alone". The second outranks the first, because the operator
    // who set it is the one standing at that supply with something delicate
    // wired to it, and they will not be looking at the link tab when the master
    // moves.
    const vetoTopics = (config && config.link_veto_topics) || {};

    // This node lives at <station>/<masterGroup>/<its own name>, so the station
    // is its topic with those two segments taken off. Derived rather than
    // authored: the station key is chosen by the manifest, and a second place
    // to spell it is a second place to get it wrong.
    const station = String(topic || '').split('/').slice(0, -2).join('/');

    const valueAt = (t) => {
        const raw = messages[t];
        if (raw === undefined) return undefined;
        try {
            const p = JSON.parse(String(raw));
            if (p && typeof p === 'object' && p.value !== undefined) return p.value;
        } catch (e) { /* plain payload */ }
        return raw;
    };

    const isTruthy = (v) => {
        if (v === undefined || v === null) return false;
        const s = String(v).trim().toLowerCase();
        return !(s === '' || s === '0' || s === 'false' || s === 'off' || s === 'no');
    };

    // Which strips exist is answered by the bus, not by a count passed down: a
    // control seeds its own topic on mount, so the strips announce themselves,
    // and a generator that joins the bench and gets a new strip is relayed to
    // without this widget being told anything.
    //
    // Counted by their ENLIST switch, which is the one control every strip is
    // guaranteed to have published. A momentary control is deliberately never
    // seeded (MqttProvider: seeding a command topic would fire the command on
    // mount), so looking for the strips by their ACQUIRE button found none of
    // them until each had been pressed by hand — with GET ALL VALUES doing
    // nothing at all until it was no longer needed.
    const unitNames = () => {
        const head = `${station}/${memberPrefix}`;
        const tail = `/${enlistField}`;
        const out = [];
        for (const t of Object.keys(messages)) {
            if (!t.startsWith(head) || !t.endsWith(tail)) continue;
            const unit = t.slice(station.length + 1, t.length - tail.length);
            if (unit.indexOf('/') === -1) out.push(unit);
        }
        return out;
    };

    // Two things relay, and NOTHING else does.
    //
    //   the master moved      → every enlisted follower goes with it
    //   a follower was linked → it catches up to where the master already is
    //
    // Both are acts the operator just performed. What must never relay is the
    // first sight of a value: master positions sit retained on their topics, so
    // a page load would otherwise re-command every generator on the bench —
    // switching outputs on, at whatever amplitude the page was last left at,
    // simply because someone opened a tab. First pass records; it does not send.
    const prevMaster = React.useRef(null);
    const prevLinked = React.useRef({});

    React.useEffect(() => {
        if (!trigger || !station) return;

        const master = {};
        for (const pair of pairs) {
            const masterField = pair.master || pair.member;
            const memberField = pair.member || pair.master;
            if (!masterField || !memberField) continue;
            const v = valueAt(`${station}/${masterGroup}/${masterField}`);
            if (v !== undefined) master[memberField] = v;
        }

        const unitTopics = {};
        for (const unit of unitNames()) {
            unitTopics[unit] = {};
            for (const memberField of Object.keys(master)) {
                unitTopics[unit][memberField] = `${station}/${unit}/${memberField}`;
            }
        }

        const first = prevMaster.current === null;
        const moved = {};
        if (!first) {
            for (const field of Object.keys(master)) {
                moved[field] = JSON.stringify(master[field]) !== prevMaster.current[field];
            }
        }

        const linked = {};
        for (const unit of Object.keys(unitTopics)) {
            const excluded = vetoTopics[unit] && isTruthy(valueAt(vetoTopics[unit]));
            linked[unit] = !excluded && isTruthy(valueAt(`${station}/${unit}/${enlistField}`));
            const justLinked = !first && prevLinked.current[unit] === false && linked[unit];
            if (!linked[unit]) continue;
            for (const field of Object.keys(unitTopics[unit])) {
                if (justLinked || moved[field]) trigger(unitTopics[unit][field], master[field]);
            }
        }

        const snapshot = {};
        for (const field of Object.keys(master)) snapshot[field] = JSON.stringify(master[field]);
        prevMaster.current = snapshot;
        prevLinked.current = Object.assign({}, prevLinked.current, linked);
    });

    return null;
};

window.LinkGang = LinkGang;
