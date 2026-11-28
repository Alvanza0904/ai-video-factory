#!/usr/bin/env python3
"""Free-first Indonesian 2D educational animation renderer."""
import json, math, os, subprocess, sys, urllib.parse, urllib.request, urllib.error, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path.cwd()
WORK = ROOT / "education-work"
OUT = ROOT / "ai-video-factory-final.mp4"
W, H, FPS = 540, 960, 15
MODEL = Path(os.environ.get("PIPER_MODEL", "models/id_ID-news_tts-medium.onnx"))
ACTIVE_BRAND = "JAECOO"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TOPICS = {
 "regenerative braking": [
  ("Bayangin, saat mobil listrik melambat, sebagian energi geraknya ternyata masih bisa dimanfaatkan lagi. Kok bisa?", "car", "ENERGI SAAT REM, KE MANA?"),
  ("Di sinilah regenerative braking bekerja. Begitu kamu lepas pedal gas atau mulai mengerem, motor listrik bisa berubah tugas jadi generator.", "motor", "MOTOR JADI GENERATOR"),
  ("Roda yang masih berputar memutar motor. Proses ini menghasilkan energi listrik, bukan sekadar membuang energi menjadi panas.", "energy", "GERAK JADI LISTRIK"),
  ("Listrik yang dihasilkan kemudian diatur sistem kendaraan, lalu dialirkan kembali untuk mengisi baterai.", "battery", "KEMBALI KE BATERAI"),
  ("Efeknya terasa saat perjalanan stop-and-go, karena sebagian energi yang biasanya terbuang bisa dipulihkan.", "car", "MEMBANTU EFISIENSI"),
  ("Tapi ingat, energi tidak kembali seratus persen. Tetap ada kehilangan karena panas dan hambatan.", "temperature", "BUKAN ENERGI GRATIS"),
  ("Jumlah energi yang pulih dipengaruhi kecepatan, kondisi baterai, jalan, dan pengaturan pengereman.", "chart", "HASILNYA BISA BERBEDA"),
  ("Jadi, regenerative braking membantu efisiensi dan memberi deselerasi yang bisa diatur. Menarik, kan?", "energy", "SEKARANG KAMU TAHU")
 ],
 "baterai lfp": [
  ("Sering dengar istilah baterai LFP, tapi masih bingung maksudnya? Santai, kita bahas pelan-pelan.", "battery", "KENAPA BATERAI LFP?"),
  ("LFP adalah singkatan lithium iron phosphate. Material utamanya terdiri dari lithium, besi, dan fosfat.", "chemistry", "LITHIUM • BESI • FOSFAT"),
  ("Salah satu karakter menariknya adalah stabilitas termal yang baik. Ini penting untuk pengelolaan panas baterai.", "temperature", "STABILITAS TERMAL"),
  ("LFP juga dikenal punya potensi umur siklus yang panjang, tergantung desain sel dan cara penggunaannya.", "chart", "UMUR SIKLUS"),
  ("Di sisi lain, kepadatan energinya umumnya lebih rendah dibanding beberapa kimia baterai lain. Jadi bobot dan ukuran perlu dihitung.", "battery", "ADA PLUS DAN MINUS"),
  ("Kinerja baterai tetap dipengaruhi suhu, sistem pendingin, pola pengisian, dan battery management system.", "charging", "BMS IKUT BERPERAN"),
  ("Karena itu, jangan menilai mobil listrik dari jenis baterainya saja. Lihat kapasitas, garansi, jarak tempuh, dan spesifikasi resminya.", "checklist", "CEK MENYELURUH"),
  ("Nah, sekarang kamu punya gambaran dasar tentang LFP. Simpan video ini kalau penjelasannya bermanfaat.", "question", "PAHAM LFP LEBIH MUDAH")
 ],
 "bev hev phev": [
  ("BEV, HEV, PHEV. Namanya mirip banget, ya? Tapi jangan ketuker, karena cara kerjanya beda.", "threecars", "TIGA JENIS, TIGA CARA"),
  ("Kita mulai dari BEV. Ini mobil listrik murni: motor listrik menggerakkan roda dan baterai jadi sumber energi utama.", "battery", "BEV • LISTRIK MURNI"),
  ("Karena tidak memakai mesin bensin sebagai penggerak, BEV perlu diisi dari sumber listrik eksternal.", "charging", "BEV DIISI DARI LUAR"),
  ("Berikutnya HEV. Mobil ini menggabungkan mesin bensin dan motor listrik. Baterainya umumnya terisi saat berkendara dan mengerem.", "hybrid", "HEV • HYBRID"),
  ("Nah, PHEV juga menggabungkan mesin dan motor listrik. Bedanya, baterainya bisa diisi dari colokan listrik.", "charging", "PHEV • PLUG-IN HYBRID"),
  ("Cara gampang mengingatnya: BEV listrik murni, HEV hybrid, dan PHEV hybrid yang bisa di-charge dari luar.", "threecars", "INGAT PERBEDAANNYA"),
  ("Pilihan terbaik bergantung pada rutinitas, akses charging, dan jarak perjalanan harian kamu.", "chart", "SESUAIKAN RUTINITAS"),
  ("Jadi, jangan cuma lihat namanya. Pahami sistem tenaga dan cek spesifikasi model yang ingin kamu pilih.", "checklist", "PILIH DENGAN PAHAM")
 ],
 "ac dc charging": [
  ("Mau nge-charge mobil listrik? Eits, AC dan DC itu beda, lho. Yuk, lihat bedanya biar nggak salah pilih.", "charging", "AC VS DC CHARGING"),
  ("AC adalah arus bolak-balik. Listrik masuk ke mobil, lalu onboard charger mengubahnya menjadi arus searah untuk baterai.", "ac", "AC • KONVERSI DI MOBIL"),
  ("Karena konversi dilakukan di dalam kendaraan, kecepatan AC dibatasi kemampuan onboard charger.", "battery", "BATAS ONBOARD CHARGER"),
  ("Pada DC, konversi utama sudah dilakukan di stasiun pengisian. Listrik searah kemudian disalurkan ke baterai.", "dc", "DC • KONVERSI DI STASIUN"),
  ("Itulah sebabnya DC fast charging umumnya menawarkan daya lebih tinggi dan waktu pengisian lebih singkat.", "charging", "DC FAST CHARGING"),
  ("Tapi mobil tidak selalu menerima daya maksimum. Suhu baterai dan persentase isi ikut berpengaruh.", "temperature", "DAYA BISA BERUBAH"),
  ("Jadi, cek kemampuan AC dan DC mobil, konektor, serta batas daya yang didukung sebelum mengisi.", "checklist", "CEK KOMPATIBILITAS"),
  ("Sekarang bedanya lebih jelas, kan? AC dan DC sama-sama berguna, tinggal sesuaikan dengan kebutuhan.", "question", "PILIH SESUAI KEBUTUHAN")
 ],
 "motor listrik": [
  ("Pernah kepikiran nggak, mobil listrik bisa jalan tanpa mesin bensin? Terus, siapa yang muterin rodanya? Nah, kita ikuti alurnya!", "car", "RAHASIA DI BALIK RODA"),
  ("Pertama, ada baterai. Anggap saja ini tempat menyimpan energi. Listrik yang keluar berbentuk arus searah alias DC.", "battery", "1 • BATERAI MENYIMPAN"),
  ("Begitu pedal gas kamu injak, sistem kontrol langsung membaca: mobil butuh tenaga seberapa besar, nih?", "system", "2 • KONTROL DAYA"),
  ("Lalu listrik masuk ke inverter. Tugasnya mengatur aliran listrik supaya cocok dengan kebutuhan motor. Jadi, bukan asal kirim, ya.", "motor", "3 • INVERTER MENGATUR ARUS"),
  ("Nah, ini bagian serunya! Motor mengubah energi listrik jadi putaran. Putaran itu menghasilkan torsi yang nantinya bikin roda bergerak.", "energy", "4 • MOTOR MEMUTAR RODA"),
  ("Putaran motor diteruskan ke roda lewat sistem reduksi gear. Makanya, respons awal mobil listrik bisa terasa spontan.", "car", "5 • RODA BERGERAK"),
  ("Terus ada bonusnya. Saat mobil melambat, motor bisa berubah fungsi jadi generator dan mengirim sebagian energi kembali ke baterai.", "energy", "BONUS • ENERGI DIPULIHKAN"),
  ("Jadi gampangnya: baterai, kontrol daya, inverter, motor, lalu roda. Sekarang kebayang, kan, gimana mobil listrik bisa melaju?", "checklist", "BATERAI → RODA")
 ]
}

