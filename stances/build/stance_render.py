"""Geometry + SVG drawing for the stance cards (figure, footprint, weight bar)."""
import math

THIGH, SHIN, FOOT = 45.0, 42.0, 26.0
ANK = 8.0            # ankle height
NAVY, GOLD, INK = "#004a87", "#FDBF17", "#1b2a3a"
SKIN, GI, GI_BACK = "#f1c9a0", "#ffffff", "#dfe6ee"

def fmt(v): return f"{v:.1f}"

# ---------- basic geometry (y up, centimetres) ----------
def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])

def ik(hip, ank, side=+1, thigh=THIGH, shin=SHIN):
    """Knee position for a two-bone leg. side=+1 puts the knee on +x of the hip-ankle line (forward)."""
    d = dist(hip, ank)
    d = min(d, thigh + shin - 0.05)
    a = (thigh**2 - shin**2 + d*d) / (2*d)
    h = math.sqrt(max(thigh**2 - a*a, 0))
    ux, uy = (ank[0]-hip[0])/d, (ank[1]-hip[1])/d
    mx, my = hip[0] + a*ux, hip[1] + a*uy
    nx, ny = -uy, ux
    if nx*side < 0: nx, ny = -nx, -ny
    return (mx + h*nx, my + h*ny)

def circle_hip(c1, r1, c2, r2, upper=True):
    d = dist(c1, c2)
    a = (r1*r1 - r2*r2 + d*d) / (2*d)
    h = math.sqrt(max(r1*r1 - a*a, 0))
    ux, uy = (c2[0]-c1[0])/d, (c2[1]-c1[1])/d
    mx, my = c1[0]+a*ux, c1[1]+a*uy
    p1 = (mx - h*uy, my + h*ux); p2 = (mx + h*uy, my - h*ux)
    return max((p1, p2), key=lambda p: p[1]) if upper else min((p1, p2), key=lambda p: p[1])

# ---------- SVG helpers (convert y-up to svg y-down) ----------
def P(p): return f"{fmt(p[0])},{fmt(-p[1])}"
def limb(pts, w, fill=GI, edge=NAVY, ew=1.6):
    d = "M" + " L".join(P(p) for p in pts)
    return (f'<path d="{d}" fill="none" stroke="{edge}" stroke-width="{fmt(w+2*ew)}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{fmt(w)}" stroke-linecap="round" stroke-linejoin="round"/>')
def poly(pts, fill, stroke=NAVY, sw=1.2):
    return f'<polygon points="{" ".join(P(p) for p in pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
def line(a, b, stroke, sw=1.0, dash=None):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{fmt(a[0])}" y1="{fmt(-a[1])}" x2="{fmt(b[0])}" y2="{fmt(-b[1])}" stroke="{stroke}" stroke-width="{sw}"{ds} stroke-linecap="round"/>'
def text(p, s, size=6, fill=INK, anchor="start", weight=600):
    return (f'<text x="{fmt(p[0])}" y="{fmt(-p[1])}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-family="Source Sans Pro,Source Sans 3,sans-serif" font-weight="{weight}">{s}</text>')
def circle(p, r, fill, stroke=NAVY, sw=1.4):
    return f'<circle cx="{fmt(p[0])}" cy="{fmt(-p[1])}" r="{fmt(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

# ---------- feet in side view ----------
def foot_side(ank, ang, kind="flat", ball=None, back=False):
    c = abs(math.cos(math.radians(ang)))
    col = "#e5b98a" if back else SKIN
    if kind == "ball":              # heel raised, ball on floor
        B = ball
        phi = 40
        A = (B[0]-13*math.cos(math.radians(phi)), B[1]+13*math.sin(math.radians(phi)))
        heel = (B[0]-19*math.cos(math.radians(phi)), B[1]+19*math.sin(math.radians(phi)))
        toe = (B[0]+7, 0)
        return A, poly([(B[0],0),(toe[0],0),(toe[0]-1,2.2),(B[0]+1,5),(A[0]+1,A[1]+1),(heel[0]-1,heel[1]+1),(heel[0]-1.5,heel[1]-3)], col)
    hx = ank[0] - max(6*c, 4.5); tx = ank[0] + max(20*c, 4.5)
    pts = [(hx,0),(tx,0),(tx-3*c-1,3.2),(ank[0]+5*c+1,ank[1]-0.5),(ank[0]-2.5,ank[1]+2),(hx,5)]
    return ank, poly(pts, col)

