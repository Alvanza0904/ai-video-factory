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
    p=idx/max(1,total-1); ease=lambda x:max(0,min(1,x))**2*(3-2*max(0,min(1,x)))
    img=Image.new("RGB",(W,H),"#EAF2EF"); d=ImageDraw.Draw(img)
    navy="#122B3A"; ink="#173746"; teal="#18A6A0"; lime="#C6F36A"; blue="#59C7E8"
    for j in range(8):
        x=(j*105-int(p*145))%720-90
        d.polygon([(x,0),(x+48,0),(x-95,960),(x-143,960)],fill="#E2ECE8")
    d.rectangle((0,0,W,165),fill=navy)
    rr(d,(25,22,515,57),12,"#234657")
    d.text((42,31),"EXPLAINER LAB  /  "+ACTIVE_BRAND,font=font(12,True),fill=lime)
    centered(d,scene["title"],82,font(25,True),"#FFFFFF",470)
    v=scene["visual"]
    def pill(box,label,fill=teal,fg="#FFFFFF",fs=15):
        rr(d,box,16,fill); x1,y1,x2,y2=box
        centered(d,label,y1+(y2-y1-fs)//2,font(fs,True),fg,x2-x1-14)
    def particles(x1,y1,x2,y2,count=9,phase=0):
        for k in range(count):
            q=(p*1.7+k/count+phase)%1; x=int(x1+(x2-x1)*q); y=int(y1+(y2-y1)*q); r=3+k%3
            d.ellipse((x-r,y-r,x+r,y+r),fill=teal,outline="#FFFFFF")
    def arrow(x1,y1,x2,y2,color=teal,width=7):
        d.line((x1,y1,x2,y2),fill=color,width=width)
        ang=math.atan2(y2-y1,x2-x1)
        d.polygon([(x2,y2),(x2+18*math.cos(ang+2.5),y2+18*math.sin(ang+2.5)),(x2+18*math.cos(ang-2.5),y2+18*math.sin(ang-2.5))],fill=color)
    def motor(cx,cy,r=110):
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=navy,outline=blue,width=10)
        d.ellipse((cx-r+22,cy-r+22,cx+r-22,cy+r-22),outline="#D4E7E7",width=8)
        angle=p*math.pi*10
        for k in range(8):
            a=angle+k*math.pi/4
            d.line((cx+math.cos(a)*25,cy+math.sin(a)*25,cx+math.cos(a)*(r-30),cy+math.sin(a)*(r-30)),fill=lime if k%2==0 else blue,width=12)
        d.ellipse((cx-25,cy-25,cx+25,cy+25),fill=lime,outline="#FFFFFF",width=4)
        st=int(p*300); d.arc((cx-r-22,cy-r-22,cx+r+22,cy+r+22),st,st+120,fill=teal,width=9)
    # Each visual family gets its own composition and continuous action.
    if v in ("car","threecars","hybrid"):
        d.rectangle((0,640,W,735),fill="#C5D3D0")
        for k in range(8):
            x=(k*105-int(p*340))%680-70; d.rounded_rectangle((x,680,x+55,689),radius=4,fill="#FFFFFF")
        shift=int(-100+200*ease(p)); bounce=int(5*math.sin(p*math.pi*8))
        draw_car(d,270+shift,520+bounce,1.22,lime,p*11)
        for k in range(6):
            x=25+k*23+int(p*100)%30; d.line((x,475,x+18,475),fill=teal,width=4)
        pill((65,770,475,825),"TORSI  •  AKSELERASI  •  GERAK",navy,lime,16)
        if v=="threecars":
            for j,label in enumerate(("BEV","HEV","PHEV")): pill((28+j*165,850,178+j*165,905),label,teal,"#FFFFFF",17)
        elif v=="hybrid": particles(70,700,470,700,12)
    elif v in ("battery","charging","temperature","chemistry"):
        bx,by=85,340; rr(d,(bx,by,bx+370,by+235),30,navy,outline="#FFFFFF",width=6)
        rr(d,(bx+370,by+75,bx+397,by+160),10,navy)
        for k in range(7):
            cx=bx+18+k*48; lit=ease(p*1.35-k*.13)>0.12
            rr(d,(cx,by+20,cx+39,by+215),10,lime if lit else "#365A63")
            if lit: d.ellipse((cx+12,by+70,cx+27,by+85),fill="#FFFFFF")
        if v=="charging":
            arrow(30,455,bx-5,455,blue,10); pill((95,640,445,700),"DAYA MASUK KE BATERAI",teal)
        elif v=="temperature":
            for k in range(5):
                yy=660-k*25-int(16*math.sin(p*math.pi*4+k)); d.arc((185+k*7,yy,355-k*7,yy+55),190,350,fill="#F08C65",width=7)
            pill((95,740,445,800),"PANTAU SUHU SEL",navy,lime)
        else: pill((85,640,455,700),"ENERGI TERSIMPAN DI DALAM SEL",navy,lime,15)
    elif v in ("motor","energy","ac","dc","system","parts"):
        y=330
        for box,label,sub in [((22,y,164,y+115),"BATERAI","ARUS DC"),((177,y,363,y+115),"INVERTER","KONTROL"),((376,y,518,y+115),"MOTOR","PUTARAN")]:
            pill(box,label,navy,lime,15); x1,y1,x2,y2=box; centered(d,sub,y1+68,font(12,True),"#D6E6E5",x2-x1-12)
        particles(164,y+55,177,y+55,5); particles(363,y+55,376,y+55,5,.4); arrow(165,y+140,375,y+140)
        if v in ("motor","energy"):
            motor(270,650); pill((72,825,468,875),"ROTOR BERPUTAR  •  TORSI",navy,lime,16)
        elif v=="ac":
            for k in range(3):
                pts=[(xx,620+k*48+int(math.sin(xx/475*math.pi*5-p*math.pi*9)*22)) for xx in range(35,510,4)]
                d.line(pts,fill=teal if k==0 else blue,width=5)
            pill((100,820,440,875),"ARUS BOLAK-BALIK",navy,lime,16)
        elif v=="dc":
            for k in range(9):
                xx=42+k*54; h=45+int(70*ease(p*1.5-k*.09)); d.rounded_rectangle((xx,790-h,xx+27,790),radius=6,fill=teal)
            pill((85,825,455,875),"ARUS SEARAH",navy,lime,16)
        else: pill((80,620,460,690),"KONTROL DAYA MENYESUAIKAN TENAGA",navy,lime,14)
    elif v=="question":
        draw_person(d,270,440,p); pulse=int(8*math.sin(p*math.pi*5))
        rr(d,(40,675+pulse,500,770+pulse),26,navy,outline=teal,width=4)
        centered(d,"KOK BISA?  •  YUK, KITA BEDAH!",705+pulse,font(19,True),lime,430)
    elif v=="chart":
        for j,label in enumerate(("ENERGI","EFISIENSI","KONDISI")):
            x=65+j*145; base=740; h=int(55+145*ease(p*1.6-j*.18))
            rr(d,(x,base-h,x+80,base),12,teal if j==1 else navy); centered(d,label,base+17,font(12,True),ink,100)
        centered(d,"FAKTOR YANG MEMPENGARUHI",800,font(16,True),ink,450)
    elif v=="checklist":
        for j,label in enumerate(("KENALI TEKNOLOGINYA","CEK SPESIFIKASI","PAHAMI KEBUTUHAN")):
            y=355+j*135; slide=int(70*(1-ease(p*4-j*.12))
            rr(d,(50+slide,y,490+slide,y+82),20,navy,outline=teal,width=3)
            d.ellipse((72+slide,y+23,116+slide,y+59),fill=lime)
            d.line((82+slide,y+41,92+slide,y+50,108+slide,y+31),fill=navy,width=5)
            d.text((137+slide,y+29),label,font=font(15,True),fill="#FFFFFF")
    else: draw_person(d,270,440,p)
    cap=caption_lines(scene.get("narration",""),font(18,True),460)[:3]
    panel_y=865-(len(cap)-1)*29; rr(d,(22,panel_y-15,518,945),18,"#FFFFFF",outline="#C7DAD6",width=2)
    for line in cap:
        centered(d,line,panel_y,font(18,True),ink,460); panel_y+=27
    d.rounded_rectangle((25,950,515,958),radius=4,fill="#C8D8D4")
    d.rounded_rectangle((25,950,25+int(490*p),958),radius=4,fill=teal)
    zoom=1+0.025*math.sin(p*math.pi); nw,nh=int(W*zoom),int(H*zoom)
    img=img.resize((nw,nh),Image.Resampling.LANCZOS); ox=(nw-W)//2+int(5*math.sin(p*math.pi*2)); oy=(nh-H)//2
    return img.crop((max(0,ox),max(0,oy),max(0,ox)+W,max(0,oy)+H)

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

def neural_voice(scene_texts):
    clips=[]; durations=[]; voice=os.environ.get("EDGE_TTS_VOICE","id-ID-ArdiNeural")
    for index,text in enumerate(scene_texts,1):
        mp3=WORK/f"voice-{index:02d}.mp3"; wav=WORK/f"voice-{index:02d}.wav"
        proc=subprocess.run([sys.executable,"-m","edge_tts","--voice",voice,"--rate","+5%","--pitch","+1Hz","--text",text,"--write-media",str(mp3)],capture_output=True,text=True,timeout=180)
        if proc.returncode or not mp3.exists() or mp3.stat().st_size<1000:
            raise RuntimeError("Neural TTS gagal: "+proc.stderr[-500:])
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(mp3),"-ar","48000","-ac","1","-c:a","pcm_s16le",str(wav)])
        probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(wav)]))
        durations.append(float(probe["format"]["duration"])); clips.append(wav)
    output=WORK/"narration.wav"
    with wave.open(str(clips[0]),"rb") as first: params=first.getparams()
    silence=b"\x00"*(int(params.framerate*.24)*params.nchannels*params.sampwidth)
    with wave.open(str(output),"wb") as combined:
        combined.setparams(params)
        for i,clip in enumerate(clips):
            with wave.open(str(clip),"rb") as part: combined.writeframes(part.readframes(part.getnframes()))
            if i<len(clips)-1: combined.writeframes(silence)
    return output,durations

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
    manifest={"jobId":"smoke-test","userId":"smoke-test","expires":"0","signature":"0","brand":"JAECOO","topic":"regenerative braking","duration":30} if os.environ.get("SMOKE_TEST")=="1" else fetch_manifest()
    ACTIVE_BRAND=manifest["brand"]; topic=manifest["topic"]; brand=manifest["brand"]; duration=int(manifest["duration"])
    scenes=choose_script(topic,duration)
    print("Narration:", " ".join(x["narration"] for x in scenes),flush=True)
    audio,spoken=neural_voice([x["narration"] for x in scenes])
    clip_durations=[d+.48 for d in spoken]
    total_video=sum(clip_durations)-.28*(len(clip_durations)-1)
    print(f"Neural voice {sum(spoken):.2f}s; edited video {total_video:.2f}s",flush=True)
    make_subtitles(scenes,spoken)
    clips=[]
    for n,(scene,seconds) in enumerate(zip(scenes,clip_durations),1):
        frames=max(24,round(seconds*FPS)); folder=WORK/f"scene-{n:02d}"; folder.mkdir(exist_ok=True)
        for frame in range(frames): draw_frame(scene,frame,frames).save(folder/f"frame-{frame:04d}.png",optimize=False)
        clip=WORK/f"scene-{n:02d}.mp4"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate",str(FPS),"-i",str(folder/"frame-%04d.png"),"-vf","scale=1080:1920:flags=lanczos,fps=30,format=yuv420p","-an","-c:v","libx264","-preset","ultrafast","-crf","23","-movflags","+faststart",str(clip)])
        clips.append(clip)
    inputs=[]
    for clip in clips: inputs += ["-i",str(clip)]
    filters=[]; current="[0:v]"; accumulated=clip_durations[0]
    transitions=["smoothleft","fade","smoothright","wipeup","fadeblack","smoothleft","fade"]
    for i in range(1,len(clips)):
        out=f"[v{i}]"; filters.append(f"{current}[{i}:v]xfade=transition={transitions[(i-1)%len(transitions)]}:duration=.28:offset={accumulated-.28:.3f}{out}")
        current=out; accumulated+=clip_durations[i]-.28
    edited=WORK/"edited-video.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y",*inputs,"-filter_complex",";".join(filters),"-map",current,"-an","-r","30","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",str(edited)])
    sfx,music=make_sound_design([d+.24 for d in spoken],total_video)
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(edited),"-i",str(audio),"-i",str(music),"-i",str(sfx),"-filter_complex",
         "[1:a]volume=1.12,acompressor=threshold=-18dB:ratio=2.2:attack=15:release=180[voice];[2:a]volume=.24,lowpass=f=9000[bed];[3:a]volume=1.35,highpass=f=100[fx];[voice][bed][fx]amix=inputs=3:duration=longest:dropout_transition=1,loudnorm=I=-15:TP=-1.0:LRA=10,alimiter=limit=.95[a]",
         "-map","0:v:0","-map","[a]","-t",f"{total_video:.2f}","-r","30","-c:v","copy","-c:a","aac","-b:a","192k","-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)])
    final=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_name,width,height","-of","json",str(OUT)]))
    video=next((x for x in final["streams"] if x.get("codec_name")=="h264"),None)
    if not video or video.get("width")!=1080 or video.get("height")!=1920: raise RuntimeError("Output bukan H.264 1080x1920.")
    if OUT.stat().st_size<100000: raise RuntimeError("File MP4 terlalu kecil.")
    blueprint={"brand":brand,"topic":topic,"duration":float(final["format"]["duration"]),"style":"2D animated explainer with edited transitions, kinetic captions and synchronized sound design","voice":"Microsoft neural Indonesian "+os.environ.get("EDGE_TTS_VOICE","id-ID-ArdiNeural"),"scene_audio_durations":spoken,"scenes":scenes}
    (WORK/"blueprint.json").write_text(json.dumps(blueprint,ensure_ascii=False,indent=2),encoding="utf-8")
    if os.environ.get("SMOKE_TEST")=="1":
        print(f"SMOKE PASS: {final['format']['duration']}s, {OUT.stat().st_size} bytes, neural narration + transitions + SFX.",flush=True); return
    params=urllib.parse.urlencode({"job_id":manifest["jobId"],"user_id":manifest["userId"],"expires":manifest["expires"],"signature":manifest["signature"],"run_id":os.environ["GITHUB_RUN_ID"]})
    req=urllib.request.Request(os.environ["OUTPUT_UPLOAD_BASE_URL"]+"?"+params,data=OUT.read_bytes(),headers={"Content-Type":"video/mp4","Content-Length":str(OUT.stat().st_size),"Authorization":"Bearer "+os.environ["OIDC_TOKEN"],"User-Agent":"Mozilla/5.0"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=300) as response:
            result=json.loads(response.read().decode())
            if not result.get("success"): raise RuntimeError("R2 tidak mengonfirmasi unggahan video.")
    except urllib.error.HTTPError as error: raise RuntimeError(f"Upload video gagal HTTP {error.code}: "+error.read().decode("utf-8",errors="replace")[:1200]) from None
    print(f"SUCCESS: {brand} '{topic}' — {final['format']['duration']} sec, {OUT.stat().st_size} bytes.",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("EDUCATION ANIMATION FAILED:",str(exc),file=sys.stderr)
        sys.exit(1)