def run(cmd, **kwargs):
    print("+", " ".join(map(str, cmd[:8])), flush=True)
    subprocess.run(cmd, check=True, **kwargs)

def fetch_manifest():
    job = os.environ["JOB_ID"]
    query = urllib.parse.urlencode({"job_id": job, "run_id": os.environ["GITHUB_RUN_ID"]})
    req = urllib.request.Request(os.environ["MANIFEST_URL"] + "?" + query,
        headers={
            "Authorization": "Bearer " + os.environ["OIDC_TOKEN"],
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.8127.88 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
        })
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:1200]
        print("MANIFEST HTTP ERROR:", error.code, dict(error.headers), detail, file=sys.stderr, flush=True)
        raise

def choose_script(topic, duration):
    key = topic.lower()
    if "regenerative" in key or "pengereman" in key or "rem" in key:
        scenes = TOPICS["regenerative braking"]
    elif "lfp" in key or "baterai" in key:
        scenes = TOPICS["baterai lfp"]
    elif "bev" in key or "phev" in key or "hev" in key or "hybrid" in key:
        scenes = TOPICS["bev hev phev"]
    elif "ac" in key or "dc" in key or "charging" in key or "pengisian" in key or "charger" in key:
        scenes = TOPICS["ac dc charging"]
    elif "motor" in key or "inverter" in key:
        scenes = TOPICS["motor listrik"]
    else:
        scenes = [
          ("Pernah penasaran bagaimana " + topic + " bekerja? Ada hal menarik yang sering terlewat. Yuk, kita lihat.", "question", "ADA YANG MENARIK DI SINI"),
          ("Pertama, kenali dulu komponen utama. Setiap bagian punya tugas yang berbeda.", "parts", "KENALI KOMPONENNYA"),
          ("Setelah itu, lihat bagaimana energi atau informasi mengalir dari satu bagian ke bagian berikutnya.", "system", "IKUTI ALURNYA"),
          ("Perhatikan hubungan antarbagian. Satu komponen memberi masukan, bagian lain merespons.", "motor", "SEMUA SALING TERHUBUNG"),
          ("Dalam penggunaan nyata, hasilnya dipengaruhi desain, kondisi, dan spesifikasi kendaraan.", "car", "KONDISI MENENTUKAN"),
          ("Ada juga batasan yang perlu dipahami. Tidak semua teknologi bekerja maksimal di setiap situasi.", "chart", "ADA FAKTOR PEMBATAS"),
          ("Jadi, periksa cara kerja dan spesifikasi dari sumber resmi sebelum mengambil kesimpulan.", "checklist", "PERIKSA SUMBER RESMI"),
          ("Sekarang kamu punya gambaran dasar tentang " + topic + ". Simpan video ini untuk mengingat penjelasannya.", "question", "SEKARANG SUDAH TAHU")
        ]
    if duration == 30:
        scenes = [scenes[i] for i in (0, 1, 3, 5, 7) if i < len(scenes)]
    elif duration == 45:
        scenes = scenes[:7]
    return [{"narration": x[0], "visual": x[1], "title": x[2]} for x in scenes]