def foot_nb(B, phi):
    c, sn = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    A = (B[0]-13*c, 13*sn); heel = (B[0]-19*c, 19*sn)
    return poly([(B[0]-1,0),(B[0]+8,0),(B[0]+7,2.5),(B[0]+2,5),(A[0]+2,A[1]+1),(heel[0]-1,heel[1]+1),(heel[0]-2,heel[1]-3)], "#e5b98a")

# ---------- figure pieces ----------
def head_torso(H, S, lean_head=0):
    parts = []
    parts.append(limb([H, S], 19))
    belt_c = (H[0]+(S[0]-H[0])*0.12, H[1]+(S[1]-H[1])*0.12+3)
    # belt as a short thick band across the torso
    parts.append(f'<rect x="{fmt(belt_c[0]-11)}" y="{fmt(-belt_c[1]-2.2)}" width="22" height="4.4" rx="1.4" fill="#151515"/>')
    N = (S[0]+ (S[0]-H[0])*0.14, S[1] + 5)
    head = (N[0]+lean_head, N[1] + 9.5)
    parts.append(limb([S, N], 7, fill=SKIN))
    parts.append(circle(head, 10.5, SKIN))
    return "".join(parts), head

def draw_leg_side(hip, knee, ank, ang, back=False, kind="flat", ball=None):
    col = GI_BACK if back else GI
    A, f = foot_side(ank, ang, kind, ball, back)
    return f + limb([hip, knee, A], 11, fill=col)

def arms_side(H, S, pose):
    out_back = out_front = ""
    if pose == "sides":
        el = (S[0]-1, S[1]-28); hd = (S[0]+1, S[1]-54)
        out_front = limb([S, el, hd], 6.2) + circle(hd, 4.2, SKIN)
        out_back = limb([S, (el[0]-5, el[1]), (hd[0]-5, hd[1])], 7.5, fill=GI_BACK)+circle((hd[0]-5,hd[1]),4.2,"#e5b98a")
    else:  # hikite: fists at hips
        el = (S[0]-14, S[1]-25); fist = (H[0]+9, H[1]+13)
        out_front = limb([S, el, fist], 6.2) + circle(fist, 4.6, SKIN)
        el2 = (S[0]-18, S[1]-22); fist2 = (H[0]+4, H[1]+12)
        out_back = limb([S, el2, fist2], 7.5, fill=GI_BACK) + circle(fist2, 4.6, "#e5b98a")
    return out_back, out_front

def ground(x0, x1):
    return (f'<rect x="{fmt(x0)}" y="0" width="{fmt(x1-x0)}" height="5" fill="#e8edf3"/>'
            + line((x0,0),(x1,0),NAVY,1.4))

def torso_points(hip, lean):
    S = (hip[0]+lean, hip[1]+56)
    return S

