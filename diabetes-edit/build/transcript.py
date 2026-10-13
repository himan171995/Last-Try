"""Selected phrases of source.mp4 for the 60 s cut, in Hinglish (Roman script).

Each entry: (source_start, source_end, text). Times are the voiced span of the phrase
(10 ms energy VAD, see phrases.py). Sections play in this order; everything not listed
is cut. Wording was checked against several Whisper passes over each span.
"""

SECTIONS = [
    ("question", "patient", [
        (3.06, 5.56, "Sir, apne paas aane waale 10 patients mein se"),
        (5.99, 7.87, "6 se 7-8 patients diabetic rehte hain."),
        (8.47, 9.99, "Aajkal apne desh mein diabetes"),
        (10.24, 12.11, "ke patients itne kyun badh rahe hain? Sir, kya kaaran hai?"),
    ]),
    ("charaka", "doctor", [
        (18.91, 19.83, "Charakacharya ji ne"),
        (20.46, 21.53, "kisko diabetes hota hai,"),
        (21.86, 22.93, "kisko madhumeh hota hai,"),
        (23.59, 24.34, "yeh bataya hua hai."),
    ]),
    ("stress", "doctor", [
        (77.41, 79.27, "Woh chinta mein apna vyapaar karta hai,"),
        (79.62, 81.01, "aur woh vyapaar karte samay"),
        (81.46, 82.30, "uska jo stress hai,"),
        (83.04, 84.02, "To iska yeh matlab hai"),
        (84.48, 85.26, "ki stress hi"),
        (85.63, 86.38, "diabetes ka ek"),
        (87.26, 88.70, "mahatvapurna kaaran, cause hai."),
    ]),
    ("dairy", "doctor", [
        (102.19, 103.84, "Jo gaay se utpann"),
        (104.32, 105.13, "doodh,"),
        (105.46, 105.85, "dahi,"),
        (106.22, 106.50, "ghee,"),
        (106.85, 108.79, "iska jo zyada prayog karta hai,"),
        (109.21, 110.98, "use bhi diabetes hota hai."),
    ]),
    ("grain", "doctor", [
        (140.68, 142.27, "Iska matlab naye chaawal ka use"),
        (142.54, 145.02, "nahi karna chahiye, naye anaaj ka use nahi karna chahiye,"),
        (145.50, 146.43, "kyunki uske kaaran"),
        (146.97, 147.99, "kaph-kaarak hota hai."),
        (148.36, 149.00, "Kaph badhta,"),
        (149.40, 150.65, "to kaph ke kaaran hi"),
        (151.35, 152.15, "diabetes hota hai."),
    ]),
    ("sweets", "doctor", [
        (159.81, 160.90, "Jo zyada meetha khaata hai,"),
        (162.07, 163.68, "jaise ganne se banayi cheez,"),
        (164.48, 165.10, "shakkar ho gaya,"),
        (165.42, 166.09, "gud ho gaya,"),
        (166.44, 168.22, "aur inse banayi meethi cheezein"),
        (168.57, 169.91, "jo baar-baar khaata hai."),
    ]),
    ("conclusion", "doctor", [
        (202.95, 204.42, "Iska matlab sabhi log sukhi hain,"),
        (205.00, 205.70, "sabhi stress mein hain,"),
        (206.35, 207.40, "yahi ek kaaran maana ja sakta hai."),
    ]),
]

# Words drawn in the accent colour.
KEYWORDS = {
    "diabetes", "diabetic", "madhumeh", "charakacharya", "chinta", "stress", "mahatvapurna",
    "kaaran", "doodh", "dahi", "ghee", "zyada", "chaawal", "anaaj", "kaph", "meetha", "shakkar",
    "gud", "baar-baar", "sukhi", "kaph-kaarak", "7-8", "10", "6",
}
