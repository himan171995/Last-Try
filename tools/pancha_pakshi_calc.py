"""Pancha Pakshi schedule from a Drik-Panchang-aligned data table.

Reads the table as plain JSON (bird -> paksha -> Day/Night -> weekday -> 5 yamams,
each with 5 sub-activities carrying a standard duration out of 144), computes
sunrise/sunset with the SunCalc algorithm (h0 = -0.833 deg), splits day and
night into 5 equal yamams, scales each sub-period to its yamam, and rounds every
boundary to the nearest minute.

usage: python3 -I calc.py <panchapakshi_data.json> <relationships.json> validate|today <out.json>
"""
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone

RAD = math.pi / 180
DAY_S = 86400
J1970 = 2440588
J2000 = 2451545
E = RAD * 23.4397
J0 = 0.0009


def to_days(dt):
    return dt.timestamp() / DAY_S - 0.5 + J1970 - J2000


def from_julian(j):
    return datetime.fromtimestamp((j + 0.5 - J1970) * DAY_S, tz=timezone.utc)


def sun_altitude(dt, lat, lng):
    """Apparent-centre altitude of the Sun in degrees (Meeus ch. 25 low-precision series)."""
    jd = dt.timestamp() / DAY_S + 2440587.5
    t = (jd + 69 / DAY_S - 2451545.0) / 36525  # TT ~ UT + 69 s
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    mr = m * RAD
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mr)
         + (0.019993 - 0.000101 * t) * math.sin(2 * mr) + 0.000289 * math.sin(3 * mr))
    omega = (125.04 - 1934.136 * t) * RAD
    lam = (l0 + c - 0.00569 - 0.00478 * math.sin(omega)) * RAD
    eps = (23 + 26 / 60 + 21.448 / 3600 - 46.8150 / 3600 * t + 0.00256 * math.cos(omega)) * RAD
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    tu = (jd - 2451545.0) / 36525
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * tu * tu - tu ** 3 / 38710000
    h = (gmst + lng) * RAD - ra
    phi = lat * RAD
    return math.asin(math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(h)) / RAD


def _cross(lat, lng, lo, hi, rising, h0=-0.833):
    for _ in range(50):
        mid = lo + (hi - lo) / 2
        above = sun_altitude(mid, lat, lng) > h0
        if above == rising:
            hi = mid
        else:
            lo = mid
    return lo + (hi - lo) / 2


def sun_times(d, lat, lng):
    """Sunrise and sunset (upper limb with standard refraction, h0 = -0.833 deg) for local date d."""
    noon = datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc) - timedelta(hours=lng / 15)
    rise = _cross(lat, lng, noon - timedelta(hours=12), noon, rising=True)
    sset = _cross(lat, lng, noon, noon + timedelta(hours=12), rising=False)
    return rise, sset


def round_min(dt):
    return datetime.fromtimestamp(round(dt.timestamp() / 60) * 60, tz=timezone.utc)


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ACT = {"Rule": "Ruling", "Eat": "Eating", "Walk": "Walking", "Sleep": "Sleeping", "Death": "Dying"}


def lordship(rel, weekday, paksha):
    out = {}
    for bird, info in rel[paksha].items():
        if weekday in info["rulingDays"]["dayTime"]:
            out["dayRuler"] = bird
        if weekday in info["rulingDays"]["nightTime"]:
            out["nightRuler"] = bird
        if weekday in info["deathDays"]:
            out["deathBird"] = bird
    return out


def schedule(table, bird, d, lat, lng, paksha):
    """Full Panchang day (sunrise to next sunrise) for one native bird.
    Assumes the paksha does not change during the day (checked by the caller)."""
    rise, sset = sun_times(d, lat, lng)
    next_rise, _ = sun_times(d + timedelta(days=1), lat, lng)
    weekday = WEEKDAYS[d.weekday()]
    yamams = []
    for half, start, end in (("Day", rise, sset), ("Night", sset, next_rise)):
        raw = table[bird][paksha][half][weekday]
        assert len(raw) == 5
        span = (end - start).total_seconds() / 5
        for i, y in enumerate(raw):
            ys = start + timedelta(seconds=i * span)
            ye = end if i == 4 else start + timedelta(seconds=(i + 1) * span)
            ylen = (ye - ys).total_seconds()
            cur = ys
            subs = []
            for j, u in enumerate(y["subActivities"]):
                ue = ye if j == len(y["subActivities"]) - 1 else cur + timedelta(seconds=u["standardDuration"] / 144 * ylen)
                subs.append({
                    "b": u["bird"], "a": ACT[u["activity"]],
                    "r": "Self" if u["relation"] == "Same" else u["relation"],
                    "ef": u["effect"], "rt": len(u["rating"]), "std": u["standardDuration"],
                    "s": round_min(cur), "e": round_min(ue),
                })
                cur = ue
            yamams.append({"p": half[0], "n": i + 1, "a": ACT[y["mainActivity"]],
                           "s": round_min(ys), "e": round_min(ye), "subs": subs})
    return {"weekday": weekday, "sunrise": round_min(rise), "sunset": round_min(sset),
            "nextSunrise": round_min(next_rise), "yamams": yamams}


def hhmm(dt, offset_h):
    return (dt + timedelta(hours=offset_h)).strftime("%H:%M")