# ---------- the side-view figures ----------
def figure_side(st):
    kind = st["kind"]
    feet = {f.get("role"): f for f in st["feet"]}
    ann = []
    back_parts, front_parts = [], []
    lean = 0
    ank = lambda f: (f["heel"][1] + 6*abs(math.cos(math.radians(f["ang"]))), ANK)
    if kind in ("zenkutsu", "hanzen"):
        r, f = feet["rear"], feet["front"]
        Ar, Af = ank(r), ank(f)
        toe_x = Af[0] + 20
        K = (toe_x - (3 if kind=="zenkutsu" else 2), 0)
        dx = K[0]-Af[0]; K = (K[0], Af[1] + math.sqrt(SHIN**2 - dx**2))
        legrear = THIGH + SHIN - 0.3
        hip = circle_hip(K, THIGH, Ar, legrear, True)
        H, lean = hip, 3
        kr = ik(H, Ar, +1); kf = K
        back_parts.append(draw_leg_side(H, kr, Ar, r["ang"], back=True))
        front_parts.append(draw_leg_side(H, kf, Af, f["ang"]))
        ann.append(line((K[0], K[1]), (K[0], 0), "#c0392b", 0.9, "2 2"))
        ann.append(text((K[0]+2, K[1]-14), "knee over toes", 5.2, "#c0392b"))
        ann.append(text((Ar[0]-16, 40), "back leg straight", 5.2, "#c0392b") if kind=="zenkutsu" else "")
        x0, x1 = -25, Af[0]+40
    elif kind == "kokutsu":
        r, f = feet["rear"], feet["front"]
        Ar, Af = ank(r), ank(f)
        H = (Af[0]*0.2, 0); H = (H[0], ANK + math.sqrt((0.95*(THIGH+SHIN))**2 - (Af[0]-H[0])**2))
        lean = 4
        kr = ik(H, Ar, +1); kf = ik(H, Af, +1)
        back_parts.append(draw_leg_side(H, kf, Af, f["ang"], back=True))
        front_parts.append(draw_leg_side(H, kr, Ar, r["ang"]))
        ann.append(text((Af[0]-2, 46), "front leg straighter", 5.2, "#c0392b", "middle"))
        x0, x1 = -30, Af[0]+40
    elif kind == "neko":
        r, f = feet["rear"], feet["front"]
        Ar = ank(r); Bx = f["heel"][1] + 19
        B = (Bx, 0)
        phi = 68
        A = (B[0]-13*math.cos(math.radians(phi)), B[1]+13*math.sin(math.radians(phi)))
        Kf = (A[0]-7, A[1]+math.sqrt(SHIN**2-49))
        hx = Ar[0]+10
        H = (hx, Kf[1]+math.sqrt(THIGH**2-(Kf[0]-hx)**2))
        kr = ik(H, Ar, +1)
        lean = 2
        back_parts.append(foot_nb(B, phi) + limb([H, Kf, A], 11, fill=GI_BACK))
        front_parts.append(draw_leg_side(H, kr, Ar, r["ang"]))
        ann.append(line((Kf[0], Kf[1]), (Kf[0], 0), "#c0392b", .9, "2 2"))
        ann.append(text((Kf[0]+3, Kf[1]-16), "knee, shin and foot in line", 5.0, "#c0392b"))
        ann.append(text((B[0]+9, 6), "heel up", 5.2, "#c0392b"))
        x0, x1 = -25, B[0]+45
    elif kind == "kosa_old":
        f, r = feet["front"], feet["rear"]
        Af = ank(f); Bx = r["heel"][1] + 19; B = (Bx, 0)
        Ar, _ = foot_side(None, 0, "ball", B)
        H = (Af[0]-12, 70)
        kf = ik(H, Af, +1); kr = ik(H, Ar, +1)
        lean = 0
        back_parts.append(draw_leg_side(H, kr, Ar, 0, back=True, kind="ball", ball=B))
        front_parts.append(draw_leg_side(H, kf, Af, f["ang"]))
        ann.append(text((kr[0]-6, kr[1]-1), "back knee behind", 5.2, "#c0392b", "end"))
        x0, x1 = -20, Af[0]+40
    elif kind in ("renoji", "tenoji"):
        return figure_hanmi(st)
    elif kind == "sagi":
        s = feet["stand"]
        As = (s["heel"][1] + 6*abs(math.cos(math.radians(s["ang"]))), ANK)
        H = (As[0]+3, 89)
        ks = ik(H, As, +1)
        ft = (ks[0]+3, ks[1]+1)       # raised foot touches the standing knee
        kr = ik(H, ft, +1)
        lean = 0
        # raised leg (back, drawn first)
        back_parts.append(limb([H, kr, ft], 11, fill=GI_BACK) + poly([(ft[0]-2,ft[1]+3),(ft[0]+6,ft[1]-1),(ft[0]+8,ft[1]-6),(ft[0]-3,ft[1]-3)], "#e5b98a"))
        front_parts.append(draw_leg_side(H, ks, As, s["ang"]))
        ann.append(text((ft[0]+6, ft[1]-12), "foot at the knee", 5.2, "#c0392b"))
        x0, x1 = -35, kr[0]+45
    S = (H[0]+lean, H[1]+56)
    ob, of = arms_side(H, S, st["pose"])
    body, head = head_torso(H, S)
    gnd = ground(x0, x1)
    top = head[1] + 14
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(x0)} {fmt(-top)} {fmt(x1-x0)} {fmt(top+6)}" '
           f'preserveAspectRatio="xMidYMax meet" class="fig">'
           f'{gnd}{"".join(back_parts)}{ob}{body}{"".join(front_parts)}{of}{"".join(ann)}</svg>')
    return svg

