# How the FORECAST interface follows NASA crew-interface standards

Source: NASA-STD-3001 Volume 2, Revision F (Human Factors, Habitability and Environmental Health),
Section 10 "Crew Interfaces" and Appendix F "Display Standard"
(https://www.nasa.gov/reference/10-0-crew-interfaces-vol-2/, https://www.nasa.gov/reference/appendix-f-vol-2/).

| NASA rule | What we changed |
| --- | --- |
| Two users, one consistent interface (V2 10005: consistent appearance, arrangement, location and operation) | Two screens by role (Astronaut, Mission Control) built from the same cards, colors and words |
| Common area for key information, visible at all times (App. F.4.2.06) | Caution & warning bar under the header, sticky while scrolling |
| Distinct alert levels for warning and caution (V2 10114); top alert shown until the crew acknowledges it (V2 10175) | Warning (red), Caution (yellow), Advisory (blue). The bar keeps showing the top alert until "Acknowledge"; after that the text stays, marked "Acknowledged" |
| Color carries meaning, not decoration; critical information needs a second cue (App. F.5.10) | One color meaning everywhere: green normal, blue advisory, yellow caution, red only for a warning (high fatigue risk on a day with a critical task). Every colored status also has an icon or a word |
| Flashing only for events that need attention (App. F.5.11) | Digital-twin dots pulse only when a signal is well off normal |
| No mental computation or transposition (App. F.4.1.5) | "D+2" became "In 2 days (day 16)"; "-6.6 SD" became "Well below normal" |
| Mixed-case text; labels next to values, same wording (App. F.5.1.8, F.5.2) | Status line reads "Mars mode · 12 min delay", "Mission day 14" instead of capitals and short codes |
| Show only what the task needs (App. F.4.1.1) | Astronaut screen: readiness today, next 3 days, NOVA in short, changes to decide. Detail lives on the Mission Control screen |
| Positive feedback that an input was registered (V2 10022: about 0.1 s feels instant, 1 s keeps the flow) | Accept / Edit / Reject show "Sending" at once, then the result, or "Not saved, try again" |
| Controls usable with gloves (V2 10157: 32 mm spacing for gloved fingers) | Buttons on the astronaut screen are at least 48 px, with a visible focus ring |

Not done yet: audio tones for alerts, testing with real crew (V2 5007 asks for a workload rating of 3 or less on the Bedford scale in a human-in-the-loop test).
