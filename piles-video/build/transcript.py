"""Phrases of the source kept in the 60 s edit, in Hinglish (Roman script), in play order.

(name, speaker, gap_before_seconds, [(source_start, source_end, text), ...]).
Spans come from a 10 ms speech map of the source; wording was reconciled from several
independent Whisper passes (slowed audio, shifted windows, hi/mr/ur/translate variants).
"""

SECTIONS = [
    ("hook", "doctor", 0.0, [
        (39.85, 43.57, "Woh agar acche se saaf karein, to baar-baar yeh problem nahi aati hai."),
    ]),
    ("question", "young", 0.0, [
        (0.02, 4.40, "Patient ek baar treatment kara leta hai, uska piles aur fissure ka problem theek bhi ho jaata hai,"),
        (4.74, 8.36, "lekin chaar-chhe mahine baad uska problem wapas, uska recurrent hota hai. Aisa kyun?"),
    ]),
    ("answer", "doctor", 1.4, [
        (10.23, 11.15, "Haan, bahut baar,"),
        (11.46, 12.67, "aapne jo sahi observe kiya hai,"),
        (13.42, 15.32, "ki patient ek baar theek hone ke baad"),
        (16.18, 19.47, "har chaar mahine, chhe mahine baad phir se usi problem par lekar aata hai."),
        (20.16, 20.85, "Iska main kaaran hai"),
        (21.60, 22.70, "ki piles mein kya hota hai,"),
        (23.19, 25.01, "jo anus dwaar hai, … saaf…"),
    ]),
    ("routine", "doctor", 0.0, [
        (26.01, 27.25, "Jaise hum-aap subah uthte hain,"),
        (27.61, 28.50, "to hum brush karte hain,"),
        (28.96, 30.45, "daaton ke andar ka mal nikaalte hain,"),
        (31.04, 32.65, "aankhon ke andar ke chipad nikaalte hain,"),
        (33.13, 34.78, "naak saaf karte hain, kaan saaf karte hain."),
    ]),
    ("clean", "doctor", 0.0, [
        (35.40, 36.63, "Waise hi jo …"),
        (37.06, 39.12, "mootra ke, jo indriyon ke jo dwaar hain,"),
        (39.85, 43.57, "woh agar acche se saaf karein, to baar-baar yeh problem nahi aati hai."),
    ]),
    ("advice", "doctor", 0.0, [
        (44.38, 46.47, "To mujhe apne patient ko bhi yahi kehna hai"),
        (47.17, 50.50, "ki baar-baar anus ke …, ek ungli andar daal ke"),
        (51.20, 52.97, "thoda usko clean karna hamesha."),
    ]),
    ("takeaway", "doctor", 0.0, [
        (53.36, 57.00, "To baar-baar yeh … jo aane waali problem, woh nahi aayegi."),
    ]),
]

KEYWORDS = {"piles", "fissure", "problem", "recurrent", "treatment", "theek", "kaaran", "anus", "dwaar", "saaf",
            "brush", "daaton", "aankhon", "naak", "kaan", "clean", "hamesha", "baar-baar", "chaar-chhe",
            "mahine", "indriyon", "chipad"}