# ---------- front-view figures ----------
def torso_front(hy, S_y, hw=13, sw=19):
    d = (f"M{-sw},{fmt(-S_y)} L{sw},{fmt(-S_y)} L{hw+3},{fmt(-(hy+30))} L{hw},{fmt(-hy)} L{-hw},{fmt(-hy)} L{-hw-3},{fmt(-(hy+30))} Z")
    return (f'<path d="{d}" fill="{GI}" stroke="{NAVY}" stroke-width="1.6" stroke-linejoin="round"/>'
            f'<path d="M{-5},{fmt(-S_y)} L0,{fmt(-(S_y-12))} L5,{fmt(-S_y)}" fill="none" stroke="{NAVY}" stroke-width="1.2"/>'
            f'<rect x="{-hw-1}" y="{fmt(-(hy+7)-2.2)}" width="{2*hw+2}" height="4.4" rx="1.4" fill="#151515"/>')

def arms_front(S_y, hy, pose):
    sx = 19
    if pose == "sides":
        return "".join(limb([(sg*sx, S_y-2), (sg*24, S_y-27), (sg*23, S_y-52)], 6.2) + circle((sg*23, S_y-52), 4.0, SKIN) for sg in (-1, 1))
    if pose == "fists_front":
        return "".join(limb([(sg*sx, S_y-2), (sg*25, S_y-25), (sg*9, S_y-44)], 6.2) + circle((sg*9, S_y-44), 4.4, SKIN) for sg in (-1, 1))
    return "".join(limb([(sg*sx, S_y-2), (sg*28, S_y-24), (sg*14, hy+9)], 6.2) + circle((sg*14, hy+9), 4.4, SKIN) for sg in (-1, 1))

def figure_hanmi(st):
    """Re no ji / Ten no ji: chest toward the viewer, feet spread along the screen's x axis."""
    kind = st["kind"]
    feet = {f.get("role"): f for f in st["feet"]}
    r, f = feet["rear"], feet["front"]
    xr = 0.0; xf = f["heel"][1] - r["heel"][1] + 6          # ankle x of front foot
    w_rear = 0.7 if kind == "renoji" else 0.5
    cx = xr*w_rear + xf*(1-w_rear)
    hy = 88
    HL, HR = (cx-8, hy), (cx+8, hy)
    kL = ik(HL, (xr, ANK), +1, ); kR = ik(HR, (xf, ANK), +1)
    kL = (kL[0]-2, kL[1]); kR = (kR[0]+2, kR[1])
    # rear foot points toward the viewer (small oval); front foot points across the picture
    rear_foot = f'<ellipse cx="{fmt(xr)}" cy="-3.4" rx="5.8" ry="3.6" fill="{SKIN}" stroke="{NAVY}" stroke-width="1.2"/>'
    A, ff = foot_side((xf, ANK), 0, "flat")
    legs = limb([HL, kL, (xr, ANK)], 11) + limb([HR, kR, (xf, ANK)], 11)
    S_y = hy + 56
    ann = []
    ann.append(text((xr-9, 12), "back foot turned out", 5.0, "#c0392b", "end"))
    ann.append(text((xf+22, 30), "front foot forward", 5.0, "#c0392b", "start"))
    x0, x1 = xr-52, xf+60
    top = S_y + 30
    g = (f'<g transform="translate({fmt(cx)},0)">' + torso_front(hy, S_y) + neck_head(S_y) + arms_front(S_y, hy, st["pose"]) + "</g>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(x0)} {fmt(-top)} {fmt(x1-x0)} {fmt(top+6)}" preserveAspectRatio="xMidYMax meet" class="fig">'
            f'{ground(x0, x1)}{rear_foot}{ff}{legs}{g}{"".join(ann)}</svg>')