def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def centered(draw, text, y, fnt, fill, maxw=470):
    words, lines, line = text.split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textbbox((0,0), test, font=fnt)[2] <= maxw: line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    for ln in lines:
        box = draw.textbbox((0,0), ln, font=fnt)
        draw.text(((W-(box[2]-box[0]))/2, y), ln, font=fnt, fill=fill)
        y += fnt.size + 10
    return y

def caption_lines(text, fnt, max_width=420):
    probe = ImageDraw.Draw(Image.new("RGB",(1,1)))
    words, lines, line = text.split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if probe.textbbox((0,0), test, font=fnt)[2] <= max_width:
            line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    if len(lines) > 2:
        last = lines[1]
        while last and probe.textbbox((0,0), last + "…", font=fnt)[2] > max_width:
            last = last[:-1]
        lines = [lines[0], last.rstrip() + "…"]
    return lines[:2]

def rr(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def draw_car(d, cx, cy, scale=1.0, accent="#B8F36A", phase=0.0):
    bw, bh = int(260*scale), int(94*scale)
    x, y = int(cx-bw/2), int(cy-bh/2)
    d.rounded_rectangle((x,y+30*scale,x+bw,y+bh), radius=int(26*scale), fill="#DCE8F2", outline="#FFFFFF", width=3)
    d.polygon([(x+45*scale,y+31*scale),(x+88*scale,y),(x+190*scale,y),(x+225*scale,y+31*scale)], fill="#9DC8E4")
    d.line([(x+88*scale,y+4*scale),(x+88*scale,y+31*scale),(x+190*scale,y+31*scale),(x+190*scale,y+4*scale)], fill="#4D657A", width=3)
    for wx in (x+58*scale,x+202*scale):
        d.ellipse((wx-22*scale,y+bh-8*scale,wx+22*scale,y+bh+36*scale), fill="#172334", outline="#9AAABD", width=4)
        d.ellipse((wx-8*scale,y+bh+6*scale,wx+8*scale,y+bh+22*scale), fill=accent)
        for spoke in range(4):
            angle=phase*math.pi*2+spoke*math.pi/2
            sx=wx+math.cos(angle)*13*scale; sy=y+bh+14*scale+math.sin(angle)*13*scale
            d.line((wx,y+bh+14*scale,sx,sy),fill="#D8E6EF",width=max(1,int(2*scale)))
    d.rounded_rectangle((x+8*scale,y+48*scale,x+30*scale,y+65*scale), radius=5, fill="#FFE8A3")
    d.rounded_rectangle((x+bw-30*scale,y+48*scale,x+bw-8*scale,y+65*scale), radius=5, fill="#FF7A72")

def draw_battery(d, cx, cy, progress, accent="#B8F36A"):
    x,y=cx-115,cy-95
    rr(d,(x,y,x+230,y+190),24,"#E8F0F5","#FFFFFF",4)
    rr(d,(x+230,y+62,x+252,y+128),8,"#E8F0F5")
    fill=max(0.08,min(.92,progress))
    d.rounded_rectangle((x+18,y+18,x+18+194*fill,y+172),radius=15,fill=accent)
    d.text((cx,y+90),"",font=font(20),fill="#172334")

def draw_person(d, cx, cy, phase):
    d.ellipse((cx-55,cy-130,cx+55,cy-20),fill="#F0C5A4",outline="#FFFFFF",width=3)
    d.arc((cx-62,cy-145,cx+62,cy-8),180,355,fill="#26364B",width=22)
    d.rounded_rectangle((cx-85,cy-10,cx+85,cy+190),radius=48,fill="#B8F36A",outline="#FFFFFF",width=3)
    arm_y=cy+45+int(math.sin(phase*math.pi*2)*12)
    d.line((cx-75,cy+20,cx-145,arm_y),fill="#F0C5A4",width=22)
    d.line((cx+75,cy+20,cx+145,arm_y-25),fill="#F0C5A4",width=22)
    d.ellipse((cx-22,cy-75,cx-8,cy-61),fill="#243044")
    d.ellipse((cx+8,cy-75,cx+22,cy-61),fill="#243044")
    d.arc((cx-18,cy-65,cx+18,cy-38),0,180,fill="#8E5148",width=3)

def draw_frame(scene, idx, total):
    p = idx / max(1,total-1)
    img=Image.new("RGB",(W,H),(12,20,31))
    d=ImageDraw.Draw(img)
    accent="#B8F36A"; cyan="#65D8F2"; white="#F3F7FA"; muted="#A9B8C8"
    # Layered city / road background with continuous parallax.
    for y in range(H):
        t=y/H
        col=tuple(int(a*(1-t)+b*t) for a,b in zip((13,25,39),(24,43,57)))
        d.line((0,y,W,y),fill=col)
    for j in range(11):
        x=(j*63-int(p*95))%650-55
        bh=120+(j*47)%190
        d.rectangle((x,500-bh,x+42,500),fill="#1C3445",outline="#29495A")
        for wy in range(4):
            for wx in range(2):
                d.rectangle((x+8+wx*17,510-bh+wy*35,x+14+wx*17,520-bh+wy*35),fill="#36566A")
    # Moving road and dashed lane lines.
    d.rectangle((0,590,W,745),fill="#263744")
    d.line((0,665,W,665),fill="#DCE6E8",width=3)
    for j in range(8):
        x=(j*100-int(p*260))%650-40
        d.rounded_rectangle((x,657,x+48,672),radius=5,fill="#E6E8DC")
    # Small moving traffic gives every scene a sense of life.
    for j in range(3):
        cx=(j*245+int(p*260))%760-100
        draw_car(d,cx,625,0.25, "#65D8F2" if j%2 else "#F6B35B",p*5+j)
    # Header is compact; content owns the frame.
    rr(d,(24,28,W-24,76),16,"#203545",outline="#3B586A")
    d.text((42,43),"AUTO EXPLAINER  •  ANIMATED",font=font(14,True),fill=accent)
    # Animated scene title enters from below, then settles.
    title_y=104+int(24*(1-min(1,p*4)))
    centered(d,scene["title"],title_y,font(27,True),white,470)
    v=scene["visual"]
    # Motion helpers.
    def particle_path(x1,y1,x2,y2,count=7):
        for k in range(count):
            q=(p*1.7+k/count)%1
            x=int(x1+(x2-x1)*q); y=int(y1+(y2-y1)*q)
            r=4+(k%3)
            d.ellipse((x-r,y-r,x+r,y+r),fill=accent,outline="#E8FFC0")
    def component(box,label,fill,sub=None):
        rr(d,box,20,fill,outline="#DCEAF0",width=3)
        x1,y1,x2,y2=box
        centered(d,label,y1+18,font(17,True),white,x2-x1-16)
        if sub: centered(d,sub,y1+49,font(12),muted,x2-x1-12)
    if v in ("car","threecars","hybrid"):
        # Driving car with wheel rotation, acceleration streaks and moving energy trail.
        shift=int(-70+210*p)
        for k in range(5):
            xx=45+k*24+int(p*90)%35
            d.line((xx,540,xx+18,540),fill=cyan,width=3)
        draw_car(d,270+shift,470,0.95,accent,p*8)
        rr(d,(55,570,485,625),15,"#1B3445",outline=cyan)
        centered(d,"AKSELERASI  •  TORSI  •  GERAK",585,font(15,True),white,400)
        if v=="threecars":
            for j,label in enumerate(("BEV","HEV","PHEV")):
                component((34+j*158,785,178+j*158,850),label,"#28475B")
        elif v=="hybrid":
            particle_path(80,690,455,690,9)
            centered(d,"MESIN + MOTOR LISTRIK",710,font(18,True),white,420)
    elif v in ("battery","charging","temperature","chemistry"):
        # Battery cells illuminate one by one; charge stream visibly enters.
        x,y=105,330
        rr(d,(x,y,x+330,y+210),28,"#DCE7EB",outline=white,width=5)
        rr(d,(x+330,y+65,x+355,y+145),9,"#DCE7EB")
        for k in range(6):
            fill="#B8F36A" if k/6 < p else "#527D68"
            bx=x+17+k*50
            rr(d,(bx,y+18,bx+42,y+192),9,fill)
            if k/6 < p:
                d.ellipse((bx+13,y+65,bx+29,y+81),fill="#F6FFD8")
        particle_path(20,435,100,435,6)
        centered(d,"ENERGI TERSIMPAN DI DALAM SEL",575,font(17,True),white,470)
        if v=="charging":
            d.line((270,650,270,745),fill=cyan,width=10)
            d.polygon([(250,730),(290,730),(270,765)],fill=cyan)
            centered(d,"PENGISIAN DAYA",780,font(16,True),accent,400)
        elif v=="temperature":
            for k in range(4):
                yy=630-k*30-int(p*20)
                d.arc((180+k*10,yy,360-k*10,yy+55),190,350,fill="#FF986E",width=7)
            centered(d,"PANTAU SUHU BATERAI",790,font(16,True),white,420)
    elif v in ("motor","energy","ac","dc","system","parts"):
        # Three linked components show the energy path instead of a decorative ring.
        y=390
        component((22,y,166,y+130),"BATERAI","#28536A","ARUS DC")
        component((198,y,342,y+130),"INVERTER","#36516D","ATUR DAYA")
        component((374,y,518,y+130),"MOTOR","#28536A","PUTARAN")
        particle_path(166,y+65,198,y+65,5)
        particle_path(342,y+65,374,y+65,5)
        if v in ("motor","energy"):
            # Cutaway motor with rotating rotor, stator coils and torque arrows.
            d.ellipse((125,590,415,880),fill="#223B4D",outline="#D7E7EF",width=8)
            d.ellipse((158,623,382,847),outline=cyan,width=15)
            d.ellipse((205,670,335,800),fill="#B8F36A",outline=white,width=5)
            angle=p*math.pi*8
            for k in range(8):
                a=angle+k*math.pi/4
                x1=270+math.cos(a)*45; y1=735+math.sin(a)*45
                x2=270+math.cos(a)*98; y2=735+math.sin(a)*98
                d.line((x1,y1,x2,y2),fill="#F6D27A",width=8)
            d.arc((90,555,450,910),int(20+p*260),int(150+p*260),fill=accent,width=9)
            d.polygon([(420,640),(449,655),(421,670)],fill=accent)
            centered(d,"ROTOR BERPUTAR  •  TORSI MENGGERAKKAN RODA",885,font(13,True),white,500)
        elif v=="ac":
            for k in range(3):
                pts=[]
                for xx in range(40,500,5):
                    yy=650+k*42+int(math.sin((xx/500*math.pi*5)-p*math.pi*8)*18)
                    pts.append((xx,yy))
                d.line(pts,fill=cyan if k==0 else accent,width=4)
            centered(d,"ARUS BOLAK-BALIK",810,font(17,True),white,440)
        elif v=="dc":
            for k in range(8):
                xx=50+k*58
                d.rectangle((xx,690,xx+28,690+int(30+70*p)),fill=accent)
            centered(d,"ARUS SEARAH MENUJU BATERAI",810,font(17,True),white,460)
    elif v=="question":
        draw_person(d,270,420,p)
        # Speech bubble pulses in and out.
        bob=int(8*math.sin(p*math.pi*4))
        rr(d,(48,650+bob,492,740+bob),24,"#29485A",outline=cyan,width=4)
        centered(d,"KOK BISA?  •  YUK, KITA BEDAH!",680+bob,font(19,True),white,410)
    elif v=="chart":
        for j,label in enumerate(("ENERGI","EFISIENSI","KONDISI")):
            x=65+j*145; base=740
            height=int(60+150*min(1,max(0,p*1.8-j*.2)))
            rr(d,(x,base-height,x+80,base),13,"#244255",outline=cyan if j==1 else "#547084")
            centered(d,label,base+18,font(12,True),white,100)
        centered(d,"FAKTOR YANG MEMPENGARUHI",810,font(17,True),white,460)
    elif v=="checklist":
        for j,label in enumerate(("KENALI TEKNOLOGINYA","CEK SPESIFIKASI","PAHAMI KEBUTUHAN")):
            y=350+j*125
            slide=int(60*(1-min(1,p*4)))
            rr(d,(65+slide,y,475+slide,y+78),18,"#203747",outline=accent if j==0 else "#426073")
            d.ellipse((88+slide,y+22,122+slide,y+56),fill=accent)
            d.line((97+slide,y+39,105+slide,y+47,116+slide,y+30),fill="#142334",width=5)
            d.text((140+slide,y+27),label,font=font(16,True),fill=white)
    else:
        draw_person(d,270,450,p)
    # Captions are clean lower-third labels, no oversized opaque slide card.
    cap=caption_lines(scene.get("narration",""),font(16,True),450)
    base_y=900 if len(cap)==1 else 870
    for line in cap:
        box=d.textbbox((0,0),line,font=font(16,True))
        tw=box[2]-box[0]
        rr(d,((W-tw)//2-14,base_y-5,(W+tw)//2+14,base_y+28),10,"#101D29",outline="#456073",width=1)
        d.text(((W-tw)//2,base_y),line,font=font(16,True),fill=white)
        base_y+=27
    # Scene progress and floating kinetic markers.
    d.rounded_rectangle((32,940,508,950),radius=5,fill="#314353")
    d.rounded_rectangle((32,940,32+int(476*p),950),radius=5,fill=accent)
    for k in range(3):
        xx=45+k*225+int(p*45)
        d.ellipse((xx,180+k*38,xx+9,189+k*38),fill=cyan if k%2 else accent)
    return img

def make_subtitles(scenes, voice_duration):
    total_words=sum(max(1,len(s["narration"].split())) for s in scenes)
    cursor=0.0
    lines=[]
    for i,s in enumerate(scenes,1):
        words=max(1,len(s["narration"].split()))
        duration=voice_duration*words/total_words
        start=cursor+0.05
        end=min(voice_duration,cursor+duration)
        text=s["narration"].replace("--","—")
        lines.append(f"{i}\n{stamp(start)} --> {stamp(max(start+0.6,end-0.08))}\n{text}\n")
        cursor+=duration
    path=WORK/"captions.srt"
    path.write_text("\n".join(lines),encoding="utf-8")
    return path

def stamp(seconds):
    ms=int(max(0,seconds)*1000)
    h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def piper_voice(scene_texts):
    if not MODEL.exists():
        raise RuntimeError("Model suara Bahasa Indonesia tidak ditemukan.")
    # Synthesize one complete spoken thought per scene. This gives the TTS a
    # fresh phrase boundary and adds a short breathing pause between ideas.
    if isinstance(scene_texts, str):
        scene_texts = [scene_texts]
    clips=[]
    for index, spoken_text in enumerate(scene_texts,1):
        spoken_text=spoken_text.strip()
        if not spoken_text:
            continue
        clip=WORK/f"voice-{index:02d}.wav"
        proc=subprocess.run(["piper","--model",str(MODEL),"--length_scale","1.10",
            "--noise_scale","0.72","--noise_w","0.82","--output_file",str(clip)],
            input=spoken_text,text=True,capture_output=True)
        if proc.returncode:
            raise RuntimeError("Piper TTS gagal: "+proc.stderr[-700:])
        if not clip.exists() or clip.stat().st_size<1000:
            raise RuntimeError("Piper tidak menghasilkan audio untuk scene "+str(index))
        clips.append(clip)
    if not clips:
        raise RuntimeError("Naskah suara kosong.")
    output=WORK/"narration.wav"
    with wave.open(str(clips[0]),"rb") as first:
        params=first.getparams()
    silence_frames=int(params.framerate*0.20)
    silence=b"\x00"*(silence_frames*params.nchannels*params.sampwidth)
    with wave.open(str(output),"wb") as combined:
        combined.setparams(params)
        for index,clip in enumerate(clips):
            with wave.open(str(clip),"rb") as part:
                combined.writeframes(part.readframes(part.getnframes()))
            if index < len(clips)-1:
                combined.writeframes(silence)
    return output

def make_sound_design(scene_durations, total_duration):
    """Create original lightweight whoosh/pop/electric/motor SFX and a rhythmic music bed."""
    import random, struct
    rate=24000
    count=int(total_duration*rate)
    mix=[0.0]*count
    music=[0.0]*count
    # Soft upbeat electronic bed: bass pulse, chord pads and a restrained click beat.
    chords=[(110.0,138.59,164.81),(98.0,123.47,146.83),(123.47,155.56,185.0),(110.0,138.59,164.81)]
    for i in range(count):
        t=i/rate
        beat=int(t*2)%4
        chord=chords[int(t/2)%len(chords)]
        pad=sum(math.sin(2*math.pi*f*t)*0.22 for f in chord)/3
        bass=math.sin(2*math.pi*(55 if beat in (0,2) else 65.4)*t)*0.20
        pulse=max(0,1-(t*2%1))*0.06
        music[i]=(pad+bass+pulse)*0.16
    rng=random.Random(23)
    cursor=0.0
    for idx,duration in enumerate(scene_durations):
        # Short whoosh on scene change, then a tactile pop; selected scenes get electric/motor texture.
        events=[(cursor+0.04,"whoosh"),(cursor+0.32,"pop")]
        if idx in (1,2,3,4,6): events.append((cursor+0.72,"electric" if idx in (1,3,6) else "motor"))
        for at,kind in events:
            start=int(at*rate)
            length=int((0.42 if kind=="whoosh" else 0.18 if kind=="pop" else 0.55)*rate)
            for j in range(length):
                pos=start+j
                if pos>=count: break
                t=j/rate
                env=(1-j/length)
                if kind=="whoosh":
                    val=(rng.random()*2-1)*env*env*0.23*math.sin(math.pi*j/length)
                elif kind=="pop":
                    val=math.sin(2*math.pi*(180+520*env)*t)*env*0.25
                elif kind=="electric":
                    val=(math.sin(2*math.pi*880*t)+0.35*math.sin(2*math.pi*1320*t))*env*0.10
                else:
                    val=math.sin(2*math.pi*(75+95*env)*t)*env*0.18
                mix[pos]+=val
        cursor+=duration
    sfx_path=WORK/"sound-effects.wav"
    music_path=WORK/"music-bed.wav"
    for path,data,scale in ((sfx_path,mix,0.8),(music_path,music,0.75)):
        with wave.open(str(path),"wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate)
            chunk=bytearray()
            for value in data:
                sample=max(-32767,min(32767,int(value*scale*32767)))
                chunk.extend(struct.pack("<h",sample))
            wf.writeframes(chunk)
    return sfx_path,music_path

def main():
    global ACTIVE_BRAND
    WORK.mkdir(exist_ok=True)
    if os.environ.get("SMOKE_TEST") == "1":
        manifest={"jobId":"smoke-test","userId":"smoke-test","expires":"0","signature":"0","brand":"JAECOO","topic":"regenerative braking","duration":30}
    else:
        manifest=fetch_manifest()
    ACTIVE_BRAND=manifest["brand"]
    topic=manifest["topic"]
    brand=manifest["brand"]
    duration=int(manifest["duration"])
    scenes=choose_script(topic,duration)
    narration=" ".join(s["narration"] for s in scenes)
    print("Narration:",narration,flush=True)
    audio=piper_voice([s["narration"] for s in scenes])
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(audio)]))
    voice_duration=float(probe["format"]["duration"])
    total_duration=voice_duration+1.8
    print(f"TTS duration {voice_duration:.2f}s; output {total_duration:.2f}s",flush=True)
    subs=make_subtitles(scenes,voice_duration)
    word_counts=[max(1,len(s["narration"].split())) for s in scenes]
    total_words=sum(word_counts)
    cursor=0.0
    clip_paths=[]
    for n,scene in enumerate(scenes,1):
        scene_duration=total_duration*word_counts[n-1]/total_words
        frames=max(30,round(scene_duration*FPS))
        folder=WORK/f"scene-{n:02d}"
        folder.mkdir(exist_ok=True)
        for frame in range(frames):
            draw_frame(scene,frame,frames).save(folder/f"frame-{frame:04d}.png",optimize=False)
        clip=WORK/f"scene-{n:02d}.mp4"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate",str(FPS),
             "-i",str(folder/"frame-%04d.png"),"-vf","scale=1080:1920:flags=lanczos,fps=30,format=yuv420p",
             "-an","-c:v","libx264","-preset","ultrafast","-crf","24","-movflags","+faststart",str(clip)])
        clip_paths.append(clip)
        cursor+=scene_duration
    concat=WORK/"concat.txt"
    concat.write_text("".join("file '"+str(p.resolve())+"'\n" for p in clip_paths),encoding="utf-8")
    silent=WORK/"silent.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),
         "-c","copy","-movflags","+faststart",str(silent)])
    scene_durations=[total_duration*w/total_words for w in word_counts]
    sfx,music=make_sound_design(scene_durations,total_duration)
    vf="null"  # Captions are burned into each animated scene at a controlled size.
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(audio),
         "-i",str(music),"-i",str(sfx),"-filter_complex",
         "[1:a]volume=1.0[voice];[2:a]volume=0.16[bed];[3:a]volume=0.42[fx];[voice][bed][fx]amix=inputs=3:duration=first:dropout_transition=1,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
         "-vf",vf,"-map","0:v:0","-map","[a]","-t",f"{total_duration:.2f}",
         "-r","30","-c:v","libx264","-preset","veryfast","-crf","22","-c:a","aac","-b:a","160k",
         "-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)])
    final=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_name,width,height","-of","json",str(OUT)]))
    video=next((s for s in final["streams"] if s.get("codec_name")=="h264"),None)
    if not video or video.get("width")!=1080 or video.get("height")!=1920:
        raise RuntimeError("Quality check gagal: output bukan H.264 1080x1920.")
    if OUT.stat().st_size<100000:
        raise RuntimeError("Quality check gagal: file MP4 terlalu kecil.")
    blueprint={"brand":brand,"topic":topic,"duration":float(final["format"]["duration"]),
        "style":"2D explainer + cartoon + motion graphics","voice":"Piper Indonesian medium (conversational pacing; limited expressiveness)",
        "scenes":scenes}
    (WORK/"blueprint.json").write_text(json.dumps(blueprint,ensure_ascii=False,indent=2),encoding="utf-8")
    if os.environ.get("SMOKE_TEST") == "1":
        print(f"SMOKE PASS: rendered {final['format']['duration']}s education video ({OUT.stat().st_size} bytes).",flush=True)
        return
    params=urllib.parse.urlencode({"job_id":manifest["jobId"],"user_id":manifest["userId"],
        "expires":manifest["expires"],"signature":manifest["signature"],"run_id":os.environ["GITHUB_RUN_ID"]})
    req=urllib.request.Request(os.environ["OUTPUT_UPLOAD_BASE_URL"]+"?"+params,data=OUT.read_bytes(),
        headers={"Content-Type":"video/mp4","Content-Length":str(OUT.stat().st_size),
        "Authorization":"Bearer "+os.environ["OIDC_TOKEN"],"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.8127.88 Safari/537.36"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=300) as response:
            result=json.loads(response.read().decode())
            if not result.get("success"): raise RuntimeError("R2 tidak mengonfirmasi unggahan video.")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"Upload video ke R2 gagal (HTTP {error.code}): {detail}") from None
    print(f"SUCCESS: {brand} education video '{topic}' — {final['format']['duration']} sec, {OUT.stat().st_size} bytes.",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("EDUCATION ANIMATION FAILED:",str(exc),file=sys.stderr)
        sys.exit(1)
