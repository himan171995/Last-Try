"""Hinglish transcript of source.mp4, anchored to source-time speech spans.

Each entry is (source_start, source_end, text). Word timings inside a span are
distributed over the voiced audio in build/voiced.json (see edl.py).
"""

SENTENCES = [
    (0.09, 2.67, "Sir, aajkal yeh jo piles aur fissure ki problem hai,"),
    (3.08, 4.06, "aajkal kyun badh rahi hai?"),
    (7.09, 8.02, "Aapne sahi poocha hai."),
    (8.64, 12.44, "Aaye din apne paas bahut saare piles ke patients aa rahe hain."),
    (13.12, 14.75, "Iska mukhya kaaran hai khaan-paan."),
    (16.81, 19.73, "Raat ko late sona, yeh to aajkal aam baat ho gayi hai."),
    (20.67, 21.29, "Masaledaar,"),
    (21.66, 22.27, "tez khaana,"),
    (22.81, 23.09, "teekha,"),
    (23.58, 23.87, "mirchi,"),
    (24.32, 24.86, "tala hua khaana."),
    (25.81, 27.99, "Aise khaane ki aadat pad jaati hai,"),
    (28.65, 34.01, "aur baar-baar aisa khaane se poori anna-nalika garam ho jaati hai."),
    (34.88, 38.51, "To us ushnata ke kaaran jo stool hai, woh hard ho jaata hai."),
    (39.17, 42.01, "Aur jab nikalta hai, to wahan garmi ke kaaran"),
    (42.60, 44.99, "piles jaise tayyar ho jaate hain."),
    (46.89, 50.95, "Us piles ke kaaran wahan pain hota hai."),
    (51.54, 54.63, "Subah-subah uthte hi jab stool pass karte hain,"),
    (55.48, 58.08, "us waqt anus ke dwaar mein dard hota hai,"),
    (58.97, 60.72, "aur pain badhta hai."),
    (61.29, 67.25, "Aksar paaya gaya hai ki patient sharm ki wajah se der karte hain."),
    (68.11, 75.23, "Jab piles complication create karta hai, tabhi woh doctor ke paas aate hain."),
    (76.26, 77.08, "Aapko samajhna chahiye"),
    (78.04, 83.77, "ki shuruaat mein agar khaan-paan ka parhez achhe se kiya jaaye,"),
    (84.00, 86.30, "aur aahaar-vihaar ka parhez rakha jaaye, to piles"),
    (86.89, 87.63, "kam ho sakte hain."),
    (88.11, 90.00, "Shuruaat mein hi woh durust ho sakte hain."),
]

# Words drawn in the accent colour when they are not the active word.
KEYWORDS = {
    "piles", "fissure", "khaan-paan", "late", "masaledaar", "tez", "teekha", "mirchi",
    "tala", "garam", "ushnata", "hard", "garmi", "pain", "dard", "sharm", "complication",
    "doctor", "parhez", "aahaar-vihaar", "durust", "anna-nalika", "stool",
}