def neck_head(S_y):
    return limb([(0, S_y), (0, S_y+6)], 7, fill=SKIN) + circle((0, S_y+15.5), 10.5, SKIN)

def foot_front(x, ang, back=False):
    s = abs(math.sin(math.radians(ang)))
    rx = 5.5 + 13*s
    off = 7*s*(1 if ang >= 0 else -1)
    return f'<ellipse cx="{fmt(x+off)}" cy="-3.2" rx="{fmt(rx)}" ry="3.6" fill="{SKIN}" stroke="{NAVY}" stroke-width="1.2"/>'

def figure_front(st):
    kind = st.get("kind", "stand")
    L, R = st["feet"]
    def ank_x(f):
        sgn = 1
        return f["heel"][0] + 6*math.sin(math.radians(f["ang"]))
    aL, aR = ank_x(L), ank_x(R)
    hipx = 8.0
    parts, ann = [], []
    if kind == "shiko":
        outk = 10
        kL = (aL-outk, ANK + math.sqrt(SHIN**2-outk**2)); kR = (aR+outk, kL[1])
        hy = kL[1] + math.sqrt(THIGH**2 - (abs(kL[0])-hipx)**2)
        HL, HR = (-hipx, hy), (hipx, hy)
        legs = [limb([HL, kL, (aL, ANK)], 11), limb([HR, kR, (aR, ANK)], 11)]
        ann.append(line((kR[0], kR[1]), (kR[0], 0), "#c0392b", .9, "2 2"))
        ann.append(text((kR[0]+3, kR[1]-12), "knee over toes", 5.2, "#c0392b"))
    elif kind == "sanchin":
        hy = 94
        HL, HR = (-hipx, hy), (hipx, hy)
        kL = ik(HL, (aL, ANK), +1); kR = ik(HR, (aR, ANK), -1)
        legs = [limb([HL, kL, (aL, ANK)], 11), limb([HR, kR, (aR, ANK)], 11)]
        ann.append(text((24, 52), "knees pulled in", 5.2, "#c0392b"))
    else:
        straight = 0.985*(THIGH+SHIN)
        hy = ANK + math.sqrt(straight**2 - (hipx-abs(aL))**2) if abs(aL) < hipx+30 else 90
        if st["slug"].startswith("02"): hy = 93
        HL, HR = (-hipx, hy), (hipx, hy)
        kL = ik(HL, (aL, ANK), -1); kR = ik(HR, (aR, ANK), +1)
        legs = [limb([HL, kL, (aL, ANK)], 11), limb([HR, kR, (aR, ANK)], 11)]
    S_y = hy + 56
    torso = torso_front(hy, S_y)
    neck = neck_head(S_y)
    arms = arms_front(S_y, hy, st["pose"])
    head = ""; sh = ""; belt = ""
    feet = foot_front(aL, L["ang"]) + foot_front(aR, R["ang"])
    half = max(abs(aL), abs(aR)) + 40
    top = S_y + 30
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(-half)} {fmt(-top)} {fmt(2*half)} {fmt(top+6)}" '
           f'preserveAspectRatio="xMidYMax meet" class="fig">{ground(-half, half)}{feet}{"".join(legs)}{torso}{neck}{arms}{"".join(ann)}</svg>')
    return svg

