// DynamicsPresets Component
// Custom dropdown to publish multiple parameters to MQTT simultaneously.

window.DynamicsPresets = ({ config }) => {
    const handlePresetChange = (e) => {
        const presetStr = e.target.value;
        if (!presetStr) return;
        
        const publishFn = window.useMqttPublish ? window.useMqttPublish() : null;
        if (!publishFn) {
            console.error("DynamicsPresets: useMqttPublish not available in environment");
            return;
        }

        try {
            const preset = JSON.parse(presetStr);
            if (preset.Ratio !== undefined) {
                publishFn("OpenAir/Gui/Dyn_Params/Ratio", preset.Ratio);
            }
            if (preset.Attack !== undefined) {
                publishFn("OpenAir/Gui/Dyn_Params/Attack", preset.Attack);
            }
            if (preset.Release !== undefined) {
                publishFn("OpenAir/Gui/Dyn_Params/Release", preset.Release);
            }
        } catch (err) {
            console.error("DynamicsPresets: Error parsing preset JSON", err);
        }
        
        // Reset the dropdown back to "Select Preset..."
        e.target.value = "";
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%', padding: '10px 0' }}>
            <span style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>Starting Points</span>
            <select 
                onChange={handlePresetChange}
                defaultValue=""
                style={{
                    backgroundColor: '#1a1a1a',
                    color: '#dcdcdc',
                    border: '1px solid #444',
                    padding: '8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    outline: 'none',
                    width: '100%',
                    minWidth: '250px'
                }}
            >
                <option value="">Select Preset...</option>
                <optgroup label="1. Kicks and Snares">
                    <option value='{"Ratio": 4.0, "Attack": 15.0, "Release": 50.0}'>Kick: Tight Rock [4:1, 15 ms, 50 ms]</option>
                    <option value='{"Ratio": 8.0, "Attack": 5.0, "Release": 30.0}'>Kick: Metal Click (Aggressive) [8:1, 5 ms, 30 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 200.0}'>Kick: Hip-Hop 808 Sub [2:1, 30 ms, 200 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 25.0, "Release": 100.0}'>Kick: Jazz Feathering [2:1, 25 ms, 100 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 40.0}'>Kick: Electronic EDM Punch [4:1, 10 ms, 40 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 20.0, "Release": 80.0}'>Kick: Vintage 70s Thud [3:1, 20 ms, 80 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 30.0, "Release": 20.0}'>Kick: Beater Snap Enhancement [6:1, 30 ms, 20 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 5.0, "Release": 150.0}'>Kick: Boomy Room Control [4:1, 5 ms, 150 ms]</option>
                    <option value='{"Ratio": 10.0, "Attack": 1.0, "Release": 20.0}'>Kick: Parallel Crush (Blend in) [10:1, 1 ms, 20 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 25.0}'>Kick: Fast Double-Bass [4:1, 10 ms, 25 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 15.0, "Release": 120.0}'>Snare: Hard Rock Crack [6:1, 15 ms, 120 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 20.0, "Release": 250.0}'>Snare: Fat Ballad Splat [4:1, 20 ms, 250 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 60.0}'>Snare: Piccolo Snap [4:1, 10 ms, 60 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 5.0, "Release": 50.0}'>Snare: Bottom Mic (Wire Sizzle) [4:1, 5 ms, 50 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 10.0, "Release": 80.0}'>Snare: Jazz Brush Consistency [2:1, 10 ms, 80 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 15.0, "Release": 100.0}'>Snare: Marching Band Roll [3:1, 15 ms, 100 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 5.0, "Release": 40.0}'>Snare: Electronic Clap [4:1, 5 ms, 40 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 10.0, "Release": 60.0}'>Snare: R&B Rim Click [3:1, 10 ms, 60 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 25.0, "Release": 100.0}'>Snare: Vintage Motown [3:1, 25 ms, 100 ms]</option>
                    <option value='{"Ratio": 20.0, "Attack": 1.0, "Release": 50.0}'>Snare: Parallel Smash (Blend in) [20:1, 1 ms, 50 ms]</option>
                </optgroup>
                <optgroup label="2. Toms, Cymbals, and Percussion">
                    <option value='{"Ratio": 4.0, "Attack": 15.0, "Release": 150.0}'>Rack Tom: Punch [4:1, 15 ms, 150 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 20.0, "Release": 250.0}'>Floor Tom: Boom Control [4:1, 20 ms, 250 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 10.0, "Release": 100.0}'>Tom: Metal Attack [6:1, 10 ms, 100 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 25.0, "Release": 200.0}'>Tom: Jazz Melodic [2:1, 25 ms, 200 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 15.0, "Release": 120.0}'>Tom: Tribal Percussion [3:1, 15 ms, 120 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 10.0, "Release": 300.0}'>Overheads: Smooth Cymbal Wash [2:1, 10 ms, 300 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 5.0, "Release": 50.0}'>Overheads: Aggressive Pumping [4:1, 5 ms, 50 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 1.0, "Release": 100.0}'>Overheads: Tape Saturation Style [3:1, 1 ms, 100 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 1.0, "Release": 20.0}'>Hi-Hat: Tame Harsh Peaks [4:1, 1 ms, 20 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 5.0, "Release": 80.0}'>Ride Cymbal: Ping Control [3:1, 5 ms, 80 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 15.0, "Release": 400.0}'>Crash: Sustain Lengthening [3:1, 15 ms, 400 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 10.0, "Release": 150.0}'>Room Mic: Natural Glue [2:1, 10 ms, 150 ms]</option>
                    <option value='{"Ratio": 20.0, "Attack": 1.0, "Release": 50.0}'>Room Mic: All-Buttons Smash [20:1, 1 ms, 50 ms]</option>
                    <option value='{"Ratio": 8.0, "Attack": 5.0, "Release": 100.0}'>Room Mic: Mono Dirt [8:1, 5 ms, 100 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 20.0, "Release": 300.0}'>Room Mic: Distant Ambience [4:1, 20 ms, 300 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 5.0, "Release": 30.0}'>Perc: Tambourine Leveling [4:1, 5 ms, 30 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 10.0, "Release": 50.0}'>Perc: Shaker Groove [3:1, 10 ms, 50 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 15.0, "Release": 100.0}'>Perc: Conga Slap [4:1, 15 ms, 100 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 10.0, "Release": 80.0}'>Perc: Bongo Tone [3:1, 10 ms, 80 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 5.0, "Release": 50.0}'>Perc: Cowbell Tame [4:1, 5 ms, 50 ms]</option>
                </optgroup>
                <optgroup label="3. Bass Instruments">
                    <option value='{"Ratio": 4.0, "Attack": 20.0, "Release": 100.0}'>Bass: Heavy Rock Picked [4:1, 20 ms, 100 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 30.0, "Release": 150.0}'>Bass: R&B Fingered [3:1, 30 ms, 150 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 5.0, "Release": 50.0}'>Bass: Slap (Tame the Pops) [6:1, 5 ms, 50 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 15.0, "Release": 100.0}'>Bass: Slap (Thick Thumb) [4:1, 15 ms, 100 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 40.0, "Release": 200.0}'>Bass: Upright Jazz (Transparent) [2:1, 40 ms, 200 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 50.0}'>Bass: Synth Pluck (EDM) [4:1, 10 ms, 50 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 50.0, "Release": 300.0}'>Bass: Sub Glue [2:1, 50 ms, 300 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 20.0, "Release": 150.0}'>Bass: Vintage Motown Tube [3:1, 20 ms, 150 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 80.0}'>Bass: Distorted Metal [4:1, 10 ms, 80 ms]</option>
                    <option value='{"Ratio": 10.0, "Attack": 1.0, "Release": 50.0}'>Bass: Parallel Fuzz (Blend in) [10:1, 1 ms, 50 ms]</option>
                </optgroup>
                <optgroup label="4. Vocals and Spoken Word">
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 80.0}'>Vocal: Modern Pop Lead [4:1, 10 ms, 80 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 5.0, "Release": 50.0}'>Vocal: Aggressive Rock [6:1, 5 ms, 50 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 5.0, "Release": 30.0}'>Vocal: Fast Rap / Hip-Hop [4:1, 5 ms, 30 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 10.0, "Release": 100.0}'>Vocal: Spoken Word / Podcast [3:1, 10 ms, 100 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 20.0, "Release": 150.0}'>Vocal: Intimate Whisper [2:1, 20 ms, 150 ms]</option>
                    <option value='{"Ratio": 8.0, "Attack": 2.0, "Release": 40.0}'>Vocal: Screaming Metal [8:1, 2 ms, 40 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 15.0, "Release": 100.0}'>Vocal: Gang Backgrounds [4:1, 15 ms, 100 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 200.0}'>Vocal: Choir Leveling [2:1, 30 ms, 200 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 25.0, "Release": 150.0}'>Vocal: Smooth R&B [3:1, 25 ms, 150 ms]</option>
                    <option value='{"Ratio": 10.0, "Attack": 1.0, "Release": 100.0}'>Vocal: Live PA Feedback Control [10:1, 1 ms, 100 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 1.0, "Release": 20.0}'>Vocal: De-Essing (High-Band only) [6:1, 1 ms, 20 ms]</option>
                    <option value='{"Ratio": 10.0, "Attack": 1.0, "Release": 50.0}'>Vocal: Parallel NY Style [10:1, 1 ms, 50 ms]</option>
                </optgroup>
                <optgroup label="5. Guitars">
                    <option value='{"Ratio": 4.0, "Attack": 15.0, "Release": 150.0}'>Acoustic: Pop Strumming [4:1, 15 ms, 150 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 20.0, "Release": 200.0}'>Acoustic: Delicate Fingerpicking [2:1, 20 ms, 200 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 10.0, "Release": 100.0}'>Acoustic: Bluegrass Flatpick [3:1, 10 ms, 100 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 15.0, "Release": 120.0}'>Acoustic: 12-String Chime [3:1, 15 ms, 120 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 80.0}'>Acoustic: Rhythm Chunk [4:1, 10 ms, 80 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 10.0, "Release": 50.0}'>Electric: Clean Funk Strum [6:1, 10 ms, 50 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 20.0, "Release": 150.0}'>Electric: Clean Jazz Lead [3:1, 20 ms, 150 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 25.0, "Release": 100.0}'>Electric: Crunchy Rhythm [2:1, 25 ms, 100 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 15.0, "Release": 150.0}'>Electric: High-Gain Lead [3:1, 15 ms, 150 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 200.0}'>Electric: Blues Dynamic [2:1, 30 ms, 200 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 5.0, "Release": 40.0}'>Electric: Country Chicken-Pickin' [6:1, 5 ms, 40 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 300.0}'>Electric: Slide Sustain [4:1, 10 ms, 300 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 50.0, "Release": 400.0}'>Electric: Ambient Swells [2:1, 50 ms, 400 ms]</option>
                </optgroup>
                <optgroup label="6. Keys, Synths, and Orchestral">
                    <option value='{"Ratio": 4.0, "Attack": 15.0, "Release": 100.0}'>Piano: Bright Pop Grand [4:1, 15 ms, 100 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 200.0}'>Piano: Dark Upright [2:1, 30 ms, 200 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 20.0, "Release": 150.0}'>Keys: Rhodes Bark [3:1, 20 ms, 150 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 25.0, "Release": 150.0}'>Keys: Wurlitzer Smooth [2:1, 25 ms, 150 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 10.0, "Release": 50.0}'>Keys: Clavinet Funk [4:1, 10 ms, 50 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 10.0, "Release": 200.0}'>Keys: Hammond Organ Sustain [2:1, 10 ms, 200 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 15.0, "Release": 50.0}'>Synth: Arpeggiator Pluck [4:1, 15 ms, 50 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 50.0, "Release": 300.0}'>Synth: Pad Glue [2:1, 50 ms, 300 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 20.0, "Release": 100.0}'>Synth: Moog Bass Lead [3:1, 20 ms, 100 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 200.0}'>Synth: Mellotron Tame [2:1, 30 ms, 200 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 15.0, "Release": 150.0}'>Orchestral: Solo Trumpet [3:1, 15 ms, 150 ms]</option>
                    <option value='{"Ratio": 3.0, "Attack": 20.0, "Release": 200.0}'>Orchestral: Smooth Saxophone [3:1, 20 ms, 200 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 25.0, "Release": 100.0}'>Orchestral: Brass Section Punch [4:1, 25 ms, 100 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 250.0}'>Orchestral: Solo Violin [2:1, 30 ms, 250 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 40.0, "Release": 300.0}'>Orchestral: String Section Glue [2:1, 40 ms, 300 ms]</option>
                </optgroup>
                <optgroup label="7. Busses and Mastering">
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 100.0}'>Bus: Drum Submix Glue [2:1, 30 ms, 100 ms]</option>
                    <option value='{"Ratio": 6.0, "Attack": 10.0, "Release": 50.0}'>Bus: Drum Submix Smash [6:1, 10 ms, 50 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 25.0, "Release": 150.0}'>Bus: Vocal Group Levelling [2:1, 25 ms, 150 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 100.0}'>Bus: Guitars Wall of Sound [2:1, 30 ms, 100 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 20.0, "Release": 200.0}'>Bus: Keys Submix [2:1, 20 ms, 200 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 30.0, "Release": 150.0}'>Master: Pop Track Punch [2:1, 30 ms, Auto / 150 ms]</option>
                    <option value='{"Ratio": 1.5, "Attack": 50.0, "Release": 300.0}'>Master: Gentle Classical [1.5:1, 50 ms, 300 ms]</option>
                    <option value='{"Ratio": 2.0, "Attack": 15.0, "Release": 100.0}'>Master: Rock Density [2:1, 15 ms, 100 ms]</option>
                    <option value='{"Ratio": 10.0, "Attack": 1.0, "Release": 50.0}'>Master: Broadcast Ceiling [10:1, 1 ms, 50 ms]</option>
                    <option value='{"Ratio": 4.0, "Attack": 5.0, "Release": 100.0}'>Master: Parallel Overall Mix [4:1, 5 ms, 100 ms]</option>
                </optgroup>
            </select>
        </div>
    );
};