def validate(table):
    DELHI = (28.6139, 77.2090)
    BERLIN = (52.5200, 13.4050)
    checks = 0
    fails = 0

    def check(label, got, want):
        nonlocal checks, fails
        checks += 1
        ok = got == want
        fails += 0 if ok else 1
        print(f"  {'OK ' if ok else 'BAD'} {label}: calc {got} | drik {want}")

    # Delhi, Sat 3 Oct 2026, Krishna, Cock (values from the engine README's Drik fixture)
    s = schedule(table, "Cock", date(2026, 10, 3), *DELHI, "Krishnapaksha")
    print("Delhi 3 Oct 2026, Cock")
    check("sunrise", hhmm(s["sunrise"], 5.5), "06:15")
    check("day Y1 end", hhmm(s["yamams"][0]["e"], 5.5), "08:37")
    check("night Y4", f'{hhmm(s["yamams"][8]["s"], 5.5)}-{hhmm(s["yamams"][8]["e"], 5.5)} {s["yamams"][8]["a"]}', "01:23-03:49 Dying")
    check("night Y5", f'{hhmm(s["yamams"][9]["s"], 5.5)}-{hhmm(s["yamams"][9]["e"], 5.5)} {s["yamams"][9]["a"]}', "03:49-06:15 Ruling")

    # Delhi, Sat 10 Oct 2026 (day part only; the night has a paksha switch)
    s = schedule(table, "Cock", date(2026, 10, 10), *DELHI, "Krishnapaksha")
    print("Delhi 10 Oct 2026")
    check("sunset", hhmm(s["sunset"], 5.5), "17:57")
    check("night Y2 start", hhmm(s["yamams"][6]["s"], 5.5), "20:25")

    # Delhi, Sat 4 Jul 2026, Krishna, Cock (indexed Drik page ?pakshi=cock)
    s = schedule(table, "Cock", date(2026, 7, 4), *DELHI, "Krishnapaksha")
    print("Delhi 4 Jul 2026, Cock")
    cock = [(y["a"], u) for y in s["yamams"][:5] for u in y["subs"] if u["b"] == "Cock"]
    want = ["05:28-05:49 Ruling Very Good", "08:15-08:57 Walking Average", "11:02-11:58 Eating Good"]
    for (ya, u), w in zip(cock[:3], want):
        check("Cock sub", f'{hhmm(u["s"], 5.5)}-{hhmm(u["e"], 5.5)} {u["a"]} {u["ef"]}', w)
    check("day Y4 start", hhmm(s["yamams"][3]["s"], 5.5), "13:49")

    # Berlin, Tue 13 Oct 2026, Shukla, default page bird (Peacock): Crow rows
    s = schedule(table, "Peacock", date(2026, 10, 13), *BERLIN, "Suklapaksha")
    print("Berlin 13 Oct 2026, Peacock page")
    crow = [u for y in s["yamams"][:5] for u in y["subs"] if u["b"] == "Crow"]
    want = ["08:38-09:22 Ruling Very Bad Enemy", "11:20-11:37 Sleeping Bad Enemy", "13:19-13:30 Dying Very Bad Enemy"]
    for u, w in zip(crow[:3], want):
        check("Crow sub", f'{hhmm(u["s"], 2)}-{hhmm(u["e"], 2)} {u["a"]} {u["ef"]} {u["r"]}', w)
    check("night Y3", f'{hhmm(s["yamams"][7]["s"], 2)}-{hhmm(s["yamams"][7]["e"], 2)}', "23:34-02:12")
    print(f"{checks - fails}/{checks} checks match")


def today(table, rel, out_path):
    DELHI = (28.6139, 77.2090)
    d = date(2026, 10, 14)
    paksha = "Suklapaksha"  # new moon ended 10 Oct 21:19 IST; full moon is 26 Oct
    result = {"date": d.isoformat(), "city": "New Delhi", "lat": DELHI[0], "lon": DELHI[1],
              "tzOffsetMin": 330, "paksha": "Shukla", "birds": {}}
    for bird in ["Vulture", "Owl", "Crow", "Cock", "Peacock"]:
        s = schedule(table, bird, d, *DELHI, paksha)
        result.update({"weekday": s["weekday"], "sunrise": s["sunrise"], "sunset": s["sunset"],
                       "nextSunrise": s["nextSunrise"]})
        result["birds"][bird] = s["yamams"]
    result.update(lordship(rel, result["weekday"], paksha))
    ser = lambda o: o.strftime("%Y-%m-%dT%H:%MZ") if isinstance(o, datetime) else o
    with open(out_path, "w") as f:
        json.dump(result, f, default=ser, separators=(",", ":"))
    print(result["weekday"], "sunrise", hhmm(result["sunrise"], 5.5), "sunset", hhmm(result["sunset"], 5.5),
          "next sunrise", hhmm(result["nextSunrise"], 5.5),
          "| day ruler", result["dayRuler"], "night ruler", result["nightRuler"], "dying", result["deathBird"])
    for y in result["birds"]["Peacock"]:
        print(f'{y["p"]}{y["n"]} {hhmm(y["s"], 5.5)}-{hhmm(y["e"], 5.5)} {y["a"]}')
        for u in y["subs"]:
            print(f'      {hhmm(u["s"], 5.5)}-{hhmm(u["e"], 5.5)} {u["b"]:8} {u["a"]:9} {u["r"]:6} {u["ef"]:9} {"+" * u["rt"]}')


if __name__ == "__main__":
    table = json.load(open(sys.argv[1]))
    rel = json.load(open(sys.argv[2]))
    if sys.argv[3] == "validate":
        validate(table)
    else:
        today(table, rel, sys.argv[4])