def figure_kosa(st):
    hy = 72
    HL, HR = (-8, hy), (8, hy)
    rear = limb([HL, (3, 38), (21, 13)], 11, fill=GI_BACK)
    rear_foot = f'<ellipse cx="22.5" cy="-3.2" rx="5.2" ry="3.2" fill="#e5b98a" stroke="{NAVY}" stroke-width="1.2"/>'
    front = limb([HR, (13, 40), (10, ANK)], 11)
    front_foot = foot_front(10, 45)
    S_y = hy + 56
    ann = [text((38, 40), "back leg crosses behind", 5.0, "#c0392b"), text((38, 33), "front leg", 5.0, "#c0392b"),
           line((22, 22), (36, 38), "#c0392b", .8, "2 2")]
    g = torso_front(hy, S_y) + neck_head(S_y) + arms_front(S_y, hy, st["pose"])
    half = 75; top = S_y + 30
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-half} {fmt(-top)} {2*half} {fmt(top+6)}" preserveAspectRatio="xMidYMax meet" class="fig">'
            f'{ground(-half, half)}{rear_foot}{rear}{front_foot}{front}{g}{"".join(ann)}</svg>')

def figure(st):
    if st.get("kind") == "kosa": return figure_kosa(st)
    return figure_front(st) if st["view"] == "front" else figure_side(st)

# ---------- footprint (plan) ----------
FOOT_POLY = [(-3.4,0),(3.4,0),(4.9,7),(5.4,16),(4.6,22),(2.2,26),(-1.4,26),(-4.4,22),(-5,15),(-4.2,7)]
BALL_POLY = [(-5,16),(5.4,16),(4.6,22),(2.2,26),(-1.4,26),(-4.4,22)]

def rot(p, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return (p[0]*c + p[1]*s, -p[0]*s + p[1]*c)   # clockwise positive, y up

def foot_pts(f, kind=None):
    base = BALL_POLY if (kind or f.get("kind")) == "ball" else FOOT_POLY
    return [(f["heel"][0]+rot(q, f["ang"])[0], f["heel"][1]+rot(q, f["ang"])[1]) for q in base]

def footprint(st, W=560, Hh=420):
    feet = st["feet"]
    allpts = []
    for f in feet:
        full = dict(f); full["kind"] = None
        allpts += foot_pts(full)
    pad = 14
    minx = min(p[0] for p in allpts)-pad; maxx = max(p[0] for p in allpts)+pad
    miny = min(p[1] for p in allpts)-pad; maxy = max(p[1] for p in allpts)+pad
    # fit; keep room for arrow/labels
    minx -= 6; maxx += 6; maxy += 10; miny -= 6
    w = maxx-minx; h = maxy-miny
    s = min((W-20)/w, (Hh-20)/h, 4.3*W/560)
    # grid (10 cm) aligned to multiples of 10
    gx0 = math.floor(minx/10)*10; gx1 = math.ceil(maxx/10)*10
    gy0 = math.floor(miny/10)*10; gy1 = math.ceil(maxy/10)*10
    def tx(x): return (x-gx0)*s + (W-(gx1-gx0)*s)/2
    def ty(y): return (gy1-y)*s + (Hh-(gy1-gy0)*s)/2
    g = []
    for gx in range(gx0, gx1+1, 10):
        g.append(f'<line x1="{tx(gx):.1f}" y1="{ty(gy0):.1f}" x2="{tx(gx):.1f}" y2="{ty(gy1):.1f}" stroke="#cdd8e4" stroke-width="{1.4 if gx%50==0 else .8}"/>')
    for gy in range(gy0, gy1+1, 10):
        g.append(f'<line x1="{tx(gx0):.1f}" y1="{ty(gy):.1f}" x2="{tx(gx1):.1f}" y2="{ty(gy):.1f}" stroke="#cdd8e4" stroke-width="{1.4 if gy%50==0 else .8}"/>')
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Hh}" class="plan" font-family="Source Sans Pro,Source Sans 3,sans-serif">',
           f'<rect width="{W}" height="{Hh}" fill="#fbfcfe"/>', "".join(g)]
    roles = {}
    for i, f in enumerate(feet):
        role = f.get("role")
        col = GOLD if role in ("front",) else ("#5b87b0" if role in ("rear",) else (GOLD if role=="stand" else ("#5b87b0" if i==0 else GOLD)))
        pts = foot_pts(f)
        if f.get("kind") == "ball":
            full = dict(f); full["kind"] = None
            fp = foot_pts(full)
            out.append('<polygon points="%s" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="5 4"/>' % (" ".join(f"{tx(x):.1f},{ty(y):.1f}" for x,y in fp), NAVY))
        out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="2.4" stroke-linejoin="round"/>' % (" ".join(f"{tx(x):.1f},{ty(y):.1f}" for x,y in pts), col, NAVY))
    # direction arrow (top-left)
    ax, ay = 34, 74
    out.append(f'<g><line x1="{ax}" y1="{ay}" x2="{ax}" y2="26" stroke="{NAVY}" stroke-width="3"/><polygon points="{ax},16 {ax-8},30 {ax+8},30" fill="{NAVY}"/>'
               f'<text x="{ax}" y="{ay+18}" text-anchor="middle" font-size="15" font-weight="700" fill="{NAVY}">front</text></g>')
    # dimension lines
    def dim_v(x_cm, y0_cm, y1_cm, label):
        x = tx(x_cm); a, b = ty(y0_cm), ty(y1_cm)
        return (f'<line x1="{x:.1f}" y1="{a:.1f}" x2="{x:.1f}" y2="{b:.1f}" stroke="#c0392b" stroke-width="2"/>'
                f'<line x1="{x-5:.1f}" y1="{a:.1f}" x2="{x+5:.1f}" y2="{a:.1f}" stroke="#c0392b" stroke-width="2"/>'
                f'<line x1="{x-5:.1f}" y1="{b:.1f}" x2="{x+5:.1f}" y2="{b:.1f}" stroke="#c0392b" stroke-width="2"/>'
                f'<text x="{x+8:.1f}" y="{(a+b)/2+5:.1f}" font-size="15" font-weight="700" fill="#c0392b">{label}</text>')
    def dim_h(y_cm, x0_cm, x1_cm, label):
        y = ty(y_cm); a, b = tx(x0_cm), tx(x1_cm)
        return (f'<line x1="{a:.1f}" y1="{y:.1f}" x2="{b:.1f}" y2="{y:.1f}" stroke="#c0392b" stroke-width="2"/>'
                f'<line x1="{a:.1f}" y1="{y-5:.1f}" x2="{a:.1f}" y2="{y+5:.1f}" stroke="#c0392b" stroke-width="2"/>'
                f'<line x1="{b:.1f}" y1="{y-5:.1f}" x2="{b:.1f}" y2="{y+5:.1f}" stroke="#c0392b" stroke-width="2"/>'
                f'<text x="{(a+b)/2:.1f}" y="{y-8:.1f}" text-anchor="middle" font-size="15" font-weight="700" fill="#c0392b">{label}</text>')
    if len(feet) == 2:
        a, b = feet
        dy = abs(a["heel"][1]-b["heel"][1]); dx = abs(a["heel"][0]-b["heel"][0])
        lo, hi = sorted([a, b], key=lambda f: f["heel"][1])
        if dy >= 15 and not b.get("kind") == "ball" and not a.get("kind") == "ball":
            out.append(dim_v(maxx-8, lo["heel"][1], hi["heel"][1], f"{dy:.0f} cm"))
        if dx >= 25:
            lx = sorted([a, b], key=lambda f: f["heel"][0])
            out.append(dim_h(min(a["heel"][1], b["heel"][1])-4, lx[0]["heel"][0], lx[1]["heel"][0], f"{dx:.0f} cm"))
    out.append(f'<text x="{W-10}" y="{Hh-10}" text-anchor="end" font-size="13" fill="#5a6b7c">each grid square = 10 cm</text>')
    out.append("</svg>")
    return "".join(out)

def weight_bar(st):
    la, pa, lb, pb = st["weight"]
    gold = lambda lab: lab.split()[0] in ("Front", "Right", "Standing")
    segs = []
    for lab, pct in ((la, pa), (lb, pb)):
        if pct:
            cls = "wb" if gold(lab) else "wa"
            segs.append(f'<div class="{cls}" style="flex:{pct};min-width:{ 190 if pct < 30 else 0}px">{lab} {pct}%</div>')
    return '<div class="wbar">' + "".join(segs) + "</div>"
